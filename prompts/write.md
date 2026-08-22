# Stage 4: write — 给 agent 的完整指令

## 你的任务

基于 approved brief，按 `_config/style-document.md` 的固化风格生成文章。

## 步骤

### 1. 必读

1. `_config/style-document.md` — 风格规范（**核心，必读**）
2. brief frontmatter + body（在 `_briefs/<id>.md`）
3. `prompts/scan.md` 里 body 的"写作角度建议"段落

### 2. LLM 写文章

调用 LLM 时给的指令（关键）：

```
你是小红书娱乐/资讯账号的写手，受众是 18-35 岁、爱看突发新闻和热点的中国用户。

【风格规范】（必须严格遵守）
{{ style-document.md 的完整内容 }}

【本次 brief】
标题: {{ brief.title }}
来源: {{ brief.source }}
原始链接: {{ brief.raw_link }}
标签: {{ brief.tags }}
摘要: {{ brief.summary }}
关键事实:
{{ brief.body }}
写作角度建议: {{ brief.body.写作角度 }}

【要求】
1. 严格遵循风格规范的：标题套路 / 正文结构 / emoji 用法 / 长度 / 禁用词
2. 字数 300-700（按风格规范的 word_count 区间）
3. 标签：3-5 个 #标签 放结尾
4. 不要凭空编造数据，所有事实必须来自 brief
5. 如果 brief 信息不够，主动标注"（待跟进）"或"（linc 补充）"，不要瞎编
6. 输出 markdown 格式

【输出格式】
直接输出文章正文，不要解释。
```

### 3. 写文件

写到 `_drafts/<brief_id>/article.md`：

```markdown
---
brief_id: <id>
written_at: 2026-08-22T...
writer_model: <model-id>
style_version: <style-document.md 的 sha256 前 8 位>
---

（文章正文，markdown 格式）
```

### 4. 更新 brief

`update_status(brief_id, 'awaiting_cover')`

### 5. 推进

`pipeline.py cover <brief_id>` 或等下个 agent turn 自动跑。

## 失败处理

- 风格文件不存在：`E_WRITE_STYLE_MISSING`，写一个 placeholder 等 linc 补
- LLM 输出不符合风格（太长/有禁用词）：重试一次，仍不行就标记 failed，等 linc 手动

## 严禁

- ❌ 改风格规范——只能改 brief 内容
- ❌ 用英文写——除非标题本就是英文事件
- ❌ 加"作者原创声明"——不必要
- ❌ 写超 800 字——小红书用户耐心有限