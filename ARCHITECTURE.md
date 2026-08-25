# v3 架构：少而确定

```
Markdown
  ↓ package
本地信息图生成（封面 + 2 图）
  ↓
图文成稿 + 三平台文案 + manifest
  ↓ check
人工上传发布
```

`package.py` 负责生成；`media.py` 负责图片；`manifest.json` 负责完整性校验。

没有长连接、定时器、Agent Harness 或浏览器自动化。平台侧变化不会破坏内容资产生成；最多只需要更新 `使用说明.md` 的人工上传步骤。
