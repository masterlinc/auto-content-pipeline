# Stage 5: cover — 给 agent 的完整指令

## 你的任务

基于写好的文章，生成小红书风格的封面图。

## 步骤

### 1. 必读

1. `_config/style-cover.md` — 封面风格规范（**必读**）
2. `_drafts/<brief_id>/article.md` — 文章内容

### 2. 设计封面 prompt

调 LLM，基于文章标题 + 风格规范，生成 image prompt：

```
你是小红书封面设计师。基于以下信息设计一个封面：

【风格规范】
{{ style-cover.md 完整内容 }}

【文章】
标题: {{ article.title }}
正文前 200 字: {{ article.body[:200] }}
标签: {{ article.tags }}

【输出 prompt 要求】
1. 视觉构图描述（背景、前景、元素位置）
2. 文字层级（主标题、副标题、装饰文字），用占位符 [主标题] 标出文字位置
3. 配色（具体到色号或近似描述）
4. 风格关键词（如：扁平插画 / 3D 渲染 / 极简 / 故障风）
5. emoji 用法（小红书流行：✨🔥💥⚡🎯📍 等）
6. 情绪调性（紧张 / 温暖 / 震撼 / 治愈）
7. 比例 3:4（1242×1660）

【直接输出 prompt 字符串】
不要解释，不要 markdown 包裹。
```

### 3. 生成封面

调 `image_generate` 工具：

```python
image_generate(
    prompt=<上一步生成的 prompt>,
    aspectRatio="3:4",
    size="1242x1660",
    outputFormat="png",
    quality="high",
)
```

### 4. 保存

- 图片 → `_drafts/<brief_id>/cover.png`
- prompt 文本 → `_drafts/<brief_id>/cover-prompt.md`（**linc 之后想重画可以参考**）

### 5. 更新 brief

`update_status(brief_id, 'awaiting_publish')`

### 6. 推进

`pipeline.py publish <brief_id>`

## 失败处理

- image_generate 报错：保留 article，重试一次；仍失败 → `E_COVER_GEN_FAIL`，brief status 回 `awaiting_cover`
- 文件保存失败：先存到 `/tmp/`，下一轮重试

## 严禁

- ❌ 在封面里放真实人脸——肖像权风险
- ❌ 用小众字体（中文 web font 不稳定）
- ❌ 在 prompt 里写"@xxx"——会触发品牌审核
- ❌ 黑白灰色调——小红书封面色彩饱和度要高