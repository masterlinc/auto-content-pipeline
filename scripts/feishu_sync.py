#!/usr/bin/env python3
"""
Stage 6: sync-feishu — 把打磨好的文章同步到飞书云文档供审阅

入参: draft_id
前置: store stage 已完成（vault 价值文章区里有 {draft_id}/article.md）

行为:
  1. 读 vault 价值文章区里的 article.md + cover.png
  2. 在飞书云空间 auto-content-pipeline/审核中/ 下创建/更新云文档
  3. 通过飞书 IM 发卡片消息给审阅人（chat_id 从 config/default.yaml 读）
  4. 写回 frontmatter: feishu_doc_token / feishu_doc_url / feishu_synced_at
  5. 更新 status 为 feishu_synced

调用方式:
  python3 feishu_sync.py <draft_id>
  python3 pipeline.py sync-feishu <draft_id>

实现:
  - 走 lark-cli（已认证即可），不依赖任何特定 agent
  - 任何 agent 也可以直接读 prompts/sync-feishu.md 自己实现
"""

import sys
import json
import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import (
    drafts_dir, read_draft, load_state, save_state, touch, now_iso, today_str,
    update_draft_status, set_feishu_doc, get_feishu_doc_token,
    DEFAULT_VAULT, FEISHU_AUDIT_FOLDER,
)

VALUE_DIR = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "价值文章"
CONFIG_PATH = HERE.parent / "config" / "default.yaml"


# ====== 读 config ======

def load_feishu_config() -> dict:
    """从 config/default.yaml 读 feishu 段。"""
    cfg = {
        "reviewer_chat_id": "",          # 飞书 chat_id（个人/群）
        "reviewer_user_open_id": "",     # 备选：open_id（脚本会自己解析成 chat_id）
        "audit_folder": FEISHU_AUDIT_FOLDER,
        "title_prefix": "📝 审阅:",
        "dry_run": False,
    }
    if not CONFIG_PATH.exists():
        return cfg
    text = CONFIG_PATH.read_text(encoding="utf-8")
    in_feishu = False
    for raw in text.splitlines():
        # 去掉行内注释（# 后面到行尾）
        if "#" in raw:
            raw = raw[: raw.index("#")]
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "feishu:":
            in_feishu = True
            continue
        if in_feishu and not line.startswith(" ") and not line.startswith("\t"):
            in_feishu = False
        if in_feishu:
            m = re.match(r"^\s+([\w_-]+):\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            if key in cfg:
                # 布尔值转换
                if val.lower() in ("true", "yes", "1"):
                    cfg[key] = True
                elif val.lower() in ("false", "no", "0"):
                    cfg[key] = False
                else:
                    cfg[key] = val
    return cfg


# ====== lark-cli 薄包装 ======

def lark_cli(*args) -> dict:
    """调 lark-cli，解析 JSON 输出。失败抛 RuntimeError。"""
    cmd = ["lark-cli", *args]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"lark-cli 失败: {' '.join(args)}\nstderr: {p.stderr[:500]}")
    out = p.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # 一些命令返回非 JSON（比如 markdown 格式），原样包一层
        return {"_raw": out}


def find_or_create_audit_folder(audit_path: str) -> Optional[str]:
    """在云空间根找/建 auto-content-pipeline/审核中/，返回 folder_token。"""
    parts = audit_path.strip("/").split("/")
    parent_token: Optional[str] = None
    for i, name in enumerate(parts):
        # 列父目录
        list_args = ["drive", "+search", "--query", name, "--type", "folder"]
        if parent_token:
            list_args += ["--parent-token", parent_token]
        try:
            search_result = lark_cli(*list_args)
        except RuntimeError:
            search_result = {}
        folders = search_result.get("files") or search_result.get("items") or []
        match = next((f for f in folders if f.get("name") == name), None)
        if match:
            parent_token = match.get("token")
            continue
        # 没找到就建
        create_args = ["drive", "+create-folder", "--name", name]
        if parent_token:
            create_args += ["--parent-token", parent_token]
        try:
            res = lark_cli(*create_args)
            parent_token = res.get("token") or res.get("folder_token")
        except RuntimeError as e:
            print(f"⚠️  建文件夹失败 {name}: {e}")
            return None
    return parent_token


