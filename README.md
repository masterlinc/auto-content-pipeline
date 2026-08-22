# Auto Content Pipeline v2.1

内容打磨 + 飞书云文档审核 + 多平台发布流水线。

## 它做什么

```
拿草稿 → 按风格 review → 自动 modify → 图文并茂 → 入库
   ↓
推到飞书云文档 → 发 IM 卡片给审阅人
   ↓
拉飞书云文档评论 → 分类（pass / 打回）
   ↓
   打回 → 改稿 → 重新推飞书 → 重新拉评论（loop）
   ↓
   pass → 多平台发布
```

## v1 → v2 → v2.1

- v1：从零开始生产内容（scan → write → cover → publish）
- v2：拿到草稿后打磨发布（6 stage）
- **v2.1**：+ 飞书云文档审核循环（7 stage + 1 loop）

定位从"自媒体选题工厂"变成"公众号/网红/极客风的润色+飞书审核+分发工具"。

## 快速跑一遍

```bash
ACP=~/github/masterlinc/auto-content-pipeline

# 1. ingest（从 vault 草稿拿一份）
python3 $ACP/scripts/pipeline.py ingest ~/Documents/Obsidian\ Vault/00-转型·一人事业/04-原创写作专区/草稿/某文.md

# 2. 打磨一条龙
python3 $ACP/scripts/pipeline.py run-all <草稿.md>

# 3. 推到飞书云文档 + 发 IM 卡片
python3 $ACP/scripts/pipeline.py sync-feishu <draft_id>

# 4. 拉评论，分类，输出 JSON
python3 $ACP/scripts/pipeline.py feishu-review <draft_id>

# 5. 审核通过后多平台发布
python3 $ACP/scripts/pipeline.py publish <draft_id> --platforms xiaohongshu

# 单步调试
python3 $ACP/scripts/pipeline.py review <id>
python3 $ACP/scripts/pipeline.py modify <id>
python3 $ACP/scripts/pipeline.py illustrate <id>
python3 $ACP/scripts/pipeline.py store <id>
```

## 文件地图

```
auto-content-pipeline/
├── SKILL.md                ← agent 调用契约（v2.1）
├── README.md               ← 你读的快速说明
├── CHANGELOG.md            ← 版本变更
├── VERSION                 ← 2.1.0
├── config/default.yaml     ← 全局配置（feishu 段 v2.1 新增）
├── prompts/                ← 8 个 stage prompt
│   ├── ingest.md / review.md / modify.md / illustrate.md / store.md
│   ├── sync-feishu.md      ⭐ v2.1 新增
│   ├── review-loop.md      ⭐ v2.1 新增（循环审核契约）
│   └── publish.md
├── scripts/                ← 11 个脚本
│   ├── pipeline.py         ← CLI 入口
│   ├── feishu_sync.py      ⭐ v2.1 新增
│   ├── feishu_review.py    ⭐ v2.1 新增
│   ├── codex_runner.py     ← v3 Codex Harness
│   └── ingest.py / review.py / modify.py / illustrate.py / store.py / publish.py / state.py
├── templates/style-templates/  ← 公众号/网红/极客/Dankoe 模板
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
请按 ~/github/masterlinc/auto-content-pipeline/SKILL.md 执行 stage: <ingest|review|modify|illustrate|store|sync-feishu|feishu-review|publish>。
draft_id: 2026-08-22_xxx
```

子 agent 读 SKILL.md 自己就知道怎么干。**不绑定特定 agent**——Mavis / Codex / Claude Code / Cursor / 任何 CLI LLM agent 都可以跑。

## v2.1 新增：飞书云文档审核循环

- 任何 agent 调 `python3 scripts/feishu_sync.py <draft_id>` 推飞书
- 审阅人评论后，调 `python3 scripts/feishu_review.py <draft_id>` 拉评论
- 输出 JSON 给 agent，agent 按 verdict 决定下一步
- pass → 跑 publish；reject → 跑 modify → sync-feishu（loop）

详见 `SKILL.md` 和 `prompts/review-loop.md`。
