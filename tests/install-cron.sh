#!/usr/bin/env bash
# 安装 auto-content-pipeline 的 cron jobs
# 用法：bash tests/install-cron.sh
#
# 安装：
#   - 周日 20:00 跑 scan
#   - 每天 09:00 跑 review（推飞书）
#
# 也可以直接看 SKILL.md 用 openclaw cron add 安装（更推荐，
# 因为可以接 OpenClaw 的 delivery 到飞书）。

set -e

ACP=/Users/masterlinc/.openclaw/workspace/skills/auto-content-pipeline

echo "=== 安装 auto-content-pipeline cron ==="
echo ""

echo "方式 1（推荐）：通过 OpenClaw cron 管理（接飞书）"
echo "  请人工执行："
echo "  openclaw cron add --name 'acp-scan-weekly' \\"
echo "    --schedule 'cron:0 20 * * 0' --tz Asia/Shanghai \\"
echo "    --session-target main --payload-kind agentTurn \\"
echo "    --message '请按 $ACP/SKILL.md 执行 stage: scan。完成后只回报抓到的 brief 数量和错误，不推送。'"
echo ""
echo "  openclaw cron add --name 'acp-review-daily' \\"
echo "    --schedule 'cron:0 9 * * *' --tz Asia/Shanghai \\"
echo "    --session-target main --payload-kind agentTurn \\"
echo "    --delivery 'announce' --channel feishu --to linc \\"
echo "    --message '请按 $ACP/SKILL.md 执行 stage: review。完成后用 message 推飞书给 linc。'"
echo ""

echo "方式 2（本脚本安装到系统 crontab）"
read -p "用系统 crontab 吗？(y/N) " use_system_cron
if [[ "$use_system_cron" == "y" ]]; then
    CRON_LINE="0 20 * * 0 /usr/bin/python3 $ACP/scripts/pipeline.py scan >> /tmp/acp-scan.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "acp-scan"; echo "$CRON_LINE") | crontab -

    CRON_LINE2="0 9 * * * /usr/bin/python3 $ACP/scripts/pipeline.py review >> /tmp/acp-review.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "acp-review"; echo "$CRON_LINE2") | crontab -

    echo "✅ 已加到 crontab："
    crontab -l | grep acp-
fi

echo ""
echo "=== 完成 ==="
echo ""
echo "建议先用 '手动跑一遍' 验证："
echo "  python3 $ACP/scripts/pipeline.py status  # 看 vault 现状"
echo "  python3 $ACP/scripts/pipeline.py scan    # 手动跑 scan"
echo "  python3 $ACP/scripts/pipeline.py review  # 手动跑 review"