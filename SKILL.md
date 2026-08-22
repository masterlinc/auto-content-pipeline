---
name: auto-content-pipeline
description: "内容打磨 + 多平台发布流水线（v3 with Codex Harness）：拿到草稿后用 OpenAI Codex Harness 作为 agent runtime，按公众号 / 网红 / 极客 / dankoe 四种风格模板 review → 自动 modify → 图文并茂 illustrate → 入库到 Obsidian 价值文章区 → 一键分发到小红书 / 掘金 / 少数派 / 知乎 / 公众号（API 待接入）。任意 OpenClaw agent 都可通过 CLI / cron / sub-agent 三种方式调用。"
metadata:
  {
    "openclaw":
      {
        "emoji": "⚡",
        "homepage": "skills/auto-content-pipeline/README.md",
        "user_invocable": true
      }
  }
---

# Auto Content Pipeline v3 — Codex Harness Edition

把"草稿 → 公众号/网红/极客/dankoe风爆款文 → 多平台分发"做成端到端自动化。v3 用 **OpenAI Codex Harness** 作 agent runtime，v2 的 6 stage 变成 Codex 的 sub-tasks。

> **v1 → v2 → v3 演进**：
> - v1：从零生产内容（scan → write → cover → publish）
> - v2：拿到草稿打磨（ingest → review → modify → illustrate → store → publish，6 个独立 Python 脚本）
> - **v3**：用 Codex Harness 当 runtime（同一个 6 stage，但每个 stage 调 Codex sub-agent）

## 架构（v3）

```
[Feishu] → [OpenClaw] → [Codex Harness] → [6 stages] → [5 平台]
                          │
                          ├─ memory (跨 session)
                          ├─ permission (publish/delete 前问 linc)
                          ├─ tool registry (image_generate / xiaohongshu_poster / ...)
                          └─ sub-agent 派发
```

详细架构看 `ARCHITECTURE.md`。

## 六阶段流水线

| Stage        | v2 (Python) | v3 (Codex sub-task) |
|--------------|-------------|---------------------|
| **ingest**   | `python3 ingest.py file.md` | `codex -p "读 X 写到 _drafts/{id}/"` |
| **review**   | `python3 review.py draft_id` | `codex -p "按 4 模板给 X 评分"` |
| **modify**   | `python3 modify.py draft_id` | `codex -p "按 review 改 X"` |
| **illustrate** | `python3 illustrate.py draft_id` | `codex -p "生成封面+正文图"` |
| **store**    | `python3 store.py draft_id` | `codex -p "复制到 vault 价值文章"` |
| **publish**  | `python3 publish.py draft_id --platforms` | `codex -p "发到小红书"` |

## 三种调用方式

### 1. CLI（v3 推荐）

```bash
# 装 Codex（首次）
npm install -g @openai/codex
codex --version  # 验证

# 跑一条龙
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py run-all <草稿.md>
# pipeline.py 会把每个 stage 包成 `codex -p "..."` 调 Codex

# 或直接给 Codex 大 prompt 让它自己跑
codex -p "按 $ACP/SKILL.md 跑一遍 auto-content-pipeline，把草稿 file.md 处理到 publish"
```

### 2. Cron（系统调度）

v3 默认**不挂定时**——Codex session 按需触发。

如果非要 cron，调 OpenClaw cron：
- `cron add --name acp-scan-daily --schedule "0 9 * * *" --session-target isolated --payload-kind agentTurn`
- message: `请用 Codex Harness 跑一遍 auto-content-pipeline v3`

### 3. Sub-agent（被其他 agent 调用）

```bash
codex -p "按 $ACP/SKILL.md 执行 stage: review。draft_id: X"
```

## 配置 / 状态文件

### Skill 端

