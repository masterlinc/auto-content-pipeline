---
name: auto-content-pipeline
description: "把 Obsidian Markdown 文章生成可校验的图文发布包：封面、两张正文信息图，以及公众号、小红书、即刻三份手动发布文案。"
metadata:
  {"openclaw":{"emoji":"📝","homepage":"skills/auto-content-pipeline/README.md","user_invocable":true}}
---

# Auto Content Pipeline v3

默认只做一件事：把一篇 Markdown 文章变成可人工发布的图文包。

```bash
python3 scripts/pipeline.py package <文章.md>
python3 scripts/pipeline.py check <发布包目录>
```

## 输出契约

- 必有 `media/cover.png`、`media/body-img-01.png`、`media/body-img-02.png`。
- 必有 `article.md`、`微信公众号.md`、`小红书.md`、`即刻.md` 与 `manifest.json`。
- `check` 必须通过，才可向用户报告“可发布”。
- 所有平台为手动发布准备；不得声称已公开发布。

## 边界

- 不调用 Codex Harness，不依赖浏览器控制，不保存平台 Cookie。
- 不改原始文章；只在发布包中写入图文版。
- 如用户要求飞书审核，可显式调用遗留 `sync-feishu`；它不是默认步骤。
