#!/usr/bin/env python3
"""
Stage 6: publish — 多平台分发

支持的平台：
  - xiaohongshu: ✅ xiaohongshu_poster.py
  - juejin:       🚧 待配置 cookie
  - sspai:        🚧 待配置
  - zhihu:        🚧 待配置
  - gongzhonghao: ⏸ 待 API（**不走浏览器**），等 linc 给 AppID/AppSecret
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import (
    drafts_dir, read_draft, load_state, save_state, touch, now_iso, record_error,
    DEFAULT_VAULT,
)

HOME = Path.home()
POSTER = HOME / ".openclaw" / "workspace" / "xiaohongshu_poster.py"
ARTICLE_TXT = HOME / ".openclaw" / "workspace" / "article_to_post.txt"

VALUE_DIR = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "价值文章"


PLATFORM_STATUS = {
    "xiaohongshu": "✅",
    "juejin": "🚧",
    "sspai": "🚧",
    "zhihu": "🚧",
    "gongzhonghao": "⏸",
}


def publish_xiaohongshu(stored_dir: Path, meta: dict) -> dict:
    """包装 xiaohongshu_poster.py 发布。"""
    article = stored_dir / "article.md"
    if not article.exists():
        return {"ok": False, "error": "article.md 不存在"}

    text = article.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---\n", 4)
        if end > 0:
            text = text[end + 5:]

    title = meta.get("title", "未命名")
    body = text
    tags = meta.get("tags", [])

    parts = [f"# {title}", "---", body.strip()]
    if tags:
        parts.append("")
        parts.append(" ".join(f"#{t}" for t in tags))
    ARTICLE_TXT.write_text("\n".join(parts), encoding="utf-8")

    cover = stored_dir / "cover.png"
    if cover.exists():
        shutil.copy(cover, HOME / ".openclaw" / "workspace" / "article_cover.png")

    result = subprocess.run(["python3", str(POSTER), "post"], cwd=POSTER.parent, capture_output=True, text=True)
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def publish_juejin(stored_dir: Path, meta: dict) -> dict:
    """占位：等配置 cookie。"""
    return {"ok": False, "error": "掘金待配置 cookie（juejin API 需要 JUEJIN_SESSION）"}


def publish_sspai(stored_dir: Path, meta: dict) -> dict:
    return {"ok": False, "error": "少数派待配置登录态"}


def publish_zhihu(stored_dir: Path, meta: dict) -> dict:
    return {"ok": False, "error": "知乎待配置 z_c0 token"}


def publish_gongzhonghao(stored_dir: Path, meta: dict) -> dict:
    return {"ok": False, "error": "公众号待 API 凭证（等 AppID/AppSecret，**不走浏览器**）"}


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py publish <draft_id> [--platforms xiaohongshu,juejin]")
        sys.exit(1)
    draft_id = sys.argv[1]

    platforms = ["xiaohongshu"]
    for arg in sys.argv[2:]:
        if arg.startswith("--platforms="):
            platforms = arg.split("=", 1)[1].split(",")

    stored_dir = VALUE_DIR / draft_id
    if not stored_dir.exists():
        print(f"❌ vault 价值文章区不存在: {stored_dir}")
        print(f"   先跑 store stage")
        return 1

    meta_path = stored_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    print(f"\n=== publish stage: {draft_id} ===")
    print(f"title: {meta.get('title', '?')}")
    print(f"platforms: {platforms}")
    print()

    publish_handlers = {
        "xiaohongshu": publish_xiaohongshu,
        "juejin": publish_juejin,
        "sspai": publish_sspai,
        "zhihu": publish_zhihu,
        "gongzhonghao": publish_gongzhonghao,
    }

    results = {}
    for p in platforms:
        status = PLATFORM_STATUS.get(p, "?")
        print(f"  [{status}] {p} ...", end=" ", flush=True)
        handler = publish_handlers.get(p)
        if not handler:
            print(f"❌ 未知平台")
            results[p] = {"ok": False, "error": "未知平台"}
            continue
        r = handler(stored_dir, meta)
        results[p] = r
        if r.get("ok"):
            print(f"✅")
        else:
            print(f"❌ {r.get('error', r.get('stderr', '失败'))}")

    # 更新 meta.json
    published = meta.get("published_platforms", [])
    for p, r in results.items():
        if r.get("ok"):
            published.append({"platform": p, "url": r.get("url", ""), "published_at": now_iso()})
    meta["published_platforms"] = published
    meta["publish_status"] = "published" if all(r.get("ok") for r in results.values()) else "partially_published" if any(r.get("ok") for r in results.values()) else "failed"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n📊 结果汇总：")
    for p, r in results.items():
        icon = "✅" if r.get("ok") else "❌"
        print(f"  {icon} {p}: {r.get('error') or r.get('url') or 'OK'}")

    state = load_state()
    touch("publish", state)
    if any(r.get("ok") for r in results.values()):
        state["counters"]["published_total"] = state["counters"].get("published_total", 0) + 1
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
