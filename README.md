# Auto Content Pipeline v2

内容打磨 + 多平台发布流水线。

## 它做什么

```
拿草稿 → 按公众号/网红/极客风格 review → 自动 modify → 图文并茂 → 入库 → 多平台发布
```

## v1 → v2

- v1：从零开始生产内容（scan → write → cover → publish）
- **v2：拿到草稿后打磨发布**（ingest → review → modify → illustrate → store → publish）

定位从"自媒体选题工厂"变成"公众号/网红/极客风的润色+分发工具"。

## 快速跑一遍

```bash
ACP=~/.openclaw/workspace/skills/auto-content-pipeline

# 1. ingest（从 vault 草稿拿一份）
python3 $ACP/scripts/pipeline.py ingest ~/Documents/Obsidian\ Vault/00-转型·一人事业/04-原创写作专区/草稿/某文.md

# 2. 一条龙
python3 $ACP/scripts/pipeline.py run-all <上一步返回的 draft_id>

# 3. 单步调试
python3 $ACP/scripts/pipeline.py review <id>
python3 $ACP/scripts/pipeline.py modify <id>
python3 $ACP/scripts/pipeline.py illustrate <id>
python3 $ACP/scripts/pipeline.py store <id>
python3 $ACP/scripts/pipeline.py publish <id> --platforms xiaohongshu,juejin
```

## 文件地图

```
skills/auto-content-pipeline/
├── SKILL.md                ← agent 调用契约
├── README.md               ← 你读的快速说明
├── CHANGELOG.md            ← 版本变更
├── VERSION                 ← 2.0.0
├── config/default.yaml     ← 全局配置
├── prompts/                ← 6 个 stage prompt
├── scripts/                ← 9 个脚本
├── templates/style-templates/  ← 公众号/网红/极客 模板
└── tests/install-cron.sh
```

## 发布平台

| 平台 | 状态 |
|------|------|
| 小红书 | ✅ 可用 |
| 掘金 | 🚧 待配置 |
| 少数派 | 🚧 待配置 |
| 知乎 | 🚧 待配置 |
| 公众号 | ⏸ 待接入 API（不走浏览器） |

## 给其他 agent 怎么调

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: review。
draft_id: 2026-08-22_xxx
```

子 agent 读 SKILL.md 自己就知道怎么干。
