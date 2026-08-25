#!/usr/bin/env python3
"""Legacy stage: actually generate local information cards, without an agent."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from media import create_assets, insert_body_images
from state import load_state, read_draft, save_state, touch, update_draft_status


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: pipeline.py illustrate <draft_id>")
        return 1
    draft_id = sys.argv[1]
    try:
        source_path, _, _ = read_draft(draft_id)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1
    article = source_path.parent / "article.md"
    if not article.exists():
        print("❌ article.md 不存在，先准备正文")
        return 1
    markdown = article.read_text(encoding="utf-8")
    assets = create_assets(markdown, source_path.parent, body_count=2)
    body_files = [asset["file"] for asset in assets if asset["role"] == "body"]
    article.write_text(insert_body_images(markdown, body_files), encoding="utf-8")
    update_draft_status(draft_id, "illustrated", illustrations=[asset["file"] for asset in assets])
    state = load_state()
    touch("illustrate", state)
    save_state(state)
    print(f"✅ 已生成 {len(assets)} 张图：{source_path.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
