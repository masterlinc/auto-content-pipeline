#!/usr/bin/env python3
"""
Stage 2: review — 复核 brief → 选 top N → 推送飞书

工作模式：
  agent 读到本文件后：
    1. 读 prompts/review.md
    2. 扫 _briefs/ status=pending_review 的
    3. LLM 二次评分（结合当日热度变化）
    4. 选 top N（默认 3），update_status → awaiting_user
    5. 生成 daily-pick-YYYY-MM-DD.md 汇总（写到 _briefs/ 同级）
    6. 推送飞书（用 message tool）让 linc 决策
    7. 写 _state.json last_review
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import vault_root, load_state, save_state, touch, today_str, list_briefs, now_iso, record_error
from brief import update_status


def main() -> int:
    state = load_state()
    touch("review", state)

    pending = [(p, fm) for p, fm in list_briefs("pending_review")]
    print(f"\n=== review stage @ {now_iso()} ===")
    print(f"pending briefs: {len(pending)}")

    if not pending:
        print("没有待复核 brief，跳过推送")
        record_error(state, "E_REVIEW_EMPTY", "没有 pending_review brief")
        save_state(state)
        return 0

    print(f"\n>>> 给 agent 的步骤：")
    print(f"   1. 读 prompts/review.md")
    print(f"   2. 读 _config/style-config.yaml 确认账号定位")
    print(f"   3. web_search 复核 {len(pending)} 个 brief 的当前热度（24h 内是否还热）")
    print(f"   4. LLM 重新评分，挑 top {state.get('review_top_n', 3)}")
    print(f"   5. 对每个选中的 brief 调 update_status(brief_id, 'awaiting_user', score=new_score)")
    print(f"   6. 未选中的：status 保持 pending_review（明早 review 再看）")
    print(f"   7. 生成 _briefs/daily-pick-{today_str()}.md 汇总")
    print(f"   8. 推送飞书：用 message tool，内容参考 prompts/confirm-message.md")
    print(f"   9. save_state(state) — last_review 已写")
    return 0


if __name__ == "__main__":
    sys.exit(main())