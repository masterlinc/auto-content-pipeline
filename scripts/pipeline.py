#!/usr/bin/env python3
"""
pipeline.py — CLI 入口（v2）

用法：
  pipeline.py ingest <草稿.md>
  pipeline.py ingest --from-vault
  pipeline.py review <draft_id>
  pipeline.py modify <draft_id>
  pipeline.py illustrate <draft_id>
  pipeline.py store <draft_id>
  pipeline.py publish <draft_id> [--platforms xiaohongshu,juejin,...]
  pipeline.py run-all <草稿.md>           # 一条龙：ingest → store
  pipeline.py status                       # 看所有 draft 状态
"""

import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_stage(stage: str, *args) -> int:
    script = HERE / f"{stage}.py"
    if not script.exists():
        print(f"❌ stage script 不存在: {script}")
        return 1
    cmd = ["python3", str(script), *args]
    print(f"▶ {stage}: {' '.join(cmd[2:])}")
    r = subprocess.run(cmd)
    return r.returncode


def cmd_status() -> int:
    return run_stage("state")  # state.py 直接打印当前状态


def cmd_run_all(ingest_arg: str) -> int:
    """从 ingest 一条龙到 store（publish 单独需要 --platforms 触发）。"""
    print(f"⚠️  run-all: ingest → review → modify → illustrate → store")
    print(f"   publish 单独跑，避免误发到错误平台")
    print()

    # ingest
    r = subprocess.run(["python3", str(HERE / "ingest.py"), ingest_arg])
    if r.returncode != 0:
        return r.returncode

    # 从 ingest 输出拿 draft_id（ingest.py 打印了 "✅ ingested → draft-XXX"）
    # 简单做法：扫 drafts_dir 取最新的
    from state import drafts_dir, parse_frontmatter
    drafts = sorted(drafts_dir().glob("draft-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not drafts:
        print("❌ 找不到刚 ingest 的 draft")
        return 1
    draft_id = drafts[0].name
    print(f"\n检测到新 draft: {draft_id}\n")

    for stage in ("review", "modify", "illustrate", "store"):
        if run_stage(stage, draft_id) != 0:
            print(f"❌ {stage} {draft_id} 失败，停止")
            return 1
    print(f"\n✅ 一条龙到 store 完成。draft_id = {draft_id}")
    print(f"   下一步：pipeline.py publish {draft_id} --platforms xiaohongshu")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "ingest":
        return run_stage("ingest", *args)
    elif cmd == "review":
        if not args:
            print("用法: pipeline.py review <draft_id>")
            return 1
        return run_stage("review", *args)
    elif cmd == "modify":
        if not args:
            print("用法: pipeline.py modify <draft_id>")
            return 1
        return run_stage("modify", *args)
    elif cmd == "illustrate":
        if not args:
            print("用法: pipeline.py illustrate <draft_id>")
            return 1
        return run_stage("illustrate", *args)
    elif cmd == "store":
        if not args:
            print("用法: pipeline.py store <draft_id>")
            return 1
        return run_stage("store", *args)
    elif cmd == "publish":
        if not args:
            print("用法: pipeline.py publish <draft_id> [--platforms xiaohongshu,juejin,...]")
            return 1
        return run_stage("publish", *args)
    elif cmd == "status":
        return cmd_status()
    elif cmd == "run-all":
        if not args:
            print("用法: pipeline.py run-all <草稿.md>")
            return 1
        return cmd_run_all(args[0])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
