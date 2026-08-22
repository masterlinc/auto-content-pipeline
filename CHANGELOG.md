# Changelog

## 2.0.0+2 — 2026-08-22

### dankoe 风格模板升级

- 互联网搜 AutoTweet / YouMind / Behance 的 Dan Koe 风格综合
- `templates/style-templates/dankoe.md`：
  - Part 1 视觉：配色 4 色 / 字体 3 套 / 5 排版模板 / 尺寸 4 平台
  - Part 2 写作：5 个核心模式（modern-monk / OPC specificity / identity-shift hook / 长线程 / 日常栈揭示）+ 3-beat 结构
  - Part 3 选模板逻辑：dankoe vs 极客 vs 网红 vs 公众号
  - 明确禁用项（emoji 大图、暖色、3D、木刻风等）
  - review 阶段加分项（identity-shift hook +0.5、philosophy+tactic 双层 +0.5）

- SKILL.md：风格模板区重排，dankoe 默认高亮（带 ⭐ 标记 + 来源说明）

## 2.0.0+1 — 2026-08-22

- 锁定 dankoe 风格为 illustrate 默认模板
- 新增 `templates/style-templates/dankoe.md`（2929 字节通用版）
- SKILL.md 加 dankoe 默认说明
- `prompts/illustrate.md` 加选模板逻辑

## 2.0.0 — 2026-08-22

**重大架构变更**：从"内容工厂"转"打磨工坊"。

### 变化

- **新 6 阶段**：ingest → review → modify → illustrate → store → publish（v1 是 scan → review → write → cover → publish）
- **风格模板体系**：新增 3 套风格模板（公众号 / 网红 / 极客），review 阶段按模板打分
- **多平台发布**：从单平台（小红书）扩到 5 平台（小红书 ✅ + 掘金/少数派/知乎 🚧 + 公众号 ⏸）
- **vault 目标目录**：从 `07-选题与发布/` 移到 `00-转型·一人事业/04-原创写作专区/价值文章/`
- **公众号接入方式**：明确**不走浏览器**，等 AppID/AppSecret 后走官方 API
- **状态机重构**：draft 状态改为 `pending → ingest_done → reviewed → modified → illustrated → stored → published`

### 删除

- v1 的 cron `acp-scan-weekly` / `acp-review-daily` 已 disable（v2 不需要定时 review，新架构是用户触发）
- v1 的 `_drafts/` 目录仍兼容作 scan 子流程存储

### 新增

- `templates/style-templates/` 目录（公众号/网红/极客 模板）
- 6 个新 prompt（ingest/modify/illustrate/store/publish + review 重写）
- 多平台 publish 配置（`config/default.yaml` 中 `publish.platforms`）
- `store.py`（vault 价值文章入库）

## 1.0.0 — 2026-08-22

首版发布。

- 6 阶段流水线：scan → review → confirm → write → cover → publish
- 支持 7 个热点源（微博/小红书/知乎/twitter/BBC/Reuters/36氪）
- LLM 评分 + 7 天去重
- 飞书推送确认机制
- 风格锁定（document + cover）
- 包装现有 xiaohongshu_poster.py
- SkillHub 上线名：`auto-flow`