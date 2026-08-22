# Stage 1: ingest — 给 agent 的完整指令

## 你的任务

把"草稿"从各种来源收进来，标准化成 `_drafts/{draft_id}/source.md`。

## 步骤

### 1. 读 context

- `_config/style-config.yaml`（账号定位）
- `_drafts/` 目录（看看有没有正在跑的 draft）

### 2. 拿草稿

按以下优先级尝试：

| 来源 | 路径 | 优先级 |
|------|------|--------|
| 用户传入文件 | 命令行参数 | 1 |
| vault 草稿区 | `00-转型·一人事业/04-原创写作专区/草稿/*.md` | 2 |
| scan 子流程 | `07-选题与发布/_briefs/*.md`（v1 留下来的 brief） | 3 |
| 飞书消息 | 最近 24h 用户发来的草稿 | 4 |

### 3. 标准化

把任何来源的草稿转成统一格式：

```markdown
---
draft_id: <自动生成，格式 YYYY-MM-DD_slug>
ingested_at: 2026-08-22T16:30:00+08:00
source: <user_upload | vault_drafts | scan_legacy | feishu_inbox>
original_path: <原文件绝对路径>
word_count: <中文字符数>
status: ingest_done
---

（正文，markdown 格式，去 frontmatter 后纯文本）
```

### 4. 写入

写到 `_drafts/{draft_id}/source.md`。

### 5. 更新 state

`save_state(state)` + counters.drafts_total++。

## 失败处理

- 草稿文件读不到 → 报错退出，提示用户检查路径
- 草稿太短（< 200 字）→ 警告但不阻断，等用户决定
- 草稿格式无法解析 → 退回纯文本，提示用户

## 严禁

- ❌ 改写草稿内容（ingest 只搬运，不润色）
- ❌ 跳过 frontmatter（下游 stage 需要 status 字段）
- ❌ 同时跑多个 ingest（避免 race condition）
