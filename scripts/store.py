#!/usr/bin/env python3
"""
Stage 5: store — 搬到 vault 价值文章区
"""

import sys
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import (
    drafts_dir, read_draft, load_state, save_state, touch, now_iso,
    DEFAULT_VAULT,
)


VALUE_DIR = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "价值文章"


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py store <draft_id>")
        sys.exit(1)
    draft_id = sys.argv[1]

    try:
        source_path, fm, _ = read_draft(draft_id)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    draft_dir = source_path.parent
    article = draft_dir / "article.md"
    cover = draft_dir / "cover.png"
    review = draft_dir / "review.json"

    if not article.exists():
        print(f"❌ article.md 不存在，先跑 modify stage")
        return 1

    target = VALUE_DIR / draft_id
    if target.exists():
        print(f"⚠️  目标已存在: {target}")
        print(f"   删了重跑或换 draft_id")
        return 1

    target.mkdir(parents=True, exist_ok=True)

    # 复制文件
    shutil.copy(article, target / "article.md")
    if cover.exists():
        shutil.copy(cover, target / "cover.png")
    for i in (1, 2, 3):
        bi = draft_dir / f"body-img-{i}.png"
        if bi.exists():
            shutil.copy(bi, target / f"body-img-{i}.png")

    # 复制 review
    if review.exists():
        shutil.copy(review, target / "review.json")

    # 写 meta.json
    review_data = {}
    if review.exists():
        try:
            review_data = json.loads(review.read_text(encoding="utf-8"))
        except Exception:
            pass

    meta = {
        "draft_id": draft_id,
        "stored_at": now_iso(),
        "title": fm.get("title", ""),
        "primary_style": review_data.get("primary_style", ""),
        "review_score": review_data.get("weighted_total", 0),
        "word_count": fm.get("word_count", 0),
        "illustration_count": sum(1 for i in (1, 2, 3) if (target / f"body-img-{i}.png").exists()) + (1 if cover.exists() else 0),
        "publish_status": "pending",
        "published_platforms": [],
        "vault_path": f"00-转型·一人事业/04-原创写作专区/价值文章/{draft_id}/",
    }
    (target / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # 更新 _index.md
    index_path = VALUE_DIR / "_index.md"
    entry = f"- [{fm.get('title', '?')}]({draft_id}/article.md) — {meta['primary_style'] or '?'}风 — 评分 {meta['review_score']} — 待发布"
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if entry not in existing:
            new = existing.replace("# 价值文章索引\n\n", f"# 价值文章索引\n\n## {now_iso()[:10]}\n\n", 1)
            new = entry + "\n" + new.split("\n", 1)[1] if "\n##" in new else entry + "\n" + existing
            index_path.write_text(new, encoding="utf-8")
    else:
        index_path.write_text(f"# 价值文章索引\n\n## {now_iso()[:10]}\n\n{entry}\n", encoding="utf-8")

    print(f"\n✅ stored → {target}")
    print(f"   meta.json: {target}/meta.json")

    state = load_state()
    touch("store", state)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
