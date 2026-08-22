# Stage 5: store — 给 agent 的完整指令

## 你的任务

把打磨好的 draft 搬进 vault 价值文章区，作为"可发布"成品。

## 步骤

### 1. 必读

- `_drafts/{draft_id}/article.md`
- `_drafts/{draft_id}/cover.png`
- `_drafts/{draft_id}/body-img-*.png`
- `config/default.yaml` 中 `store.*`（覆盖策略、是否更新 _index）

### 2. 目标路径

```
{value_dir}/{draft_id}/
├── article.md       ← 改稿后正文
├── cover.png        ← 封面
├── body-img-1.png   ← 正文配图（如有）
├── body-img-2.png
├── review.json      ← 评分快照（用于回溯）
└── meta.json        ← 草稿元信息
```

`value_dir` 默认 = `~/Documents/Obsidian Vault/00-转型·一人事业/04-原创写作专区/价值文章/`

### 3. meta.json 格式

```json
{
  "draft_id": "<id>",
  "stored_at": "2026-08-22T17:00:00+08:00",
  "title": "从 GitHub 上 10 个 Agent 看 AI 管理转型",
  "primary_style": "jike",
  "review_score": 8.2,
  "word_count": 1850,
  "illustration_count": 3,
  "publish_status": "pending",
  "published_platforms": [],
  "vault_path": "00-转型·一人事业/04-原创写作专区/价值文章/<id>/"
}
```

### 4. 更新 _index.md

如果 `store.update_index=true`，在价值文章根目录维护一个 `_index.md`：

```markdown
# 价值文章索引

按时间倒序，最新的在最上面。

## 2026-08

- [从 GitHub 上 10 个 Agent 看 AI 管理转型](2026-08-22_xxx/article.md) — 极客风 — 评分 8.2 — 待发布
```

### 5. 更新 state

draft status → `stored`。

### 6. 返回 store 路径

返回完整 vault 路径，方便 publish stage 用。

## 失败处理

- 目标目录已存在同 id → 按 `store.overwrite` 决定（默认 false，提示用户）
- copy 失败 → 回滚已 copy 的文件

## 严禁

- ❌ 改 article.md 内容（store 只搬运）
- ❌ 删 _drafts/ 下的原文件（store 是双向冗余）
- ❌ 修改 meta.json 里的 review_score（必须诚实）
