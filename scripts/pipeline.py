#!/usr/bin/env python3
"""Auto Content Pipeline v3 — two commands, no agent harness required.

Recommended:
  pipeline.py package <article.md> [--output <directory>]
  pipeline.py check <package-directory>

The legacy commands remain for existing users, but v3 does not invoke Codex,
browser automation, or an implicit image-generation tool.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

LEGACY = {
    "review": "review.py",
    "modify": "modify.py",
    "illustrate": "illustrate.py",
    "store": "store.py",
    "sync-feishu": "feishu_sync.py",
    "feishu-review": "feishu_review.py",
    "publish": "publish.py",
}


def invoke(script: str, *args: str) -> int:
    return subprocess.call(["python3", str(HERE / script), *args])


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    command, args = sys.argv[1], sys.argv[2:]
    if command in ("package", "make", "run-all"):
        if not args:
            print("用法: pipeline.py package <文章.md> [--output <目录>]")
            return 1
        return invoke("package.py", "make", *args)
    if command == "check":
        if len(args) != 1:
            print("用法: pipeline.py check <发布包目录>")
            return 1
        return invoke("package.py", "check", args[0])
    if command == "ingest":
        return invoke("ingest.py", *args)
    if command in ("feishu-sync",):
        command = "sync-feishu"
    if command in ("feishu-feedback",):
        command = "feishu-review"
    script = LEGACY.get(command)
    if not script or not args:
        print(__doc__)
        return 1
    return invoke(script, *args)


if __name__ == "__main__":
    raise SystemExit(main())
