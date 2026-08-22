# Auto Content Pipeline v2 — 30 秒上手

把这套 skill 装到你自己的 OpenClaw 工作区，30 秒跑起来。

## 1. 安装 skill

```bash
# A. SkillHub（推荐）
openclaw skills install auto-pipe

# B. GitHub clone
git clone https://github.com/masterlinc/auto-content-pipeline.git \
  ~/.openclaw/workspace/skills/auto-content-pipeline

# C. 直接拷贝
cp -r /path/to/auto-content-pipeline ~/.openclaw/workspace/skills/
```

## 2. 初始化 vault（3 个目录）

```bash
VAULT=~/Documents/Obsidian\ Vault

mkdir -p "$VAULT/00-转型·一人事业/04-原创写作专区/草稿"
mkdir -p "$VAULT/00-转型·一人事业/04-原创写作专区/价值文章"
mkdir -p "$VAULT/00-转型·一人事业/04-原创写作专区/价值文章/_config/style-templates"
```

如果你的 vault 路径不一样，改 `config/default.yaml` 里的 `vault.drafts_dir` 和 `vault.value_dir`。

## 3. 拷风格模板

```bash
cp ~/.openclaw/workspace/skills/auto-content-pipeline/templates/style-templates/*.md \
   "$VAULT/00-转型·一人事业/04-原创写作专区/价值文章/_config/style-templates/"
```

## 4. 写一篇草稿，跑一条龙

```bash
# 1) 在草稿区放文章
echo "# 我的第一篇正文..." > "$VAULT/00-转型·一人事业/04-原创写作专区/草稿/第一篇.md"

# 2) 一条龙（ingest → review → modify → illustrate → store）
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py run-all "$VAULT/00-转型·一人事业/04-原创写作专区/草稿/第一篇.md"

# 3) 看产物
ls "$VAULT/00-转型·一人事业/04-原创写作专区/价值文章/"
```

## 5. 发布到平台

```bash
# 默认发小红书（其它平台需要先配 cookie/login，详见 README.md）
python3 $ACP/scripts/pipeline.py publish <draft_id> --platforms=xiaohongshu
```

## 6. 让别的 agent 调用

最小调用：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: review。
draft_id: 2026-08-22_xxx
```

子 agent 读 SKILL.md 自己就知道怎么干。

## 排错

| 现象 | 可能原因 | 解决 |
|------|----------|------|
| `pipeline.py run-all` 卡在 review | agent 没调 LLM（占位 prompt） | 手动 `pipeline.py review <id>` 后改 review.json，再 `modify` |
| `illustrate` 没生成图 | agent 没调 image_generate | 手动 `image_generate` 写到 `cover.png`，再 `store` |
| `publish xiaohongshu` 失败 | cookie 过期 | `python3 ~/.openclaw/workspace/xiaohongshu_poster.py login` |
| `publish juejin/sspai/zhihu` 失败 | cookie 未配置 | 在 `config/default.yaml` 里加 cookie |
| `publish gongzhonghao` 报"待接入" | AppID/AppSecret 未提供 | 等 OpenClaw 接入 API，**不走浏览器** |

## 兼容性

- Python 3.9+
- OpenClaw 工作区（必须）
- Linux / macOS（没测 Windows）
- 不需要装 gemini CLI / ChatGPT API（agent 自己跑 LLM）

## 跟 v1 的区别

v1 是从零开始生产内容（scan → write → cover → publish），已弃用。
v2 是拿到草稿后打磨发布（ingest → review → modify → illustrate → store → publish）。

旧 skill 的 cron 已 disable，vault 里 v1 的文件（`07-选题与发布/`）保留兼容。