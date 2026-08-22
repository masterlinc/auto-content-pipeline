#!/usr/bin/env python3
"""
Vault 状态 I/O + 全局 helper。

错误码（写到 _state.json 的 errors 字段）：
  E_SCAN_NO_SOURCE       scan 阶段所有源都失败
  E_SCAN_RATE_LIMIT      某个源被限流
  E_REVIEW_EMPTY         review 时没有 pending brief
  E_WRITE_STYLE_MISSING  风格文件不存在
  E_COVER_GEN_FAIL       image_generate 失败
  E_PUBLISH_LOGIN        xiaohongshu 没登录
  E_PUBLISH_UI_DRIFT     小红书 UI 改了，selector 找不到（要修 xiaohongshu_poster.py）
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_VAULT = Path.home() / "Documents" / "Obsidian Vault" / "07-选题与发布"
TZ_OFFSET = "+08:00"


def now_iso() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def vault_root() -> Path:
    """读 config/user.yaml 优先，否则 default.yaml，最后默认路径。"""
    cfg = Path(__file__).resolve().parent.parent / "config"
    for name in ("user.yaml", "default.yaml"):
        p = cfg / name
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*root:\s*(.+)$", line)
                if m:
                    raw = m.group(1).strip().strip('"').strip("'")
                    return Path(os.path.expanduser(raw))
    return DEFAULT_VAULT


def state_file() -> Path:
    return vault_root() / "_state.json"


def load_state() -> dict:
    p = state_file()
    if not p.exists():
        return {
            "version": 1,
            "last_scan": None,
            "last_review": None,
            "last_publish": None,
            "counters": {
                "scanned_total": 0,
                "briefs_total": 0,
                "published_total": 0,
                "rejected_total": 0,
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
    state["errors"].append(
        {"code": code, "msg": msg, "at": now_iso()}
    )
    # 只保留最近 20 条
    state["errors"] = state["errors"][-20:]


def touch(stage: str, state: dict) -> None:
    state[f"last_{stage}"] = now_iso()


# ======== brief frontmatter 工具 ========

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """返回 (frontmatter_dict, body_str)。支持 --- 包裹的 YAML-ish 简单格式。"""
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
        m = re.match(r"^([\w_-]+):\s*(.*)$", line)
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
    """把 dict 序列化成 --- 包裹的 frontmatter。"""
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


def read_brief(brief_id: str) -> tuple[Path, dict, str]:
    """找到 brief 文件，返回 (path, frontmatter, body)。"""
    root = vault_root() / "_briefs"
    matches = list(root.glob(f"{brief_id}*.md"))
    if not matches:
        raise FileNotFoundError(f"brief not found: {brief_id}")
    p = matches[0]
    text = p.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    return p, fm, body


def write_brief(path: Path, fm: dict, body: str) -> None:
    text = dump_frontmatter(fm) + "\n\n" + body.lstrip()
    path.write_text(text, encoding="utf-8")


def list_briefs(status=None):  # Optional[str]
    root = vault_root() / "_briefs"
    out = []
    for p in sorted(root.glob("*.md")):
        fm, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
        if status is None or fm.get("status") == status:
            out.append((p, fm))
    return out


if __name__ == "__main__":
    # smoke test
    print("vault:", vault_root())
    print("state:", load_state())