```
skills/auto-content-pipeline/
├── ARCHITECTURE.md       ← v3 架构总览
├── SKILL.md               ← 本文件（v3）
├── README.md
├── CHANGELOG.md
├── VERSION                ← 3.0.0
├── config/
│   ├── default.yaml       ← 平台 + 路径 + 模板
│   └── codex.toml.example ← Codex 配置示例
├── prompts/               ← 每个 stage 的 prompt（v3 适配）
├── scripts/
│   ├── pipeline.py        ← CLI 入口（v3 调 Codex runner）
│   ├── codex_runner.py    ← Codex CLI 薄包装
│   ├── state.py / brief.py / store.py / publish.py  ← v2 兼容层
└── templates/style-templates/
    ├── dankoe.md          ⭐ 默认
    ├── 公众号.md / 网红.md / 极客.md
```

### Vault 端

```
~/Documents/Obsidian Vault/
├── 00-转型·一人事业/04-原创写作专区/
│   ├── 草稿/             ← ingest 来源
│   ├── 价值文章/         ← store 目标
│   └── _config/style-templates/  ← 4 风格模板（v3 同步）
└── 07-选题与发布/        ← v1 遗留，仍兼容
```

## Draft 状态机

```
pending → ingest_done → reviewed → modified → illustrated → stored → published
                                       ↓
                                   failed（任意 stage 可失败）
```

## 风格模板（review + illustrate 阶段必读）

`templates/style-templates/` 目录下放 4 份风格规范：

### ⭐ 默认模板：`dankoe.md`

**所有 illustrate 出图默认走这个**（除非 frontmatter 显式指定）。

基于公开研究的 Dan Koe 视觉 + 写作风格，分 3 部分：

| Part | 用途 | Stage |
|------|------|-------|
| **Part 1 视觉** | 配色/字体/排版/尺寸 | illustrate, cover |
| **Part 2 写作** | 5 个核心模式 + 3-beat 结构 + review 加成 | review, modify |
| **Part 3 选模板顺序** | dankoe vs 极客 vs 网红 vs 公众号 怎么选 | illustrate |

视觉要点：黑底白字 / 单色调（4 色）/ 大字占 60-80% / 大留白 / 一句一观点 / 16:9 横幅。
写作要点：哲学 + 实操双层 / identity-shift hook / 现代僧侣哲学框架 / 流程揭示。

### 其它 3 个模板（按需）

- `公众号.md` —— 长文 / 标题党 / 故事化开头 / 多段落 / 强 CTA
- `网红.md` —— 短句 / emoji 多 / 情绪化 / 个人化视角 / 一句话金句
- `极客.md` —— 技术准确 / 代码块 / 工具对比表 / 客观中立

### 选模板顺序（illustrate stage 默认）

1. **观点 / 强情绪 / 反常识** → **`dankoe.md`**（默认）
2. 教程 / 工具盘点 / 实操 → 极客.md
3. 种草 / 体验 / 个人故事 → 网红.md
4. 长文深度 / 案例分析 → 公众号.md

修改风格规范前必须跟 linc 确认 —— agent 不自动改。

## 发布平台（v3.0.0）

| 平台       | 状态                | 实现方式                |
|------------|---------------------|-------------------------|
| 小红书     | ✅ 可用              | xiaohongshu_poster.py   |
| 掘金       | 🚧 待配置 cookie    | juejin API              |
| 少数派     | 🚧 待配置           | sspai API               |
| 知乎       | 🚧 待配置           | zhihu API               |
| 公众号     | ⏸ 待接入 API        | **不走浏览器**，等 AppID/AppSecret |

## v1 → v2 → v3 迁移

| 版本 | 时间 | 变化 |
|------|------|------|
| v1 | 2026-08-22 上午 | scan → write → cover → publish 4 阶段（已弃用） |
| v2 | 2026-08-22 下午 | ingest → review → modify → illustrate → store → publish 6 阶段（独立脚本） |
| v3 | 2026-08-22 深夜 | 同 v2 6 阶段，但 agent runtime 换成 Codex Harness |

- v1 cron（`acp-scan-weekly` / `acp-review-daily`）已 disable
- v2 stage 脚本**保留可用**（v3 默认走 Codex，可降级到 v2）
- SkillHub 上 `auto-flow` 已升 v3