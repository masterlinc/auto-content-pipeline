#!/usr/bin/env python3
"""
Stage 6: publish — 发布到小红书

包装现有的 ~/.openclaw/workspace/xiaohongshu_poster.py：
  - 把 _drafts/<id>/article.md 转成 article_to_post.txt 格式
  - 把 _drafts/<id>/cover.png 复制到 ~/.openclaw/workspace/article_cover.png
  - 调 xiaohongshu_poster.py post
  - 移到 _published/<id>/

不直接改 xiaohongshu_poster.py —— 那是另一份独立脚本，
我们只通过文件接口集成。
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
POSTER = HOME / ".openclaw" / "workspace" / "xiaohongshu_poster.py"
ARTICLE_TXT = HOME / ".openclaw" / "workspace" / "article_to_post.txt"
COVER_HINT = HOME / ".openclaw" / "workspace" / "article_cover.png"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import vault_root, load_state, save_state, touch, record_error, now_iso
from brief import update_status, archive


def format_for_poster(article_md: Path, title: str, tags: list[str]) -> str:
    """把 .md 转成 xiaohongshu_poster.py 认识的格式。

    xiaohongshu_poster.py 的逻辑：
      - 如果含 '---'，split 后第一段是标题，后面是正文
      - 否则前 30 字当标题，全文当正文
    """
    body = article_md.read_text(encoding="utf-8")
    # 去 frontmatter
    if body.startswith("---"):
        end = body.find("\n---\n", 4)
        if end > 0:
            body = body[end + 5:]

    # 把标题拼在前面 + ---
    parts = [f"# {title}", "---", body.strip()]
    if tags:
        parts.append("")
        parts.append(" ".join(f"#{t}" for t in tags))
    return "\n".join(parts)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: pipeline.py publish <brief_id>")
        return 1
    brief_id = sys.argv[1]

    state = load_state()

    draft_dir = vault_root() / "_drafts" / brief_id
    article_md = draft_dir / "article.md"
    cover_png = draft_dir / "cover.png"

    if not article_md.exists():
        print(f"❌ 找不到 {article_md}")
        record_error(state, "E_PUBLISH_NO_ARTICLE", brief_id)
        save_state(state)
        return 1

    if not cover_png.exists():
        print(f"⚠️  找不到 {cover_png}，没封面能发，但可以试试纯文")

    # 读 brief frontmatter 拿 title 和 tags
    from state import read_brief
    _, fm, _ = read_brief(brief_id)
    title = fm.get("title", "未命名")
    tags = fm.get("tags") or []

    # 1. 写 article_to_post.txt
    text = format_for_poster(article_md, title, tags)
    ARTICLE_TXT.write_text(text, encoding="utf-8")
    print(f"📝 已写 {ARTICLE_TXT}")

    # 2. 复制封面
    if cover_png.exists():
        shutil.copy(cover_png, COVER_HINT)
        print(f"🖼️  已复制封面到 {COVER_HINT}")

    # 3. 调 xiaohongshu_poster.py post
    print(f"🚀 调 xiaohongshu_poster.py post ...")
    result = subprocess.run(["python3", str(POSTER), "post"], cwd=POSTER.parent)
    if result.returncode != 0:
        print(f"❌ xiaohongshu_poster 返回 {result.returncode}")
        record_error(state, "E_PUBLISH_FAILED", brief_id)
        save_state(state)
        return 1

    # 4. 归档
    archive(brief_id, "_published")
    update_status(brief_id, "published", published_at=now_iso())
    touch("publish", state)
    state["counters"]["published_total"] = state["counters"].get("published_total", 0) + 1
    save_state(state)

    print(f"\n✅ {brief_id} 已发布并归档到 _published/")
    return 0


if __name__ == "__main__":
    sys.exit(main())