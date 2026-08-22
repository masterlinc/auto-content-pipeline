# Stage 2: review — 给 agent 的完整指令

## 你的任务

按 **3 套风格模板**（公众号 / 网红 / 极客）给草稿打分，输出 review.json，含每维度得分 + 改稿建议。

## 步骤

### 1. 必读

- `_drafts/{draft_id}/source.md`（草稿原文）
- `templates/style-templates/公众号.md`、`网红.md`、`极客.md`（3 套风格规范）
- `config/default.yaml` 中 `review.weights`（3 套模板的权重）

### 2. 对每个风格维度打分

每套模板给 0-10 分：

| 维度 | 说明 |
|------|------|
| **标题** | 是否有冲击力、是否符合该风格标题套路 |
| **开头** | 前 3 句是否抓人 |
| **结构** | 段落/小标题是否清晰 |
| **节奏** | 长短句搭配、emoji 密度 |
| **CTA** | 结尾是否有行动号召 |
| **平台适配** | 整体调性是否符合目标平台用户 |

总分 = 加权和（公众号 0.4 / 网红 0.3 / 极客 0.3）。

### 3. 选最强风格

取总分最高的风格作为 `primary_style`，给后续 modify stage 用。

### 4. 输出改稿建议

按 `min_dim_score` 过滤（默认 6.0），低于阈值的维度生成具体改稿建议。每条建议格式：

```json
{
  "dimension": "标题",
  "current_score": 4.5,
  "suggestion": "标题偏长，公众号风格 28 字内最佳。当前 38 字，建议砍掉后半句。",
  "example_rewrite": "从伊朗 4 月出口数据看 2026 的供应链危机"
}
```

最多返回 `review.max_suggestions` 条（默认 10）。

### 5. 写到 `_drafts/{draft_id}/review.json`

```json
{
  "draft_id": "2026-08-22_xxx",
  "reviewed_at": "2026-08-22T16:35:00+08:00",
  "scores": {
    "gongzhonghao": { "title": 7, "opening": 6, "structure": 8, ... },
    "wanghong": { ... },
    "jike": { ... }
  },
  "weighted_total": 7.2,
  "primary_style": "gongzhonghao",
  "suggestions": [
    { "dimension": "标题", "current_score": 4.5, ... }
  ],
  "status": "reviewed"
}
```

### 6. 更新 state

brief status → `reviewed`，加 reviewed_at。

## 失败处理

- 模板文件缺失 → 报错退出，提示用户补 templates
- 草稿太短无法评分 → 给"信息不足，建议补内容"作为唯一建议

## 严禁

- ❌ 改写草稿（review 只打分和建议，不动手）
- ❌ 给所有维度都打高分（要诚实）
- ❌ 编造不存在的格式问题（基于模板原文判断）
