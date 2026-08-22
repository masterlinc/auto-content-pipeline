# Stage 2: review — 给 agent 的完整指令

## 你的任务

复核所有 `status=pending_review` 的 brief，挑 **top N（默认 3）** 给 linc 决策。

## 步骤

### 1. 读 context

- `_config/style-config.yaml`
- `_config/style-document.md`
- `_briefs/*.md` 里所有 `status=pending_review`

### 2. 二次评分

对每个 pending brief：
- web_search 关键词，**看 24h 内是否还有热度**
- 时效性已过的（原始事件已无新进展）：降到 ≤ 4
- 仍在升温的：原分 +0.5
- 已有新反转的：在 brief body 里加一节"最新动态"，分不变

### 3. 选 top N

按新评分排序，取前 N（默认 3）。

### 4. 推进状态

- 选中的：`update_status(brief_id, 'awaiting_user', score=new_score)`
- 没选中的：保持 `pending_review`（明天 review 还会再看）

### 5. 生成 daily-pick

写到 `_briefs/daily-pick-YYYY-MM-DD.md`：

```markdown
---
date: 2026-08-22
top_n: 3
total_pending: 8
---

# 今日选题（2026-08-22）

共扫到 8 个候选，挑了 3 个最热的。

## 1. 伊朗对以色列发动大规模导弹袭击（评分 9.2）
- ID: `2026-08-22_xxx`
- 来源: weibo-trending
- 摘要: 一句话
- 为什么: 时效性强 + 受众关心

## 2. ...
## 3. ...
```

### 6. 推送飞书

调 `message(action="send")` 给 linc，**模板见 `prompts/confirm-message.md`**。

### 7. 更新 state

`save_state(state)`。

## 失败处理

- 没有 pending brief：跳过推送，写 `E_REVIEW_EMPTY`，不打扰 linc
- 飞书推送失败：写到 `_briefs/daily-pick-xxx.md` 就行，linc 自己扫 vault

## 严禁

- ❌ 把所有 brief 都标 awaiting_user —— top N 是硬限制
- ❌ 推完不写 daily-pick —— vault 是 fallback
- ❌ 修改 brief body 内容 —— review 只动 score 和 status