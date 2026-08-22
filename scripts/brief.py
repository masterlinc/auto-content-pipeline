#!/usr/bin/env python3
"""
brief 操作工具：创建 / 评分 / 推进状态。

每个 brief 是一个 .md，frontmatter 见 SKILL.md。
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

from state import (
    vault_root, now_iso, today_str,
    dump_frontmatter, write_brief, list_briefs, read_brief,
)


def slugify(text: str) -> str:
    """生成 brief_id。kebab-case，最长 60。"""
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:60] or "untitled"


def create_brief(
    title: str,
    source: str,
    raw_link: str = "",
    score: float = 0.0,
    tags=None,  # Optional[List[str]]
    deadline_hours: int = 36,
    body: str = "",
    summary: str = "",
):  # -> Path:
    """在 _briefs/ 下创建新 brief，返回路径。"""
    brief_id = f"{today_str()}_{slugify(title)}"
    root = vault_root()
    briefs_dir = root / "_briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)

    # 防重名
    target = briefs_dir / f"{brief_id}.md"
    if target.exists():
        i = 2
        while (briefs_dir / f"{brief_id}-{i}.md").exists():
            i += 1
        target = briefs_dir / f"{brief_id}-{i}.md"
        brief_id = target.stem

    deadline = (datetime.now() + timedelta(hours=deadline_hours)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"

    fm = {
        "id": brief_id,
        "created": now_iso(),
        "source": source,
        "status": "pending_review",
        "score": round(score, 1),
        "title": title,
        "tags": tags or [],
        "deadline": deadline,
        "raw_link": raw_link,
    }

    if summary:
        body = f"## 摘要\n\n{summary}\n\n{body}"

    write_brief(target, fm, body)
    return target


def update_status(brief_id: str, new_status: str, **extra) -> Path:
    """改 brief 状态，可以传 extra={key: value} 写进 frontmatter。"""
    path, fm, body = read_brief(brief_id)
    fm["status"] = new_status
    fm["updated"] = now_iso()
    for k, v in extra.items():
        fm[k] = v
    write_brief(path, fm, body)
    return path


def archive(brief_id: str, target_dir: str) -> Path:
    """移到 _published/ 或 _rejected/。"""
    path, fm, body = read_brief(brief_id)
    dest_dir = vault_root() / target_dir / fm["id"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    return dest


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        for p, fm in list_briefs():
            print(f"{fm.get('status','?'):20s} {fm.get('id','?'):50s} {fm.get('title','')}")
    elif cmd == "pending":
        for p, fm in list_briefs("pending_review"):
            print(f"{fm.get('id','?'):50s} score={fm.get('score','-')}  {fm.get('title','')}")
    else:
        print(__doc__)