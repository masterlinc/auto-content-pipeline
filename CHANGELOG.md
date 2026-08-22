# Changelog

## 2.1.0 — 2026-08-23

**飞书云文档审核循环**：store → publish 中间加一道人工审核墙。

### 新增

- **Stage 6: `sync-feishu`**（`scripts/feishu_sync.py`）
  - 把 vault 价值文章区里的 article.md 推到飞书云空间 `auto-content-pipeline/审核中/`
  - 通过飞书 IM 发卡片给审阅人
  - 走 `lark-cli`（不绑定任何 agent 工具）
  - 输出 doc_token / doc_url，写回 frontmatter

- **Stage 7: `feishu-review`**（`scripts/feishu_review.py`）
  - 拉飞书云文档评论（`lark-cli drive +list-comments`）
  - 按 `last_seen_comment_id` 过滤新评论
  - 分类：`pass`（含"确认发布"/"通过"） / `reject`（含"打回"/"重写"） / `suggestion`（其他）
  - 输出 JSON 给 agent：verdict / suggestions / next_action

- **Prompt 契约**：
  - `prompts/sync-feishu.md` — 任何 agent 怎么跑这个 stage
  - `prompts/review-loop.md` — 循环审核的状态机 + 步骤

- **状态机扩展**（`scripts/state.py`）：
  - 新增状态：`feishu_sync_pending` / `feishu_synced` / `feishu_review_pending` / `feishu_review_modifying` / `feishu_review_syncing` / `feishu_review_passed`
  - 新增 frontmatter 字段：`feishu_doc_token` / `feishu_doc_url` / `feishu_synced_at` / `review_round` / `last_seen_comment_id` / `last_reviewed_at` / `last_review_verdict`
  - 新增工具函数：`set_feishu_doc` / `bump_review_round` / `classify_feishu_comment`

- **配置段**（`config/default.yaml`）：
  - 新增 `feishu` 段：reviewer_chat_id / audit_folder / pass_keywords / reject_keywords

### 变更

- **`SKILL.md`**：7 阶段流程图 + 飞书审核循环契约 + 通用 agent 调用约定
- **`README.md`**：同步 v2.1 描述 + 文件地图
- **`pipeline.py`**：注册 `sync-feishu` / `feishu-review` 两个 stage
- **`state.py`**：状态机扩展

### 设计原则

- **不绑定任何 agent**——所有 stage 用 `lark-cli` + `python3` 实现
- **不绑定任何 harness**——v3 Codex Harness / v2 stage 脚本 / 对话驱动 都可触发
- **状态机驱动**——所有状态写在 frontmatter，任何 agent 都能解析
- **对话驱动循环**——loop 由 agent 根据 verdict 触发，不依赖长连接/cron

### 升级要点

```bash
# 1. 配 config/default.yaml
#    feishu.reviewer_chat_id: oc_xxxx
#
# 2. 确认 lark-cli 已认证
lark-cli auth status
#
# 3. 升级后跑法：
python3 pipeline.py sync-feishu <draft_id>      # 推飞书
python3 pipeline.py feishu-review <draft_id>     # 拉评论
# 输出 JSON → agent 按 verdict 决定 modify/publish
```

## 2.0.0 — 2026-08-23

**回退到 v2**（v3 Codex Harness 集成暂缓）。

### 变化

- **VERSION**：`3.0.0` → `2.0.0`（v3 的 codex_runner.py / ARCHITECTURE.md / codex.toml.example 仍保留，但默认不用）
- **pipeline.py**：默认走 v2 stage 脚本（Python 直接调）
- **v3 opt-in**：设 `ACP_USE_CODEX=1` 启用 Codex Harness
- **DRY_RUN**：仅 v3 生效

### v3 暂缓原因

- Codex 需要 OAuth（初次跑麻烦）
- Codex 第一次跑会真改文件，需要 permission 流程
- 用户暂时想"简单跑通即可"，v2 stage 脚本占位 + 状态机已经能展示完整流程

### v3 文件保留

不删 v3 资产（git 历史里有）：

- `ARCHITECTURE.md` — v3 设计文档（参考）
- `scripts/codex_runner.py` — Codex 薄包装（启用方式：`ACP_USE_CODEX=1`）
- `config/codex.toml.example` — Codex 配置示例

## 3.0.0 — 2026-08-22

**重大架构变更**：agent runtime 从 v2 独立脚本切换到 OpenAI Codex Harness。

### 新增

- `ARCHITECTURE.md` — v3 完整架构文档
- `scripts/codex_runner.py` — Codex CLI 薄包装
- `config/codex.toml.example` — Codex 配置示例

### 变化

- SKILL.md 改为 v3
- pipeline.py 默认调 Codex runner
- stage 脚本作为 fallback（codex 未装时）

## 2.0.0+3 — 2026-08-22

### dankoe 同步

- SKILL.md 风格模板区重排
- vault `_config/style-templates/dankoe.md` 同步

## 2.0.0+2 — 2026-08-22

### dankoe 风格模板升级

- 互联网搜 AutoTweet / YouMind / Behance 的 Dan Koe 风格
- Part 1 视觉 / Part 2 写作 / Part 3 选模板

## 2.0.0+1 — 2026-08-22

- 锁定 dankoe 风格为 illustrate 默认模板

## 2.0.0 — 2026-08-22（首发）

**架构**：从"内容工厂"转"打磨工坊"。

- 新 6 阶段：ingest → review → modify → illustrate → store → publish
- 4 风格模板（dankoe / 公众号 / 网红 / 极客）
- 5 发布平台（小红书 ✅ / 掘金-少数派-知乎 🚧 / 公众号 ⏸）
- vault 目标目录：`00-转型·一人事业/04-原创写作专区/价值文章/`

## 1.0.0 — 2026-08-22

首版发布。

- 6 阶段：scan → review → confirm → write → cover → publish
- 7 个热点源
- LLM 评分 + 7 天去重
- SkillHub 上线名：`auto-flow`