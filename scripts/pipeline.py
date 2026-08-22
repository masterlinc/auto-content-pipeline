#!/usr/bin/env python3
"""
pipeline.py — CLI 入口

用法：
  pipeline.py scan
  pipeline.py review
  pipeline.py confirm <approved|rejected|modified> <brief_id> [note]
  pipeline.py write <brief_id>
  pipeline.py cover <brief_id>
  pipeline.py publish <brief_id>
  pipeline.py run-all            # 从 scan 跑到 publish（用户主动跑时用）
  pipeline.py status             # 看所有 brief 状态
"""

import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_stage(stage: str, *args) -> int:
    """调对应 stage 脚本。"""
    script = HERE / f"{stage}.py"
    if not script.exists():
        print(f"❌ stage script 不存在: {script}")
        return 1
    cmd = ["python3", str(script), *args]
    print(f"▶ {stage}: {' '.join(cmd[2:])}")
    r = subprocess.run(cmd)
    return r.returncode


def cmd_status() -> int:
    r = run_stage("brief", "list")
    return r


def cmd_run_all() -> int:
    """scan → review → 等用户确认（在 review 阶段就会等）→ 一条龙"""
    print("⚠️  run-all 模式：会跑 scan + review + 把所有 approved 的自动 write/cover/publish")
    print("   请先确保你已经在飞书/CLI 确认过哪些 brief 要做")
    print()
    for code in run_stage("scan"), run_stage("review"):
        if code != 0:
            return code
    # 找所有 approved 跑剩下的
    sys.path.insert(0, str(HERE))
    from state import list_briefs
    approved = [p for p, fm in list_briefs() if fm.get("status") == "approved"]
    print(f"找到 {len(approved)} 个 approved brief")
    for p, fm in approved:
        bid = fm.get("id")
        for stage in ("write", "cover", "publish"):
            if run_stage(stage, bid) != 0:
                print(f"❌ {stage} {bid} 失败，跳过")
                break
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "scan":
        return run_stage("scan", *args)
    elif cmd == "review":
        return run_stage("review", *args)
    elif cmd == "confirm":
        return run_stage("confirm", *args)
    elif cmd == "write":
        if not args:
            print("用法: pipeline.py write <brief_id>")
            return 1
        return run_stage("write", *args)
    elif cmd == "cover":
        if not args:
            print("用法: pipeline.py cover <brief_id>")
            return 1
        return run_stage("cover", *args)
    elif cmd == "publish":
        if not args:
            print("用法: pipeline.py publish <brief_id>")
            return 1
        return run_stage("publish", *args)
    elif cmd == "status":
        return cmd_status()
    elif cmd == "run-all":
        return cmd_run_all()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())