#!/usr/bin/env python3
"""
Stage 1: scan — 抓全网热点 → 生成 brief

工作模式（重要）：
  这个脚本主要是给 **agent** 跑的，不是直接命令行。
  Agent 读到本文件后：
    1. 读 prompts/scan.md 拿到完整指令
    2. 用 web_search / web_fetch 抓热点
    3. 读 _config/sources.json 知道从哪抓
    4. 读 _config/style-config.yaml 知道账号定位
    5. 调 brief.create_brief() 生成 brief

如果被 cron 当脚本调（payload.kind=agentTurn），
cron 的 message 会告诉 agent 调 scan，agent 读 SKILL.md 知道怎么做。

本文件提供：
  - main() 入口（agent 视角的提示）
  - print_sources() 列出源
  - dedup_check() 查重
"""

import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import vault_root, load_state, save_state, record_error, touch, today_str, list_briefs, now_iso  # noqa: F401
from brief import create_brief


CONFIG_FILE = vault_root() / "_config" / "style-config.yaml"
SOURCES_FILE = vault_root() / "_config" / "sources.json"


def print_sources():
    """读 sources.json，返回 sources 列表。"""
    if not SOURCES_FILE.exists():
        print(f"❌ 找不到 {SOURCES_FILE}")
        return []
    data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    return data.get("sources", [])


def dedup_check(title: str, window_days: int = 7) -> bool:
    """如果 7 天内有相似标题，返回 True（重复）。"""
    from difflib import SequenceMatcher
    target = title.lower()
    for p, fm in list_briefs():
        existing = fm.get("title", "").lower()
        sim = SequenceMatcher(None, target, existing).ratio()
        if sim > 0.7:
            print(f"  ↺ 重复（相似度 {sim:.2f}）: {existing}")
            return True
    return False


def main() -> int:
    """
    主入口。

    当 cron 调本脚本时（payload.kind=agentTurn, message="请跑 auto-content-pipeline 的 scan stage"），
    是 agent 本身在跑，所以本 main() 主要做：
      - 加载 context
      - 打印提示 agent 该读哪些文件
      - 不直接生成 brief（那是 LLM 干的活）

    当用户直接跑（python3 scan.py），
    打印源清单和去重参考，让用户/agent 接着干。
    """
    state = load_state()
    touch("scan", state)
    save_state(state)

    sources = print_sources()
    print(f"\n=== scan stage @ {now_iso()} ===")
    print(f"账号: 看 _config/style-config.yaml")
    print(f"源 ({len(sources)} 个):")
    for s in sources:
        print(f"  - {s.get('id')}: {s.get('url')}  ({s.get('note','')})")

    print(f"\n待生成 brief 上限: 8 (看 _config/style-config.yaml 的 scan.max_briefs)")
    print(f"\n>>> 下一步给 agent：")
    print(f"   1. 读 prompts/scan.md（详细指令）")
    print(f"   2. 用 web_search / web_fetch 抓每个源的热点")
    print(f"   3. LLM 评估每个候选主题（0-10 分）")
    print(f"   4. dedup_check() 查重")
    print(f"   5. create_brief() 写入 _briefs/")
    print(f"   6. 更新 _state.json counters.briefs_total")
    return 0


if __name__ == "__main__":
    sys.exit(main())