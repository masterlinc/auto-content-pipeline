---
name: auto-content-pipeline
description: "内容打磨 + 飞书云文档审核 + 多平台发布流水线（v2.1）：拿到草稿后按公众号 / 网红 / 极客 / dankoe 四种风格模板 review → 自动 modify → 图文并茂 illustrate → 入库到 Obsidian 价值文章区 → **同步到飞书云文档供审阅**（v2.1 新增）→ **拉飞书云文档评论循环改稿**（v2.1 新增）→ 通过审核后一键分发到小红书 / 掘金 / 少数派 / 知乎 / 公众号（API 待接入）。任意 OpenClaw agent 都可通过 CLI / sub-agent / 对话驱动三种方式调用。v3 Codex Harness 集成作为可选项（ACP_USE_CODEX=1）。"
metadata:
  {
    "openclaw":
      {
        "emoji": "✨",
        "homepage": "skills/auto-content-pipeline/README.md",
        "user_invocable": true
      }
  }
---

# Auto Content Pipeline v2.1 — 打磨工坊 + 飞书云文档审核

把"草稿 → 公众号/网红/极客/dankoe 风爆款文 → **飞书云文档审核** → 多平台分发"做成端到端自动化。**任意 agent 都可以调用**——不绑定特定 agent 实现。

> **版本说明**：当前活跃版本是 **v2.1**。v3（OpenAI Codex Harness 集成）的代码保留在树里，通过 `ACP_USE_CODEX=1` 启用。v2.1 新增飞书云文档审核循环（sync-feishu + feishu-review 两个 stage）。

## 7 阶段流水线（含审核循环）

```
[ingest] → [review] → [modify] → [illustrate] → [store]
  拿草稿     风格评审     自动润色     图文并茂      入库
                                                 ↓
                              ┌──→ [sync-feishu]    推飞书云文档 + 发 IM 卡片
                              │         ↓
                              │  [feishu-review] 拉评论，分类
                              │         ↓
                              │  分类: pass → 跳到 publish
                              │         ↓ reject
                              │  [modify]   按评论改稿
                              │         ↓
                              │  [sync-feishu] 重新推飞书（update 不是 create）
                              │         ↓
                              │  [feishu-review] 重新拉评论
                              │         ↓
                              └──┘ loop until pass
                                                 ↓
                                              [publish] 多平台分发
```

| Stage        | 做什么                                              | 输入                          | 输出                                              | Prompt |
|--------------|-----------------------------------------------------|-------------------------------|---------------------------------------------------|--------|
| **ingest**   | 拿草稿                                              | vault 草稿 / 手动 / scan 子流程 | `_drafts/{id}/source.md`                          | `prompts/ingest.md` |
| **review**   | 按 dankoe/公众号/网红/极客 4 套风格模板打分 | source + 4 个模板             | `review.json`（每维度得分 + 改稿建议）           | `prompts/review.md` |
| **modify**   | 自动按 review 结果改稿                              | source + review.json          | `_drafts/{id}/article.md`                         | `prompts/modify.md` |
| **illustrate** | 配图（封面 + 正文 2-3 张）                        | article.md                    | cover.png + body-img-{n}.png                      | `prompts/illustrate.md` |
| **store**    | 入库到 Obsidian 价值文章区                          | 全部 draft 产物               | vault `04-原创写作专区/价值文章/{id}/`            | `prompts/store.md` |
| **sync-feishu** ⭐ | 推到飞书云文档 + 发 IM 卡片给审阅人       | store 后的 article.md         | 飞书 doc_token + IM 消息                          | `prompts/sync-feishu.md` |
| **feishu-review** ⭐ | 拉飞书云文档评论，分类 + 更新 status | doc_token                     | JSON: verdict / suggestions / next_action         | `prompts/review-loop.md` |
| **publish**  | 多平台分发                                          | store 后的成品                | 小红书 + 掘金 + 少数派 + 知乎（公众号待接入 API） | `prompts/publish.md` |

## 三种调用方式

### 1. CLI（默认走 v2.1）

```bash
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py ingest       <草稿路径>
python3 $ACP/scripts/pipeline.py review      <draft_id>
python3 $ACP/scripts/pipeline.py modify      <draft_id>
python3 $ACP/scripts/pipeline.py illustrate  <draft_id>
python3 $ACP/scripts/pipeline.py store       <draft_id>
python3 $ACP/scripts/pipeline.py sync-feishu <draft_id>     # v2.1 新增
python3 $ACP/scripts/pipeline.py feishu-review <draft_id>   # v2.1 新增
python3 $ACP/scripts/pipeline.py publish     <draft_id> --platforms xiaohongshu,juejin
python3 $ACP/scripts/pipeline.py run-all     <草稿>
python3 $ACP/scripts/pipeline.py status
```

### 2. CLI（v3 Codex Harness 模式）

```bash
# 装 Codex CLI（一次性）
npm install -g @openai/codex

# 启用 v3
ACP_USE_CODEX=1 python3 $ACP/scripts/pipeline.py review <draft_id>
ACP_DRY_RUN=1 ACP_USE_CODEX=1 python3 $ACP/scripts/pipeline.py review <draft_id>  # 只打印 prompt
```

