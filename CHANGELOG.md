# Changelog

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