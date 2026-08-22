#!/usr/bin/env python3
"""
pipeline.py — CLI 入口（v3: Codex Harness Edition）

默认走 Codex Harness（v3），v2 stage 脚本作为 fallback。

用法：
  pipeline.py ingest <草稿.md>
  pipeline.py ingest --from-vault
  pipeline.py review <draft_id>          # v3: 调 codex_runner
  pipeline.py modify <draft_id>          # v3: 调 codex_runner
  pipeline.py illustrate <draft_id>      # v3: 调 codex_runner
  pipeline.py store <draft_id>           # v3: 调 codex_runner
  pipeline.py publish <draft_id> [--platforms xiaohongshu,juejin]
  pipeline.py run-all <草稿.md>          # ingest → store 全跑
  pipeline.py status                      # 看所有 draft 状态

环境变量：
  ACP_USE_V2=1    # 强制走 v2 stage 脚本（不走 Codex）
  ACP_DRY_RUN=1   # 只打印 prompt 不真调 Codex
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

USE_V2 = os.environ.get("ACP_USE_V2") == "1"
DRY_RUN = os.environ.get("ACP_DRY_RUN") == "1"
CODEX_BIN = shutil.which("codex")


def run_v3(stage: str, draft_id: str, *extra) -> int:
    """v3: 调 codex_runner.py。"""
    if not CODEX_BIN and not DRY_RUN:
        print(f"⚠️  codex CLI 未装，自动降级到 v2 stage 脚本")
        return run_v2(stage, draft_id)

    cmd = ["python3", str(HERE / "codex_runner.py"), stage, "--draft-id", draft_id]
    if DRY_RUN:
        cmd.append("--dry-run")
    if extra:
        cmd.extend(extra)
    print(f"▶ v3/{stage}: {' '.join(cmd[2:])}")
    return subprocess.call(cmd)


def run_v2(stage: str, draft_id: str, *extra) -> int:
    """v2: 调原 stage 脚本（fallback）。"""
    if stage == "review":
        script = "review.py"
    elif stage == "modify":
        script = "modify.py"
    elif stage == "illustrate":
        script = "illustrate.py"
    elif stage == "store":
        script = "store.py"
    elif stage == "publish":
        script = "publish.py"
    else:
        print(f"❌ 未知 stage: {stage}")
        return 1
    cmd = ["python3", str(HERE / script), draft_id]
    if extra:
        cmd.extend(extra)
    print(f"▶ v2/{stage}: {' '.join(cmd[2:])}")
    return subprocess.call(cmd)


def cmd_status() -> int:
    """看所有 draft 状态。"""
    from state import list_drafts, load_state, drafts_dir
    state = load_state()
    print(f"vault:  {drafts_dir()}")
    print(f"状态:  {state.get('counters', {})}")
    print()
    drafts = list_drafts()
    if not drafts:
        print("(无 draft)")
        return 0
    for p, fm in drafts:
        print(f"  [{fm.get('status','?'):20s}] {fm.get('id','?'):50s} {fm.get('title','?')[:40]}")
    return 0


def cmd_run_all(ingest_arg: str) -> int:
    """从 ingest 一条龙到 store。"""
    print(f"⚠️  run-all: ingest → review → modify → illustrate → store")
    print(f"   publish 单独跑，避免误发")
    print()

    # ingest 总是用 v2（轻量）
    r = subprocess.run(["python3", str(HERE / "ingest.py"), ingest_arg])
    if r.returncode != 0:
        return r.returncode

    from state import drafts_dir
    drafts = sorted(drafts_dir().glob("draft-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not drafts:
        print("❌ 找不到刚 ingest 的 draft")
        return 1
    draft_id = drafts[0].name
    print(f"\n检测到新 draft: {draft_id}\n")

    # 后面 stage 默认走 v3（Codex），除非 ACP_USE_V2=1
    runner = run_v2 if USE_V2 else run_v3
    for stage in ("review", "modify", "illustrate", "store"):
        if runner(stage, draft_id) != 0:
            print(f"❌ {stage} {draft_id} 失败，停止")
            return 1
    print(f"\n✅ 一条龙完成。draft_id = {draft_id}")
    print(f"   下一步：ACP_DRY_RUN=1 python3 $ACP/scripts/pipeline.py publish {draft_id} --platforms xiaohongshu")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if USE_V2:
        print(f"⚙️  ACP_USE_V2=1 → 走 v2 stage 脚本")
    if DRY_RUN:
        print(f"⚙️  ACP_DRY_RUN=1 → 只打印 prompt")
    if not USE_V2 and not CODEX_BIN and not DRY_RUN:
        print(f"⚠️  codex CLI 未装，降级到 v2（如要 v3：`npm i -g @openai/codex`）")
        print()

    runner = run_v2 if USE_V2 else run_v3

    if cmd == "ingest":
        return subprocess.call(["python3", str(HERE / "ingest.py")] + args)
    elif cmd == "review":
        if not args:
            print("用法: pipeline.py review <draft_id>")
            return 1
        return runner("review", args[0])
    elif cmd == "modify":
        if not args:
            print("用法: pipeline.py modify <draft_id>")
            return 1
        return runner("modify", args[0])
    elif cmd == "illustrate":
        if not args:
            print("用法: pipeline.py illustrate <draft_id>")
            return 1
        return runner("illustrate", args[0])
    elif cmd == "store":
        if not args:
            print("用法: pipeline.py store <draft_id>")
            return 1
        return runner("store", args[0])
    elif cmd == "publish":
        if not args:
            print("用法: pipeline.py publish <draft_id> [--platforms xiaohongshu,juejin]")
            return 1
        return runner("publish", args[0], *args[1:])
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