def get_chat_id_from_user(open_id: str) -> Optional[str]:
    """把 user open_id 解析成 p2p chat_id。"""
    try:
        res = lark_cli("im", "+chat-list", "--types", "p2p")
        chats = res.get("chats") or res.get("items") or []
        # 直接走 +chat-search 更准
        res2 = lark_cli("im", "+chat-search", "--query", open_id, "--types", "p2p")
        chats2 = res2.get("chats") or res2.get("items") or []
        for c in chats + chats2:
            members = c.get("members") or []
            for m in members:
                if m.get("id") == open_id or m.get("open_id") == open_id:
                    return c.get("chat_id")
            if open_id in (c.get("description") or "") or open_id in c.get("name", ""):
                return c.get("chat_id")
    except RuntimeError:
        pass
    return None


# ====== 核心流程 ======

def build_doc_markdown(title: str, draft_id: str, body: str, review_round: int, feishu_doc_url: str = "") -> str:
    """组装飞书云文档的 markdown 内容。"""
    header = (
        f"# {title}\n\n"
        f"> **审阅稿** · draft_id: `{draft_id}` · 审核轮数: {review_round}\n\n"
        f"---\n\n"
    )
    return header + body.strip() + "\n"


def create_feishu_doc(title: str, markdown: str, folder_token: Optional[str]) -> dict:
    """调 lark-cli docs +create。"""
    args = [
        "docs", "+create",
        "--title", title,
        "--content", markdown,
        "--content-format", "markdown",
    ]
    if folder_token:
        args += ["--folder-token", folder_token]
    return lark_cli(*args)


def update_feishu_doc(doc_token: str, markdown: str) -> dict:
    """调 lark-cli docs +update。"""
    args = [
        "docs", "+update",
        "--doc-token", doc_token,
        "--content", markdown,
        "--content-format", "markdown",
        "--mode", "overwrite",
    ]
    return lark_cli(*args)


def upload_cover_to_doc(doc_token: str, cover_path: Path) -> Optional[str]:
    """把封面图传到飞书文档。返回 media_id 或 None。"""
    if not cover_path.exists():
        return None
    try:
        res = lark_cli("docs", "+media-upload", "--doc-token", doc_token, "--file", str(cover_path))
        return res.get("media_id") or res.get("file_token")
    except RuntimeError as e:
        print(f"⚠️  封面上传失败: {e}")
        return None


def send_review_card(chat_id: str, doc_url: str, title: str, draft_id: str, review_round: int) -> dict:
    """发 IM 卡片消息给审阅人。"""
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📝 待审阅：{title}"},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**draft_id**: `{draft_id}`\n"
                        f"**审核轮数**: {review_round}\n"
                        f"**状态**: 待审阅\n\n"
                        f"👉 [点此进入云文档审阅]({doc_url})\n\n"
                        f"---\n"
                        f"💬 **在云文档里写评论**即可反馈修改意见。\n"
                        f"✅ 评论中含 `确认发布` / `通过` 即视为审核通过。\n"
                        f"🔄 否则按「修改意见」自动重推。"
                    ),
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🚀 确认发布"},
                        "type": "primary",
                        "url": doc_url,
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📝 打开云文档"},
                        "type": "default",
                        "url": doc_url,
                    },
                ],
            },
            {
                "tag": "note",
                "elements": [
                    {"tag": "plain_text", "content": f"auto-content-pipeline · 审核轮 {review_round}"},
                ],
            },
        ],
    }
    return lark_cli(
        "im", "+messages-send",
        "--chat-id", chat_id,
        "--msg-type", "interactive",
        "--content", json.dumps(card, ensure_ascii=False),
    )


# ====== 主流程 ======

