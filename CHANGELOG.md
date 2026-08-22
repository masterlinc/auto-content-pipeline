# Changelog

## 3.0.0 — 2026-08-22

**重大架构变更**：agent runtime 从 v2 独立脚本切换到 **OpenAI Codex Harness**。

### 新增

- **`ARCHITECTURE.md`** — v3 完整架构文档
- **`scripts/codex_runner.py`** — Codex CLI 薄包装（v3 入口）
  - `review` / `modify` / `illustrate` / `store` / `publish` 5 个 stage
  - `--dry-run` 模式只打印 prompt 不真跑
  - 检测到 codex 没装会自动报错并给安装指引
  - 失败自动降级到 v2 stage 脚本

### 变化

- **SKILL.md**：v3 = v2 stages + Codex Harness 当 runtime
  - 每个 stage 改为 Codex sub-task 风格
  - 加了「为什么用 Codex」对照表
  - 加了「给 linc 的迁移清单」
- **prompts/*.md**：保留作为 fallback（Codex 不可用时用）
- **scripts/pipeline.py**：仍可独立跑 v2 stage（v3 双轨）
- **README.md / VERSION**：同步 v3

### v3 的优势（vs v2）

| 维度 | v2 | v3 (Codex) |
|------|-----|-----------|
| 跨 session 记忆 | 手动读 _state.json | Codex 内置 memory |
| 工具调用 | 脚本手写 | Codex tool registry |
| 权限管理 | 自己写 if-else | Codex permission system |
| 任务拆解 | stage 之间手动传 | Codex sub-agent 派发 |
| Session log | 自己写 | Codex 自动 |

### 风险

- Codex 是 Rust 写的（npm 包可绕过）
- Codex OAuth 偶尔失败（用 API key 兜底）
- Codex sub-agent 比 v2 慢（5 分钟 stage 超时）

## 2.0.0+3 — 2026-08-22

### dankoe 同步

- SKILL.md：风格模板区重排，dankoe 默认高亮（⭐ + Part 1/2/3 + 来源）
- CHANGELOG.md：记录 v2.0.0+2 升级（研究版 dankoe）+ v2.0.0+3（同步）
- 同步到 vault `_config/style-templates/dankoe.md` + staging

## 2.0.0+2 — 2026-08-22

### dankoe 风格模板升级

- 互联网搜 AutoTweet / YouMind / Behance 的 Dan Koe 风格综合
- `templates/style-templates/dankoe.md`：
  - Part 1 视觉：配色 4 色 / 字体 3 套 / 5 排版模板 / 尺寸 4 平台
  - Part 2 写作：5 个核心模式 + 3-beat 结构
  - Part 3 选模板逻辑
  - 明确禁用项

## 2.0.0+1 — 2026-08-22

- 锁定 dankoe 风格为 illustrate 默认模板

## 2.0.0 — 2026-08-22

**重大架构变更**：从"内容工厂"转"打磨工坊"。

### 变化

- **新 6 阶段**：ingest → review → modify → illustrate → store → publish
- **风格模板体系**：4 套风格（dankoe / 公众号 / 网红 / 极客）
- **多平台发布**：5 平台（小红书 ✅ / 掘金-少数派-知乎 🚧 / 公众号 ⏸）
- **vault 目标目录**：`00-转型·一人事业/04-原创写作专区/价值文章/`
- **公众号接入**：明确**不走浏览器**，等 AppID/AppSecret

## 1.0.0 — 2026-08-22

首版发布。

- 6 阶段流水线：scan → review → confirm → write → cover → publish
- 7 个热点源
- LLM 评分 + 7 天去重
- SkillHub 上线名：`auto-flow`