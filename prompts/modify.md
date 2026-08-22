# Stage 3: modify — 给 agent 的完整指令

## 你的任务

按 review.json 的建议自动改稿，输出 `_drafts/{draft_id}/article.md`。

## 步骤

### 1. 必读

- `_drafts/{draft_id}/source.md`（原稿）
- `_drafts/{draft_id}/review.json`（评分 + 建议）
- `config/default.yaml` 中 `modify.*`（允许重写、保留原稿、阈值）

### 2. 应用改稿建议

按 review.json 的 `suggestions` 逐条应用：

- **小改**（替换词/调语序）→ 直接改
- **中改**（重写段落）→ 整段替换
- **大改**（超过 `rewrite_threshold` 比例）→ 标记为"重写"段，提示用户

### 3. 风格锁定

根据 `review.primary_style` 套对应模板的写法：
- primary_style=gongzhonghao → 套公众号.md 的标题/开头/CTA 套路
- primary_style=wanghong → 套网红.md 的短句/emoji/金句
- primary_style=jike → 套极客.md 的技术准确/对比表/客观中立

### 4. 保留原稿

如果 `modify.keep_original=true`，把原稿备份到 `_drafts/{draft_id}/source.md.bak`。

### 5. 写到 `_drafts/{draft_id}/article.md`

```markdown
---
draft_id: <id>
modified_at: 2026-08-22T16:40:00+08:00
based_on_review: <review.json path>
applied_suggestions: 7
rewrite_segments: 2
primary_style: gongzhonghao
status: modified
---

（改稿后的正文，markdown）
```

### 6. 更新 state

draft status → `modified`。

## 失败处理

- 建议之间冲突 → 优先级：标题 > 开头 > 结构 > 节奏 > CTA > 平台适配
- 改完后字数 < 300 → 警告但不阻断
- 改完后字数 > 1000 → 警告但不阻断

## 严禁

- ❌ 删原稿（即使 keep_original=false，也要给 .bak）
- ❌ 凭空加事实（review 没提的不能编）
- ❌ 改 frontmatter 中的 status 字段（其它字段如 title/tags 可改）
- ❌ 跨多稿融合（modify 只改一份）
