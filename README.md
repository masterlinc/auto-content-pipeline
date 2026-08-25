# Auto Content Pipeline v3

把一篇 Obsidian Markdown 文章变成可直接人工发布的图文包。

**不需要 Codex、浏览器自动化、平台 Cookie 或定时任务。**

```
文章.md → 封面 + 2 张正文信息图 → 公众号 / 小红书 / 即刻文案 → 完整性检查
```

## 30 秒开始

```bash
git clone https://github.com/masterlinc/auto-content-pipeline.git
cd auto-content-pipeline
python3 -m pip install -r requirements.txt
python3 scripts/pipeline.py package /你的文章路径/文章.md
```

默认在 Obsidian 的 `04-原创写作专区/发布包/` 生成一个新目录。目录内有：

```
20260825-文章标题/
├── article.md          # 已插入正文图的 Obsidian 成稿
├── 微信公众号.md         # 公众号长文
├── 小红书.md            # 小红书图文文案和上传顺序
├── 即刻.md              # 即刻短文
├── media/
│   ├── cover.png        # 3:4 封面
│   ├── body-img-01.png
│   └── body-img-02.png
├── manifest.json        # 素材清单、尺寸与哈希
└── 使用说明.md
```

发布前检查一次：

```bash
python3 scripts/pipeline.py check "<发布包目录>"
```

显示“发布包完整”后，按 `使用说明.md` 手动上传即可。

## 它解决什么

- 你只写 Markdown；系统稳定生成一套有封面、有正文图、有平台文案的发布资产。
- 图片为本地生成的信息图，不依赖某个 Agent 是否“记得调用出图”。
- `manifest.json` 会校验图片是否被遗漏或改动，避免小红书草稿出现空图。
- 小红书、即刻默认是**手动发布包**，不承诺不稳定的平台浏览器自动化。

## 配置

如果你的 Vault 不在默认路径，新建 `config/user.yaml`：

```yaml
package:
  output_dir: /你的/Obsidian Vault/04-原创写作专区/发布包
```

macOS 会自动使用系统中文字体。其他系统若中文显示异常，可设置 `ACP_FONT_PATH=/字体文件路径` 后再运行。

## 可选：飞书审核

已有用户仍可使用旧的 `sync-feishu` 与 `feishu-review` 命令；它们是可选能力，不影响 v3 的一键发布包流程。

## 兼容与边界

- Python 3.9+，依赖仅为 Pillow。
- v3 只生成并校验发布资产；**不会替你公开发帖**。
- 旧版 `ingest/review/modify/store/publish` 命令保留兼容，但不构成 v3 主路径。

## 开发验证

```bash
python3 -m unittest tests/test_package.py
```
