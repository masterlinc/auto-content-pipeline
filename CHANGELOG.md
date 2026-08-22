# Changelog

## 1.0.0 — 2026-08-22

首版发布。

**功能**：
- 6 阶段流水线：scan → review → confirm → write → cover → publish
- 支持 7 个热点源（微博/小红书/知乎/twitter/BBC/Reuters/36氪）
- LLM 评分 + 7 天去重
- 飞书推送确认机制
- 风格锁定（document + cover）
- 包装现有 xiaohongshu_poster.py，集成发布链路
- 完全 agent-driven，不需要外部 LLM API
- 任意 agent 可通过 CLI / cron / sub-agent 三种方式调用

**Cron**：
- 每周日 20:00 跑 scan
- 每天 09:00 跑 review + 推飞书

**Vault**：
- 风格固化文件：`style-document.md` / `style-cover.md`
- 账号配置：`style-config.yaml`
- 源列表：`sources.json`
- 状态机：pending_review → awaiting_user → approved → awaiting_cover → awaiting_publish → published
