# Auto Content Pipeline — 30 秒上手

把这套 skill 装到你自己的 OpenClaw 工作区，30 秒跑起来。

## 1. 解压 + 放到 skills 目录

```bash
unzip auto-content-pipeline.zip -C ~/.openclaw/workspace/skills/
```

最终路径：
```
~/.openclaw/workspace/skills/auto-content-pipeline/
```

## 2. 初始化你的 vault

把 `templates/` 里的文件拷到你的 Obsidian vault 对应位置：

```bash
VAULT=~/Documents/Obsidian\ Vault/07-选题与发布   # 改成你的路径
mkdir -p "$VAULT"/{_config,_briefs,_drafts,_covers,_published,_rejected}

cp templates/style-document.template.md  "$VAULT/_config/style-document.md"
cp templates/style-cover.template.md     "$VAULT/_config/style-cover.md"
cp templates/style-config.template.yaml  "$VAULT/_config/style-config.yaml"
cp templates/sources.template.json        "$VAULT/_config/sources.json"
cp templates/_state.template.json        "$VAULT/_state.json"
```

**关键**：改 `style-document.md` 和 `style-cover.md` 成你自己的账号风格（这是你跟别的小红书号差异化的地方）。

## 3. 装 xiaohongshu 发布器（可选）

发布到小红书需要：

```bash
# 1. 装 playwright
pip install playwright
playwright install chromium

# 2. 拿 xiaohongshu_poster.py（问原作者要，或者自己写一个）
# 它要支持读 article_to_post.txt + 调用 xiaohongshu.com 发布
# 放路径：~/.openclaw/workspace/xiaohongshu_poster.py

# 3. 登录（扫码）
python3 ~/.openclaw/workspace/xiaohongshu_poster.py login
```

如果不要发小红书，把 `_config/style-config.yaml` 里的 `platform: xiaohongshu` 改成你要的平台（比如公众号），再自己改 `scripts/publish.py`。

## 4. 装 cron

```bash
bash tests/install-cron.sh
```

或手动用 OpenClaw 的 cron 管理（推荐，能接飞书）：

```bash
openclaw cron add --name acp-scan-weekly \
  --schedule 'cron:0 20 * * 0' --tz Asia/Shanghai \
  --session-target isolated --payload-kind agentTurn \
  --message '按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: scan'

openclaw cron add --name acp-review-daily \
  --schedule 'cron:0 9 * * *' --tz Asia/Shanghai \
  --session-target isolated --payload-kind agentTurn \
  --delivery announce --channel feishu --to <your_id> \
  --message '按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: review'
```

## 5. 手动跑一遍验证

```bash
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py status   # 看 vault 现状
python3 $ACP/scripts/pipeline.py scan     # 手动 scan
python3 $ACP/scripts/pipeline.py review   # 手动 review（会推飞书）
python3 $ACP/scripts/pipeline.py confirm approved <brief_id>   # 模拟你点头
python3 $ACP/scripts/pipeline.py write <brief_id>
python3 $ACP/scripts/pipeline.py cover <brief_id>
python3 $ACP/scripts/pipeline.py publish <brief_id>
```

## 6. 让别的 agent 调用

最小调用：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: review。
```

子 agent 读 SKILL.md 自己就知道怎么干。

## 排错

- **scan 抓不到数据**：检查 `_config/sources.json` 的 URL 还能不能访问，有些网站反爬
- **publish 失败**：重新 `xiaohongshu_poster.py login`，小红书 cookies 1-2 周会过期
- **agent 不知道怎么干**：让它先读 SKILL.md，如果还是不动，把报错贴出来
- **风格不符**：改 `_config/style-document.md` 的 version 字段，agent 下次写文章会读新版本

## 不依赖外部 LLM

- ✅ 不需要装 gemini CLI / ChatGPT API
- ✅ 全部 LLM 调用由 agent 本身（OpenClaw）完成
- ✅ 图像生成走 OpenClaw 原生 image_generate 工具

## 兼容性

- Python 3.9+ （用了些新语法，3.8 不行）
- OpenClaw 工作区（必须）
- Linux / macOS（没测 Windows）