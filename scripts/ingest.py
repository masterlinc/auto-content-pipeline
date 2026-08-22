#!/usr/bin/env python3
"""
Stage 1: ingest — 把草稿收进来

支持来源：
- 命令行传入的文件路径
- vault 草稿区（00-转型·一人事业/04-原创写作专区/草稿/*.md）
- scan 遗留 brief（v1 兼容，07-选题与发布/_briefs/*.md）
"""

import sys
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import (
    drafts_dir, load_state, save_state, touch, now_iso, today_str,
    dump_frontmatter, parse_frontmatter, DEFAULT_VAULT,
)


def slugify(text: str) -> str:
    import re
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:50] or "untitled"


def make_draft_id(title: str) -> str:
    return f"draft-{today_str()}_{slugify(title)}"


def setup_draft_dir(draft_id: str) -> Path:
    d = drafts_dir() / draft_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def ingest_file(path: str) -> Path:
    src = Path(path).expanduser().resolve()
    if not src.exists():
        print(f"❌ 文件不存在: {src}")
        sys.exit(1)

    text = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # 取标题（frontmatter.title > 文件名 > 正文首行）
    title = fm.get("title") or src.stem
    body_first_line = body.strip().split("\n", 1)[0].lstrip("# ").strip()
    if not fm.get("title") and body_first_line:
        title = body_first_line[:60]

    draft_id = make_draft_id(title)
    draft_dir = setup_draft_dir(draft_id)
    target = draft_dir / "source.md"

    # 写 frontmatter
    fm_out = {
        "draft_id": draft_id,
        "ingested_at": now_iso(),
        "source": "user_upload",
        "original_path": str(src),
        "title": title,
        "word_count": len([c for c in body if '\u4e00' <= c <= '\u9fff']),
        "status": "ingest_done",
    }
    # 保留原 frontmatter 的 tags 等字段
    for k, v in fm.items():
        if k not in fm_out and k not in ("draft_id", "status"):
            fm_out[k] = v

    target.write_text(dump_frontmatter(fm_out) + "\n\n" + body.lstrip(), encoding="utf-8")

    state = load_state()
    touch("ingest", state)
    state["counters"]["drafts_total"] = state["counters"].get("drafts_total", 0) + 1
    save_state(state)

    print(f"✅ ingested → {draft_id}")
    print(f"   路径: {target}")
    print(f"   字数: {fm_out['word_count']}")
    return target


def ingest_from_vault_dir() -> list:
    """扫描 vault 草稿区所有 .md，返回 ingest 后的 draft_id 列表。"""
    drafts = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "草稿"
    if not drafts.exists():
        print(f"❌ 草稿区不存在: {drafts}")
        return []
    out = []
    for f in sorted(drafts.glob("*.md")):
        try:
            target = ingest_file(str(f))
            out.append(target)
        except Exception as e:
            print(f"⚠️  {f.name}: {e}")
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py ingest <草稿.md>")
        print("      pipeline.py ingest --from-vault  # 扫整个 vault 草稿区")
        sys.exit(1)

    if sys.argv[1] == "--from-vault":
        ingest_from_vault_dir()
        return 0

    ingest_file(sys.argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
