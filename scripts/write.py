#!/usr/bin/env python3
"""
Stage 4: write — 按 brief 写文章，符合固化风格

工作模式：
  agent 读到本文件后：
    1. 读 prompts/write.md（完整指令）
    2. 读 _config/style-document.md（必读）
    3. 读 brief frontmatter + body
    4. LLM 按风格规范生成文章
    5. 写到 _drafts/<brief_id>/article.md
    6. update_status(brief_id, 'awaiting_cover')
"""

import sys
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import vault_root, load_state, save_state, read_brief
from brief import update_status


def setup_draft_dir(brief_id: str) -> Path:
    draft_dir = vault_root() / "_drafts" / brief_id
    draft_dir.mkdir(parents=True, exist_ok=True)
    return draft_dir


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py write <brief_id>")
        return 1
    brief_id = sys.argv[1]

    state = load_state()

    try:
        brief_path, fm, body = read_brief(brief_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    if fm.get("status") != "approved":
        print(f"⚠️  brief 当前 status={fm.get('status')}，要求 approved")
        print(f"   先 pipeline.py confirm approved {brief_id}")
        return 1

    draft_dir = setup_draft_dir(brief_id)
    print(f"\n=== write stage: {brief_id} ===")
    print(f"draft dir: {draft_dir}")
    print(f"\n>>> 给 agent 的步骤：")
    print(f"   1. 读 prompts/write.md")
    print(f"   2. 读 _config/style-document.md（风格规范）")
    print(f"   3. 读 brief frontmatter:")
    print(f"      title: {fm.get('title')}")
    print(f"      tags:  {fm.get('tags')}")
    print(f"      source: {fm.get('source')}")
    print(f"      raw_link: {fm.get('raw_link')}")
    print(f"   4. LLM 生成 300-700 字文章（严格按 style-document.md）")
    print(f"   5. 写到 {draft_dir}/article.md")
    print(f"   6. update_status('{brief_id}', 'awaiting_cover')")
    print(f"   7. pipeline.py cover {brief_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())