#!/usr/bin/env python3
"""
v2 vault state I/O。

draft 状态机：
  pending → ingest_done → reviewed → modified → illustrated → stored → published
                                                  ↓
                                              failed（任意 stage 可失败）
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

DEFAULT_VAULT = Path.home() / "Documents" / "Obsidian Vault"
DRAFTS_DIR = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "草稿"
VALUE_DIR = DEFAULT_VAULT / "00-转型·一人事业" / "04-原创写作专区" / "价值文章"
LEGACY_BRIEFS = DEFAULT_VAULT / "07-选题与发布" / "_briefs"


def now_iso() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def vault_root() -> Path:
    cfg = Path(__file__).resolve().parent.parent / "config"
    for name in ("user.yaml", "default.yaml"):
        p = cfg / name
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("value_dir:"):
                    raw = line.split(":", 1)[1].strip().strip('"').strip("'")
                    return Path(os.path.expanduser(raw)).parent.parent.parent
    return DEFAULT_VAULT


def drafts_dir() -> Path:
    """skill 内部 _drafts/ 目录（在 skill 安装目录下，不在 vault）。"""
    p = Path(__file__).resolve().parent.parent / "_drafts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_file() -> Path:
    return drafts_dir() / "_state.json"


def load_state() -> dict:
    p = state_file()
    if not p.exists():
        return {
            "version": 2,
            "last_ingest": None,
            "last_review": None,
            "last_publish": None,
            "counters": {
                "drafts_total": 0,
                "reviewed_total": 0,
                "published_total": 0,
                "failed_total": 0,
            },
            "errors": [],
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    p = state_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def record_error(state: dict, code: str, msg: str) -> None:
    state.setdefault("errors", [])
    state["errors"].append({"code": code, "msg": msg, "at": now_iso()})
    state["errors"] = state["errors"][-20:]


def touch(stage: str, state: dict) -> None:
    state[f"last_{stage}"] = now_iso()


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 5:]
    fm = {}
    current_list_key = None
    for raw in fm_block.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_list_key:
            fm[current_list_key].append(line[4:].strip().strip('"').strip("'"))
            continue
        m = __import__("re").match(r"^([\w_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            fm[key] = []
            current_list_key = key
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            current_list_key = None
        else:
            fm[key] = val.strip('"').strip("'")
            current_list_key = None
    return fm, body


def dump_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            else:
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def read_draft(draft_id: str) -> Tuple[Path, dict, str]:
    """找 draft 目录里的 source.md，返回 (path, frontmatter, body)。"""
    root = drafts_dir() / draft_id
    if not root.exists():
        raise FileNotFoundError(f"draft not found: {draft_id}")
    p = root / "source.md"
    if not p.exists():
        raise FileNotFoundError(f"source.md not found in {root}")
    text = p.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    return p, fm, body


def update_draft_status(draft_id: str, new_status: str, **extra) -> Path:
    """更新 draft 的 source.md 的 frontmatter status 字段。"""
    root = drafts_dir() / draft_id
    source = root / "source.md"
    fm, body = parse_frontmatter(source.read_text(encoding="utf-8"))
    fm["status"] = new_status
    fm["updated"] = now_iso()
    for k, v in extra.items():
        fm[k] = v
    source.write_text(dump_frontmatter(fm) + "\n\n" + body.lstrip(), encoding="utf-8")
    return source


def list_drafts(status: Optional[str] = None) -> List[Tuple[Path, dict]]:
    root = drafts_dir()
    out = []
    for d in sorted(root.glob("draft-*")):
        source = d / "source.md"
        if not source.exists():
            continue
        fm, _ = parse_frontmatter(source.read_text(encoding="utf-8"))
        if status is None or fm.get("status") == status:
            out.append((d, fm))
    return out


if __name__ == "__main__":
    print("vault:", vault_root())
    print("drafts_dir:", drafts_dir())
    print("state:", load_state())
