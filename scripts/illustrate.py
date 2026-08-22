#!/usr/bin/env python3
"""
Stage 4: illustrate — 生成封面 + 正文配图
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import drafts_dir, read_draft, load_state, save_state, touch


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py illustrate <draft_id>")
        sys.exit(1)
    draft_id = sys.argv[1]

    try:
        source_path, fm, _ = read_draft(draft_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    draft_dir = source_path.parent
    article_path = draft_dir / "article.md"
    if not article_path.exists():
        print(f"❌ article.md 不存在，先跑 modify stage")
        return 1

    print(f"\n=== illustrate stage: {draft_id} ===")
    print()
    print(">>> 给 agent 的步骤：")
    print("   1. 读 prompts/illustrate.md")
    print(f"   2. 读 article: {article_path}")
    print("   3. LLM 生成封面 prompt，调 image_generate(3:4, 1242x1660)")
    print(f"   4. 封面写到 {draft_dir}/cover.png")
    print("   5. 生成 2-3 张正文配图（minimal-diagram / flat-illustration）")
    print(f"   6. 写到 {draft_dir}/body-img-1.png / 2.png / 3.png")
    print(f"   7. 把图引用插入 article.md，更新 frontmatter.illustrations 字段")
    print(f"   8. update_draft_status('{draft_id}', 'illustrated')")

    state = load_state()
    touch("illustrate", state)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
