#!/usr/bin/env python3
"""
Stage 2: review — 按 3 套风格模板打分
"""

import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import drafts_dir, read_draft, load_state, save_state, touch, now_iso


def load_style_template(name: str) -> str:
    """读 skill 自带的 templates/style-templates/*.md。"""
    p = Path(__file__).resolve().parent.parent / "templates" / "style-templates" / f"{name}.md"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py review <draft_id>")
        sys.exit(1)
    draft_id = sys.argv[1]

    try:
        source_path, fm, body = read_draft(draft_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    draft_dir = source_path.parent
    review_path = draft_dir / "review.json"

    print(f"\n=== review stage: {draft_id} ===")
    print(f"title: {fm.get('title', '?')}")
    print(f"字数: {fm.get('word_count', len(body))}")
    print()
    print(">>> 给 agent 的步骤：")
    print("   1. 读 prompts/review.md 完整指令")
    print("   2. 加载 3 个风格模板（公众号/网红/极客）")
    print(f"   3. 读 source: {source_path}")
    print(f"   4. LLM 按 6 维度 × 3 模板打分，输出 review.json 到 {review_path}")
    print(f"   5. 选 primary_style（总分最高的模板）")
    print(f"   6. 写回 review.json（格式见 prompts/review.md）")
    print(f"   7. update_draft_status('{draft_id}', 'reviewed', reviewed_at=...)")

    # 即使没真跑 LLM，也写个空 review.json 占位，让下一 stage 能继续
    if not review_path.exists():
        placeholder = {
            "draft_id": draft_id,
            "reviewed_at": now_iso(),
            "scores": {
                "gongzhonghao": {k: 7 for k in ["title", "opening", "structure", "rhythm", "cta", "platform_fit"]},
                "wanghong": {k: 7 for k in ["title", "opening", "structure", "rhythm", "cta", "platform_fit"]},
                "jike": {k: 7 for k in ["title", "opening", "structure", "rhythm", "cta", "platform_fit"]},
            },
            "weighted_total": 7.0,
            "primary_style": "gongzhonghao",
            "suggestions": [],
            "status": "reviewed",
            "note": "占位 review，等 LLM 真跑后覆盖",
        }
        review_path.write_text(json.dumps(placeholder, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n⚠️  写了占位 review.json，agent 真跑 LLM 后会覆盖")

    state = load_state()
    touch("review", state)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
