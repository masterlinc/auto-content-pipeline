#!/usr/bin/env python3
"""
Stage 5: cover — 生成封面图

工作模式：
  agent 读到本文件后：
    1. 读 prompts/cover.md
    2. 读 _config/style-cover.md（必读）
    3. 读 _drafts/<brief_id>/article.md
    4. LLM 基于文章标题 + 风格规范，生成封面 prompt
    5. 调 image_generate（OpenClaw 原生工具）
    6. 写到 _drafts/<brief_id>/cover.png
    7. update_status(brief_id, 'awaiting_publish')
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import vault_root, load_state
from brief import update_status


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py cover <brief_id>")
        return 1
    brief_id = sys.argv[1]

    state = load_state()
    draft_dir = vault_root() / "_drafts" / brief_id
    article = draft_dir / "article.md"
    cover_path = draft_dir / "cover.png"
    cover_prompt_path = draft_dir / "cover-prompt.md"

    if not article.exists():
        print(f"❌ 找不到 {article}，先跑 write stage")
        return 1

    print(f"\n=== cover stage: {brief_id} ===")
    print(f"\n>>> 给 agent 的步骤：")
    print(f"   1. 读 prompts/cover.md")
    print(f"   2. 读 _config/style-cover.md（封面风格）")
    print(f"   3. 读 {article}")
    print(f"   4. LLM 生成封面 prompt（英文，中文标题翻译成对应英文/视觉描述）")
    print(f"   5. 调 image_generate(prompt=<prompt>, aspectRatio='3:4', size='1242x1660', outputFormat='png')")
    print(f"   6. 保存到 {cover_path}")
    print(f"   7. 把 prompt 也写到 {cover_prompt_path}（linc 之后想重画可以参考）")
    print(f"   8. update_status('{brief_id}', 'awaiting_publish')")
    print(f"   9. pipeline.py publish {brief_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())