#!/usr/bin/env python3
"""
Stage 3: modify — 按 review.json 自动改稿
"""

import sys
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import drafts_dir, read_draft, load_state, save_state, touch, now_iso, dump_frontmatter


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py modify <draft_id>")
        sys.exit(1)
    draft_id = sys.argv[1]

    try:
        source_path, fm, body = read_draft(draft_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    draft_dir = source_path.parent
    review_path = draft_dir / "review.json"
    article_path = draft_dir / "article.md"

    print(f"\n=== modify stage: {draft_id} ===")
    print(f"title: {fm.get('title', '?')}")
    print()
    print(">>> 给 agent 的步骤：")
    print("   1. 读 prompts/modify.md 完整指令")
    print(f"   2. 读 source: {source_path}")
    print(f"   3. 读 review: {review_path}")
    print(f"   4. LLM 按 review.suggestions 逐条改稿，套 primary_style 模板")
    print(f"   5. 把原稿备份到 {draft_dir}/source.md.bak（如果 modify.keep_original=true）")
    print(f"   6. 改稿写到 {article_path}")
    print(f"   7. update_draft_status('{draft_id}', 'modified')")

    # 占位 article.md
    if not article_path.exists():
        article_path.write_text(body, encoding="utf-8")
        bak = draft_dir / "source.md.bak"
        if not bak.exists():
            shutil.copy(source_path, bak)
        print(f"\n⚠️  写了占位 article.md（=source 原样），agent 真跑 LLM 后会覆盖")

    state = load_state()
    touch("modify", state)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