def run(draft_id: str) -> int:
    cfg = load_feishu_config()
    if cfg.get("dry_run"):
        print("⚠️  feishu.dry_run=true，只打印不实际推送")
    if not cfg.get("reviewer_chat_id") and not cfg.get("reviewer_user_open_id"):
        print("❌ config/default.yaml 里 feishu.reviewer_chat_id / reviewer_user_open_id 都未配置")
        print("   至少填一个，或 export ACP_REVIEWER_CHAT_ID=oc_xxx")
        return 1

    # 1. 找已 store 的产物
    stored_dir = VALUE_DIR / draft_id
    article = stored_dir / "article.md"
    if not article.exists():
        print(f"❌ vault 价值文章区里没找到 article.md: {article}")
        print("   先跑 store stage")
        return 1
    cover = stored_dir / "cover.png"
    fm, _ = read_draft(draft_id)
    title = fm.get("title", draft_id)

    # 2. 读 article.md 正文
    text = article.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---\n", 4)
        if end > 0:
            text = text[end + 5:]
    body = text.strip()

    # 3. 解析 chat_id
    chat_id = cfg.get("reviewer_chat_id")
    if not chat_id and cfg.get("reviewer_user_open_id"):
        chat_id = get_chat_id_from_user(cfg["reviewer_user_open_id"])
        if not chat_id:
            print(f"❌ 无法从 open_id {cfg['reviewer_user_open_id']} 解析 chat_id")
            return 1

    # 4. 找/建审核中文件夹
    if not cfg.get("dry_run"):
        folder_token = find_or_create_audit_folder(cfg["audit_folder"])
        if not folder_token:
            print("⚠️  找不到/建不了审核中文件夹，继续走云空间根目录")

    # 5. 创建/更新云文档
    doc_token = get_feishu_doc_token(draft_id) if not cfg.get("dry_run") else None
    review_round = int(fm.get("review_round", 0))
    full_md = build_doc_markdown(title, draft_id, body, review_round)

    if cfg.get("dry_run"):
        print(f"[dry-run] {cfg.get('audit_folder')}/{title}")
        print(f"[dry-run] chat_id={chat_id}")
        print(f"[dry-run] body 前 200 字: {body[:200]}")
        return 0

    if doc_token:
        print(f"▶ 复用已有飞书文档: {doc_token}")
        update_feishu_doc(doc_token, full_md)
        doc_url = fm.get("feishu_doc_url") or f"https://feishu.cn/docx/{doc_token}"
    else:
        print(f"▶ 创建飞书云文档...")
        res = create_feishu_doc(f"{cfg.get('title_prefix', '📝 审阅:')}{title}", full_md, folder_token)
        doc_token = res.get("doc_token") or res.get("document_id") or res.get("token")
        doc_url = res.get("url") or res.get("doc_url") or (f"https://feishu.cn/docx/{doc_token}" if doc_token else "")
        if not doc_token:
            print(f"❌ 创建飞书文档失败，lark-cli 返回: {json.dumps(res, ensure_ascii=False)[:500]}")
            return 1
        print(f"✅ 飞书文档创建: {doc_url}")

    # 6. 上传封面（可选）
    if cover.exists():
        media_id = upload_cover_to_doc(doc_token, cover)
        if media_id:
            print(f"   封面上传: media_id={media_id}")

    # 7. 发 IM 卡片
    print(f"▶ 发审阅 IM 卡片到 {chat_id}...")
    send_review_card(chat_id, doc_url, title, draft_id, review_round)
    print(f"✅ IM 卡片已发送")

    # 8. 写回 frontmatter + 状态
    set_feishu_doc(draft_id, doc_token, doc_url)
    update_draft_status(draft_id, "feishu_synced")

    state = load_state()
    touch("feishu_sync", state)
    save_state(state)

    print(f"\n✅ sync-feishu done → {draft_id}")
    print(f"   doc: {doc_url}")
    print(f"   状态: feishu_synced")
    print(f"   下一步：审阅人在云文档评论 → 跑 feishu-review 拉反馈")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py sync-feishu <draft_id>")
        print("      pipeline.py feishu-sync <draft_id>")
        sys.exit(1)
    return run(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