### 3. Sub-agent（被其他 agent 调用 — **推荐方式**）

**任意 agent**（Mavis / Codex / Claude Code / Cursor / 任何 CLI LLM agent）都可以这样调：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: <ingest|review|modify|illustrate|store|sync-feishu|feishu-review|publish>。
draft_id: <id>
```

子 agent 读 SKILL.md → 知道 stage 是什么 → 读 `prompts/<stage>.md` → 自己决定怎么实现。

不绑定任何 agent 的工具——所有 stage 都用 `lark-cli` + `python3` 实现，任何 agent 都能跑。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `ACP_USE_CODEX` | `0`（v2） | `1` 走 v3 Codex Harness |
| `ACP_DRY_RUN` | `0` | `1` 让 Codex 只打印 prompt 不真跑 |
| `ACP_USE_V2` | `1`（v2） | 冗余写明，强制 v2 |

## 配置 / 状态文件

### Skill 端

```
skills/auto-content-pipeline/
├── ARCHITECTURE.md       ← v3 设计文档（参考）
├── SKILL.md               ← 本文件（v2）
├── README.md
├── CHANGELOG.md
├── VERSION                ← 2.0.0
├── config/
│   ├── default.yaml       ← 平台 + 路径 + 模板
│   └── codex.toml.example ← v3 Codex 配置示例
├── prompts/               ← 每个 stage 的 prompt
├── scripts/
│   ├── pipeline.py        ← CLI 入口（v2/v3 双轨）
│   ├── codex_runner.py    ← v3 Codex 薄包装
│   └── state.py / brief.py / ingest.py / review.py / modify.py / illustrate.py / store.py / publish.py
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
│   └── _config/style-templates/  ← 4 风格模板
└── 07-选题与发布/        ← v1 遗留，仍兼容
```

## Draft 状态机（v2.1 含飞书审核循环）

```
ingest_done → reviewed → modified → illustrated → stored
                                                ↓
                                   feishu_sync_pending
                                                ↓
                                   feishu_synced
                                                ↓
                                   feishu_review_pending
                                                ↓ (有评论)
                                   feishu_review_modifying
                                                ↓
                                   feishu_review_syncing
                                                ↓
                                   feishu_review_pending  ← loop
                                                ↓ (pass)
                                   feishu_review_passed
                                                ↓
                                   publish_pending → published
                                       ↓
                                   failed（任意 stage 可失败）
```

**关键约定**：
- 任何 stage 写 status 到 `_drafts/{draft_id}/source.md` 的 frontmatter
- 飞书相关字段：`feishu_doc_token` / `feishu_doc_url` / `review_round` / `last_seen_comment_id`
- 飞书评论拉取用 `lark-cli drive +list-comments`，不依赖 SDK
- 评论分类逻辑在 `scripts/state.py::classify_feishu_comment()`，agent 可以复用

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

## 发布平台（v2.0.0）

| 平台       | 状态                | 实现方式                |
|------------|---------------------|-------------------------|
| 小红书     | ✅ 可用              | xiaohongshu_poster.py   |
| 掘金       | 🚧 待配置 cookie    | juejin API              |
| 少数派     | 🚧 待配置           | sspai API               |
| 知乎       | 🚧 待配置           | zhihu API               |
| 公众号     | ⏸ 待接入 API        | **不走浏览器**，等 AppID/AppSecret |

## v1 → v2 → v2.1 → v3 迁移

| 版本 | 时间 | 状态 |
|------|------|------|
| v1 | 2026-08-22 上午 | 已弃用（scan → write → cover → publish） |
| v2 | 2026-08-22 下午 | 6 stage 独立 Python 脚本 |
| **v2.1** | **2026-08-23** | **当前默认**（+ sync-feishu + feishu-review 两个 stage，飞书云文档审核循环） |
| v3 | 2026-08-22 深夜 | 暂缓（Codex Harness 集成，文件保留在树里，ACP_USE_CODEX=1 启用） |

- v1 cron（`acp-scan-weekly` / `acp-review-daily`）已 disable
- v2 stage 脚本**保留可用**
- v2.1 新增：`scripts/feishu_sync.py` / `scripts/feishu_review.py` / `prompts/sync-feishu.md` / `prompts/review-loop.md`
- v3 文件保留：codex_runner.py / ARCHITECTURE.md / codex.toml.example

## v2.1 飞书云文档审核配置

在 `config/default.yaml` 里配 `feishu` 段：

```yaml
feishu:
  reviewer_chat_id: "oc_xxxx"           # 必填，审阅人飞书 chat_id
  reviewer_user_open_id: ""             # 备选，自动解析成 chat_id
  audit_folder: "auto-content-pipeline/审核中"
  title_prefix: "📝 审阅:"
  dry_run: false
  pass_keywords: [确认发布, 通过, approved, ...]
  reject_keywords: [打回, 重写, 退回, ...]
```

**前置**：
- `lark-cli auth status` 返回 user identity: ready
- 飞书云空间根目录有写权限
- 审阅人 chat_id 拿到（p2p 个人聊天 或 群聊）