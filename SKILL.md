---
name: auto-content-pipeline
description: "小红书/公众号自动化内容流水线：每周日 20:00 自动从互联网抓热点 → 生成候选选题 brief → 每日复核 → 推送给 linc 确认 → 自动写文章 + 生成封面 → 调用 xiaohongshu_poster.py 发布。整个流水线用 vault 状态文件串联，可被任意 agent 通过 cron / spawn / CLI 三种方式调用。"
metadata:
  {
    "openclaw":
      {
        "emoji": "📰",
        "homepage": "skills/auto-content-pipeline/README.md",
        "user_invocable": true
      }
  }
---

# Auto Content Pipeline

把"互联网热点 → 小红书文章"做成端到端自动化。任意 agent 都可以调用：本 skill 既是给主 agent 读的 SOP，也是给 cron / sub-agent 派发任务的契约。

## 六阶段流水线

```
[scan] → [review] → [confirm] → [write] → [cover] → [publish]
  周日20:00  每天09:00   等用户回复    立即       立即       立即
```

| Stage     | 触发                | 输入                                       | 输出 / 副作用                                                  | 状态字段                                       |
|-----------|---------------------|--------------------------------------------|----------------------------------------------------------------|------------------------------------------------|
| **scan**  | cron 周日 20:00     | sources.json + 历史 brief（去重）          | `_briefs/*.md` （status=`pending_review`），通常 5-10 个       | `status: pending_review`                       |
| **review**| cron 每天 09:00     | `_briefs/` 中 `pending_review` 的 brief    | 更新为 `awaiting_user`；生成 `daily-pick-YYYY-MM-DD.md` 汇总；推送飞书 | `status: awaiting_user`                        |
| **confirm**| linc 在飞书/CLI 决策 | linc 的回复                              | brief status → `approved` / `rejected` / `modified`            | `status: approved/rejected/modified`           |
| **write** | confirm 后自动      | status=`approved` 的 brief + style-document | `_drafts/{id}/article.md`                                     | `status: awaiting_cover`                       |
| **cover** | write 后自动        | article.md + style-cover                  | `_drafts/{id}/cover.png` + `cover-prompt.md`                   | `status: awaiting_publish`                     |
| **publish**| cover 后自动      | `_drafts/{id}/` 全部                      | 调用 `xiaohongshu_poster.py`，移到 `_published/{id}/`          | `status: published` + `_state.json.last_publish` |

## 三种调用方式

### 1. CLI（本地直接跑）

```bash
ACP=/Users/masterlinc/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py scan       # 周日 20:00 cron 用
python3 $ACP/scripts/pipeline.py review     # 每天 09:00 cron 用
python3 $ACP/scripts/pipeline.py confirm approved <brief_id>
python3 $ACP/scripts/pipeline.py write <brief_id>
python3 $ACP/scripts/pipeline.py cover <brief_id>
python3 $ACP/scripts/pipeline.py publish <brief_id>
python3 $ACP/scripts/pipeline.py run-all    # 一条龙（用户主动跑时用）
python3 $ACP/scripts/pipeline.py status     # 看当前所有 brief 状态
```

### 2. Cron（系统调度）

参考 `tests/install-cron.sh` —— scan 用周日 20:00，review 用每天 09:00，announce 模式让结果回推飞书。

### 3. Sub-agent（被其他 agent 调用）

任意 agent 可以 `sessions_spawn` 一个子 agent，prompt 里写：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: <scan|review|write|cover|publish>。
完成后回报：受影响 brief_id 列表、状态变更摘要、错误（如有）。
```

子 agent 读完 SKILL.md 自己就知道怎么干。

## 配置/状态文件（vault 真实路径）

```
~/Documents/Obsidian Vault/07-选题与发布/
├── _config/
│   ├── style-document.md    # 文档风格固化（标题套路、正文结构、emoji、长度、禁用词）
│   ├── style-cover.md       # 封面风格固化（比例、配色、字体、布局）
│   ├── style-config.yaml    # 账号定位 / 推送窗口 / 敏感词 / 源开关
│   └── sources.json         # 热点源 URL 列表（小红书榜 / 微博热搜 / 知乎热榜 / twitter）
├── _briefs/                 # 选题 brief（一个 .md 一份，frontmatter 含 status / score / source）
├── _drafts/<brief_id>/      # 草稿 + 封面 + 文章 + 元信息
├── _published/<brief_id>/   # 已发布归档
├── _rejected/<brief_id>/    # 已拒绝归档
├── _state.json              # 全局流水线状态（last_scan / last_review / last_publish / counters）
└── _README.md               # vault 内的快速说明
```

## Brief frontmatter 约定

```yaml
---
id: 2026-08-24_iran-israel          # 简短 kebab，唯一
created: 2026-08-24T20:03:11+08:00
source: weibo-trending              # 来源
status: pending_review             # pending_review | awaiting_user | approved | rejected | modified | awaiting_cover | awaiting_publish | published
score: 8.4                          # LLM 评分（0-10）
title: 伊朗对以色列发动大规模导弹袭击
tags: [伊朗, 以色列, 中东, 国际新闻]
deadline: 2026-08-25T18:00:00+08:00  # 时效性
raw_link: https://...               # 原始链接
---
```

## 风格规范（必须读）

执行 write / cover stage 前**必读** `_config/style-document.md` 和 `_config/style-cover.md`，所有生成内容必须符合。这两份是 lin c 亲自审过的固化版本。

修改风格规范前必须先跟 linc 确认 —— 不要自动改。

## 错误处理

- **scan 抓不到数据**：重试 3 次后写 `_state.json.last_scan_error`，不在飞书推噪音
- **publish 失败**：保留 `_drafts/` 不动，brief status 回退 `awaiting_publish`，下次重试
- **图片生成失败**：保留 article，等手动触发 cover

详细错误码见 `scripts/state.py` 顶部注释。

## 调用前后检查清单

✅ **调用前**：
1. 读 `_config/style-config.yaml` 看账号定位
2. 读 `_state.json` 看上次状态
3. 读本次 stage 对应的 prompt 文件（`prompts/<stage>.md`）

✅ **调用后**：
1. 写回 `_state.json`
2. 该推飞书就推（review / publish 后）
3. brief frontmatter status 必须更新

## 集成

- **xiaohongshu 发布**：`scripts/publish.py` 包装现有的 `~/.openclaw/workspace/xiaohongshu_poster.py post`，不直接动它
- **LLM 调用**：scan/review/write/cover 都是 agent 自身跑（读 prompt 后调用工具）；不要试图装 gemini CLI 或外部 LLM
- **图像生成**：cover stage 用 `image_generate` 工具（OpenClaw 原生）
- **推送飞书**：review 后用 `message(action=send)` 推；不要扫其它 IM