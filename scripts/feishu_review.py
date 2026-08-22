#!/usr/bin/env python3
"""
Stage 7: feishu-review — 拉取飞书云文档评论，分类 + 回写 status

入参: draft_id
前置: sync-feishu 已完成（frontmatter 有 feishu_doc_token）

行为:
  1. 读 frontmatter 里的 feishu_doc_token + last_seen_comment_id
  2. 调 lark-cli drive +list-comments 拉最新评论
  3. 按 last_seen_comment_id 过滤"新评论"
  4. 用 classify_feishu_comment() 分类: pass / reject / suggestion
  5. 输出:
     - 如果任意新评论是 pass → status = feishu_review_passed
     - 否则 → status = feishu_review_modifying，把所有新评论（除 pass）作为修改建议
  6. 更新 frontmatter:
     - last_seen_comment_id
     - last_reviewed_at
     - review_round + 1

输出格式（stdout JSON，方便 agent 读）:
  {
    "draft_id": "...",
    "doc_token": "...",
    "review_round": 2,
    "verdict": "reject" | "pass" | "empty" | "no_doc",
    "new_comments": [{"id": "...", "author": "...", "text": "...", "classification": "..."}],
    "suggestions": ["具体修改意见 1", "..."],
    "next_action": "modify_then_resync" | "ready_to_publish" | "wait_for_comments"
  }

调用方式:
  python3 feishu_review.py <draft_id>
  python3 pipeline.py feishu-review <draft_id>
"""

import sys
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import (
    drafts_dir, read_draft, load_state, save_state, touch, now_iso,
    update_draft_status, set_feishu_doc, bump_review_round, classify_feishu_comment,
)


def lark_cli(*args) -> dict:
    """调 lark-cli，解析 JSON 输出。"""
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
        return {"_raw": out}


def fetch_comments(doc_token: str) -> list:
    """拉飞书云文档的全部评论。"""
    res = lark_cli("drive", "+list-comments", "--doc-token", doc_token, "--page-all")
    items = res.get("items") or res.get("comments") or res.get("data", {}).get("items") or []
    out = []
    for c in items:
        # 兼容不同 schema
        cid = c.get("id") or c.get("comment_id")
        text = (
            c.get("text")
            or c.get("content")
            or (c.get("message") or {}).get("text")
            or ""
        )
        author = ""
        if isinstance(c.get("user"), dict):
            author = c["user"].get("name") or c["user"].get("en_name") or c["user"].get("id", "")
        else:
            author = c.get("author") or c.get("user_id", "")
        out.append({
            "id": cid,
            "author": author,
            "text": text if isinstance(text, str) else json.dumps(text, ensure_ascii=False),
            "created_at": c.get("created_time") or c.get("create_time") or "",
        })
    return out


def update_draft_review(draft_id: str, last_seen_comment_id: str) -> None:
    """写回 last_seen_comment_id + 时间戳。"""
    root = drafts_dir() / draft_id
    source = root / "source.md"
    text = source.read_text(encoding="utf-8")
    from state import parse_frontmatter, dump_frontmatter
    fm, body = parse_frontmatter(text)
    fm["last_seen_comment_id"] = last_seen_comment_id
    fm["last_reviewed_at"] = now_iso()
    source.write_text(dump_frontmatter(fm) + "\n\n" + body.lstrip(), encoding="utf-8")


def run(draft_id: str) -> int:
    try:
        _, fm, _ = read_draft(draft_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    doc_token = fm.get("feishu_doc_token")
    if not doc_token:
        print(f"❌ draft frontmatter 里没有 feishu_doc_token")
        print(f"   先跑 sync-feishu stage")
        result = {
            "draft_id": draft_id,
            "verdict": "no_doc",
            "next_action": "run_sync_feishu_first",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    last_seen_id = fm.get("last_seen_comment_id", "")
    review_round = int(fm.get("review_round", 0))

    # 1. 拉评论
    try:
        all_comments = fetch_comments(doc_token)
    except RuntimeError as e:
        print(f"❌ 拉评论失败: {e}")
        return 1

    if not all_comments:
        result = {
            "draft_id": draft_id,
            "doc_token": doc_token,
            "review_round": review_round,
            "verdict": "empty",
            "new_comments": [],
            "suggestions": [],
            "next_action": "wait_for_comments",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # 2. 按 last_seen_id 过滤"新评论"
    seen = False
    new_comments = []
    for c in all_comments:
        if seen:
            new_comments.append(c)
            continue
        if c["id"] == last_seen_id:
            seen = True
    if not last_seen_id:
        # 第一次跑：所有评论都算新
        new_comments = all_comments

    if not new_comments:
        result = {
            "draft_id": draft_id,
            "doc_token": doc_token,
            "review_round": review_round,
            "verdict": "empty",
            "new_comments": [],
            "suggestions": [],
            "next_action": "wait_for_comments",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # 3. 分类
    for c in new_comments:
        c["classification"] = classify_feishu_comment(c["text"])

    has_pass = any(c["classification"] == "pass" for c in new_comments)
    suggestions = [c["text"] for c in new_comments if c["classification"] in ("reject", "suggestion")]

    # 4. 更新 last_seen + 状态
    latest_id = new_comments[-1]["id"]
    update_draft_review(draft_id, latest_id)

    if has_pass:
        new_round = bump_review_round(draft_id)
        update_draft_status(draft_id, "feishu_review_passed", last_review_verdict="pass")
        verdict = "pass"
        next_action = "ready_to_publish"
    else:
        new_round = bump_review_round(draft_id)
        update_draft_status(draft_id, "feishu_review_modifying", last_review_verdict="reject")
        verdict = "reject"
        next_action = "modify_then_resync"

    state = load_state()
    touch("feishu_review", state)
    save_state(state)

    result = {
        "draft_id": draft_id,
        "doc_token": doc_token,
        "review_round": new_round,
        "verdict": verdict,
        "new_comments": new_comments,
        "suggestions": suggestions,
        "next_action": next_action,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py feishu-review <draft_id>")
        sys.exit(1)
    return run(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
