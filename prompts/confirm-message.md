# 给 linc 的推送模板

每天 09:00 review 后通过飞书推的消息。

## 模板（agent 直接套）

```
📰 今日选题 {{ DATE }}

共扫 {{ TOTAL }} 个候选，挑了 {{ TOP_N }} 个最热的。回复编号确认，或说"全拒" / "改：xxx"。

{{ LOOP_START }}
{{ INDEX }}. ⭐{{ SCORE }} {{ TITLE }}
   {{ ONE_LINE_SUMMARY }}
   标签：#{{ TAGS }}
   链接：brief id `{{ BRIEF_ID }}`

{{ LOOP_END }}

操作：
• 选：回复 `选 #1` / `选 #2 #3`（多个）
• 全拒：回复 `拒`
• 改：回复 `改 #{{ INDEX }}：新标题`
• 详细：点 vault 里的 `_briefs/daily-pick-{{ DATE }}.md`
```

## 示例

```
📰 今日选题 2026-08-22

共扫 8 个候选，挑了 3 个最热的。回复编号确认，或说"全拒" / "改：xxx"。

1. ⭐9.2 伊朗对以色列发动大规模导弹袭击
   美国和以色列联合袭击伊朗核设施，伊朗宣称报复。已确认 3 名美军阵亡。
   标签：#伊朗 #中东 #国际新闻
   链接：brief id `2026-08-22_iran-israel-strikes`

2. ⭐8.5 北上广深房租集体上涨
   一线城市 7 月房租同比涨 8%，多个新一线跟进。
   标签：#房租 #房价 #民生
   链接：brief id `2026-08-22_rent-rise-tier1`

3. ⭐7.8 鸿蒙 PC 版正式开放下载
   华为发布首款桌面级鸿蒙系统，支持 x86 模拟。
   标签：#鸿蒙 #华为 #国产系统
   链接：brief id `2026-08-22_harmonyos-pc-launch`

操作：
• 选：回复 `选 #1` / `选 #2 #3`（多个）
• 全拒：回复 `拒`
• 改：回复 `改 #1：新标题`
• 详细：点 vault 里的 `_briefs/daily-pick-2026-08-22.md`
```

## agent 收到 linc 回复后的处理

- `选 #1` → 调 `confirm.py approved 2026-08-22_iran-israel-strikes`，触发 write → cover → publish 链
- `选 #2 #3` → 对两个 brief 都调 approved
- `拒` → 调 `confirm.py rejected <id>`（**全拒** = 对所有 awaiting_user 都调 rejected）
- `改 #1：xxx` → 调 `confirm.py modified 2026-08-22_xxx xxx`，brief status 改 awaiting_user 等再确认

## 备注

- 推送时间窗口：09:00-09:30（cron 卡了）
- 周末可放宽到 10:00
- 深夜 22:00 后不推