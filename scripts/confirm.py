#!/usr/bin/env python3
"""
Stage 3: confirm — 接收 linc 决策，更新 brief 状态

用法：
  pipeline.py confirm approved <brief_id>
  pipeline.py confirm rejected <brief_id> [reason]
  pipeline.py confirm modified <brief_id> <new_title>

linc 也可以在飞书直接说"OK #3" / "拒 #2" / "改：xxx"，agent 收到后调本脚本。
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from brief import update_status, archive
from state import load_state, save_state


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    decision = sys.argv[1]
    brief_id = sys.argv[2]
    note = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

    state = load_state()

    if decision == "approved":
        path = update_status(brief_id, "approved", decision_note=note)
        print(f"✅ {brief_id} → approved（待写文章）")
        print(f"   下一步: pipeline.py write {brief_id}")
        state["counters"]["approved_total"] = state["counters"].get("approved_total", 0) + 1
    elif decision == "rejected":
        archive(brief_id, "_rejected")
        print(f"🗑️  {brief_id} → 移到 _rejected/")
        state["counters"]["rejected_total"] = state["counters"].get("rejected_total", 0) + 1
    elif decision == "modified":
        if not note:
            print("❌ modified 必须给新标题：confirm modified <id> <new_title>")
            return 1
        path = update_status(brief_id, "awaiting_user", modified_title=note, decision_note="linc 修改")
        print(f"✏️  {brief_id} 标题改为: {note}")
        print(f"   还在 awaiting_user，等 linc 再点一次 approved")
    else:
        print(f"❌ 未知决策: {decision}（approved / rejected / modified）")
        return 1

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())