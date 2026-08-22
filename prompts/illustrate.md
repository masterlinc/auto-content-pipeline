# Stage 4: illustrate — 给 agent 的完整指令

## 你的任务

给 article.md 加封面 + 正文配图，输出图文并茂版。

## 步骤

### 1. 必读

- `_drafts/{draft_id}/article.md`（改稿后正文）
- `templates/style-templates/cover-default.md`（封面风格，可选）
- `config/default.yaml` 中 `illustrate.*`（封面规格 + 正文图数量 + 排版）

### 2. 生成封面

调 `image_generate`：

```python
image_generate(
    prompt=<封面 prompt>,
    aspectRatio="3:4",
    size="1242x1660",
    outputFormat="png",
    quality="high",
)
```

封面 prompt 由 LLM 基于 article.md 标题 + 风格生成。

写到 `_drafts/{draft_id}/cover.png`。

### 3. 生成正文配图

按 `illustrate.body_images.count`（默认 2-3 张）生成：

- 风格：`illustrate.body_images.style`（minimal-diagram | flat-illustration | screenshot）
- 排版：`illustrate.body_images.placement`（after_each_section | inline_with_text）

每张图单独 prompt，尺寸按文章宽度（建议 800x600）。

写到 `_drafts/{draft_id}/body-img-{1,2,3}.png`。

### 4. 把图插入文章

按 placement 规则在 article.md 中插入 `![](body-img-N.png)` 引用。

### 5. 写到 `_drafts/{draft_id}/article.md`（覆盖）

更新 frontmatter：
```yaml
illustrations:
  cover: cover.png
  body:
    - body-img-1.png
    - body-img-2.png
```

### 6. 更新 state

draft status → `illustrated`。

## 失败处理

- image_generate 报错 → 保留 article（无图），status 留在 `modified`，提示用户手动触发
- 单张图失败 → 重试 1 次，仍失败跳过该张
- 所有图失败 → 整个 stage 失败，article 仍可纯文字发布

## 严禁

- ❌ 用 AI 生成真实人脸（肖像权）
- ❌ 用品牌 logo / 商标
- ❌ 图片用大段文字（封面 6 字内，正文图不超 30 字）
- ❌ 黑白灰色调（饱和度低点击率差）
