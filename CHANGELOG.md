# Changelog

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
