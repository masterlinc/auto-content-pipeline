# 飞书云文档循环审核 — 通用 agent 契约

> 任何 agent 读这份文件就知道怎么处理"飞书云文档审阅循环"。
> 这是 v2.1 的核心，把 store → publish 中间塞一道人工审核。

## 完整流程

```
[5. store]      → 把文章搬进 vault 价值文章区
       ↓
[6. sync-feishu] → 推飞书云文档 + 发 IM 卡片
       ↓
[7a. feishu-review] → 拉飞书评论
       ↓
       分类:
         - 含 "确认发布"/"通过"/"approved" → pass
         - 含 "打回"/"重写"/"退回"     → reject
         - 其他                          → suggestion
       ↓
       pass  → status = feishu_review_passed → 跳到 stage 7 (publish)
       reject/suggestion → status = feishu_review_modifying → 进 loop
       ↓
[7b. modify]    → 改稿（修改意见来自飞书评论）
       ↓
[7c. re-sync]  → 重新推飞书云文档（update，不是 create）
       ↓
[7d. notify]   → 重新发 IM 卡片告诉审阅人"已按意见修改"
       ↓
       回到 [7a. feishu-review]
       ↓
       循环直到 pass
       ↓
[8. publish]   → 多平台分发
```

## 单次循环的具体步骤

### Step 1: 拉评论

读 frontmatter 里的 `feishu_doc_token` 和 `last_seen_comment_id`：

```bash
lark-cli drive +list-comments --doc-token <doc_token> --page-all
```

返回 `items[]`，每条：

```json
{
  "id": "comment_xxx",
  "text": "评论内容",
  "user": {"name": "linc", "id": "ou_xxx"},
  "created_time": "1700000000"
}
```

### Step 2: 过滤"新评论"

- 第一次跑：`last_seen_comment_id` 为空 → 所有评论都算新
- 之后：保留 `id > last_seen_comment_id` 的评论

### Step 3: 分类

```python
def classify(text):
    t = text.strip().lower()
    if any(kw in t for kw in ["确认发布", "通过", "approved", "approve", "ok 发布"]):
        return "pass"
    if any(kw in t for kw in ["打回", "重写", "退回", "reject", "不通过", "重新"]):
        return "reject"
    return "suggestion"
```

**判定规则**：

- 只要有 1 条新评论是 `pass` → verdict = pass
- 否则 → verdict = reject，**所有新评论**（除 pass）都进 suggestions 列表

### Step 4: 输出 JSON（agent 读这个去行动）

```json
{
  "draft_id": "draft-2026-08-22_xxx",
  "doc_token": "doccnXXX",
  "review_round": 2,
  "verdict": "pass | reject | empty | no_doc",
  "new_comments": [
    {"id": "c1", "author": "linc", "text": "...", "classification": "suggestion"}
  ],
  "suggestions": ["具体修改意见 1", "..."],
  "next_action": "ready_to_publish | modify_then_resync | wait_for_comments | run_sync_feishu_first"
}
```

### Step 5: 更新状态

| verdict | status | 后续 |
|---------|--------|------|
| pass | `feishu_review_passed` | 跑 stage 8 (publish) |
| reject | `feishu_review_modifying` | 改稿 + re-sync + 回到 step 1 |
| empty | 不变 | 等用户评论 |
| no_doc | 不变 | 先跑 sync-feishu |

写回 frontmatter：

- `last_seen_comment_id`: 最新评论 id
- `last_reviewed_at`: ISO timestamp
- `review_round`: +1
- `last_review_verdict`: pass | reject

### Step 6: 把建议交给 modify stage

```python
# 任何 agent 都可以跑：
python3 scripts/modify.py <draft_id> --from-feishu-review
# modify stage 读 frontmatter 里的 last_review_verdict 和 suggestions
# 把所有 suggestion 当成 modify 的输入（类似 review.json 的 suggestions 字段）
```

### Step 7: 改稿后重新同步

跑完 modify 之后，跑 `sync-feishu`：

- 检测到 `feishu_doc_token` 已存在 → 自动走 update 而不是 create
- 再发一条 IM 卡片告诉审阅人"已按意见修改，审核轮 N+1"

### Step 8: 回到 Step 1

agent 重新跑 `feishu-review`，等新评论。

## 触发"确认发布"后

当 verdict = pass：

1. status = `feishu_review_passed`
2. agent 跑 stage 8 (publish)：
   ```bash
   python3 scripts/pipeline.py publish <draft_id> --platforms xiaohongshu,juejin
   ```
3. publish 完成后 status = `published`

## 状态机全貌

```
ingest_done → reviewed → modified → illustrated → stored
   ↓
feishu_sync_pending → feishu_synced
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
failed (任意 stage 可失败)
```

## agent 实现提示

- 不需要长连接、cron 监听。**对话驱动**即可：
  - 用户说"pipeline 跑一下" → 跑 1-5 阶段
  - 跑 6 → 7a → 输出 JSON 给用户
  - 用户反馈（"按评论改稿"）→ 跑 7b → 7c → 7d
  - 循环
  - 用户说"确认发布" → 跑 8

- 也可以定时轮询：用 `lark-cli im +chat-messages-list` 看审阅人有没有在群里说"通过"或"打回"

## 错误处理

| 错误 | 怎么处理 |
|------|---------|
| 飞书评论为空 | verdict=empty，不更新 review_round |
| 飞书评论里"打回"和"通过"都有 | 按 pass 处理（保守原则，避免误发） |
| modify stage 失败 | 保留 status=feishu_review_modifying，下次重试 |
| sync-feishu 失败（网络/限流） | 重试 3 次，仍失败 → 提示用户手动操作 |
