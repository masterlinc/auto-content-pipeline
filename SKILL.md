---
name: auto-content-pipeline
description: "内容打磨 + 多平台发布流水线：拿到草稿后按公众号 / 网红 / 极客三种风格模板 review → 自动 modify → 图文并茂 illustrate → 入库到 Obsidian 价值文章区 → 一键分发到小红书 / 掘金 / 少数派 / 知乎 / 公众号（API 待接入）。任意 OpenClaw agent 都可通过 CLI / cron / sub-agent 三种方式调用。"
metadata:
  {
    "openclaw":
      {
        "emoji": "✨",
        "homepage": "skills/auto-content-pipeline/README.md",
        "user_invocable": true
      }
  }
---

# Auto Content Pipeline v2 — 打磨工坊

把"草稿 → 公众号/网红/极客风爆款文 → 多平台分发"做成端到端自动化。任意 agent 都可以调用。

> **v1 → v2 重大变更**：v1 是"从零开始生产内容"（scan → review → write → cover → publish）。v2 改成"**拿到草稿后打磨发布**"（ingest → review → modify → illustrate → store → publish）。scan 子流程保留作为 ingest 的可选源。

## 六阶段流水线

```
[ingest] → [review] → [modify] → [illustrate] → [store] → [publish]
  拿草稿     风格评审     自动润色     图文并茂      入库       多平台分发
```

| Stage        | 做什么                                              | 输入                          | 输出                                              |
|--------------|-----------------------------------------------------|-------------------------------|---------------------------------------------------|
| **ingest**   | 拿草稿                                              | vault 草稿 / 手动 / scan 子流程 | `_drafts/{id}/source.md`                          |
| **review**   | 按 公众号/网红/极客 三套风格模板打分               | source + 3 个模板             | `review.json`（每维度得分 + 改稿建议）           |
| **modify**   | 自动按 review 结果改稿                              | source + review.json          | `_drafts/{id}/article.md`                         |
| **illustrate** | 配图（封面 + 正文 2-3 张）                        | article.md                    | cover.png + body-img-{n}.png                      |
| **store**    | 入库到 Obsidian 价值文章区                          | 全部 draft 产物               | vault `04-原创写作专区/价值文章/{id}/`            |
| **publish**  | 多平台分发                                          | store 后的成品                | 小红书 + 掘金 + 少数派 + 知乎（公众号待接入 API） |

## 三种调用方式

### 1. CLI（本地直接跑）

```bash
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py ingest    <草稿路径或brief_id>
python3 $ACP/scripts/pipeline.py review   <draft_id>
python3 $ACP/scripts/pipeline.py modify   <draft_id>
python3 $ACP/scripts/pipeline.py illustrate <draft_id>
python3 $ACP/scripts/pipeline.py store    <draft_id>
python3 $ACP/scripts/pipeline.py publish  <draft_id> --platforms xiaohongshu,juejin
python3 $ACP/scripts/pipeline.py run-all  <草稿> --from ingest   # 一条龙
python3 $ACP/scripts/pipeline.py status   # 看所有 draft 状态
```

### 2. Cron（系统调度）

参考 `tests/install-cron.sh`：
- ingest 扫描可挂周日 20:00（用 v1 留下来的 scan 子流程）
- store→publish 可挂用户指定时间

### 3. Sub-agent（被其他 agent 调用）

任意 agent 可以 spawn 子 agent：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: <ingest|review|modify|illustrate|store|publish>。
draft_id: <id>
完成后回报：状态变更摘要、关键评分、产物路径。
```

## 配置/状态文件

### Skill 端（workspace）

```
skills/auto-content-pipeline/
├── SKILL.md
├── config/default.yaml        # 全局配置（发布平台、风格模板路径、敏感词）
├── prompts/                   # 每个 stage 的 prompt 模板
│   ├── ingest.md
│   ├── review.md
│   ├── modify.md
│   ├── illustrate.md
│   ├── store.md
│   └── publish.md
├── scripts/                   # 9 个 stage + 工具脚本
└── templates/style-templates/ # 公众号/网红/极客 风格模板（示例）
```

### Vault 端（用户）

```
~/Documents/Obsidian Vault/
├── 00-转型·一人事业/
│   └── 04-原创写作专区/
│       ├── 草稿/             ← ingest 来源（手动写）
│       ├── 价值文章/         ← store 目标（打磨后可发）
│       └── _config/style-templates/  # 风格模板（公众号/网红/极客）
└── 07-选题与发布/            ← v1 留下来的 scan/brief 区，仍兼容
```

## Draft 状态机

```
pending → ingest_done → reviewed → modified → illustrated → stored → published
                                       ↓
                                   failed（任意 stage 可失败）
```

## 风格模板（review + illustrate 阶段必读）

`templates/style-templates/` 目录下放 4 份风格规范：

### ⭐ 默认模板：`dankoe.md`

**所有 illustrate 出图默认走这个**（除非 frontmatter 显式指定其它）。

基于公开研究的 Dan Koe 视觉 + 写作风格，分 3 部分：

| Part | 用途 | Stage |
|------|------|-------|
| **Part 1 视觉** | 配色/字体/排版/尺寸 | illustrate, cover |
| **Part 2 写作** | 5 个核心模式 + 3-beat 结构 + review 加成 | review, modify |
| **Part 3 选模板顺序** | dankoe vs 极客 vs 网红 vs 公众号 怎么选 | illustrate |

视觉要点：黑底白字 / 单色调（4 色）/ 大字占 60-80% / 大留白 / 一句一观点 / 16:9 横幅。
写作要点：哲学 + 实操双层 / identity-shift hook / 现代僧侣哲学框架 / 流程揭示。

### 其它 3 个模板（按需）

- `公众号.md` —— 长文 / 标题党 / 故事化开头 / 多段落 / 强 CTA
- `网红.md` —— 短句 / emoji 多 / 情绪化 / 个人化视角 / 一句话金句
- `极客.md` —— 技术准确 / 代码块 / 工具对比表 / 客观中立

### 选模板顺序（illustrate stage 默认）

1. **观点 / 强情绪 / 反常识** → **`dankoe.md`**（默认）
2. 教程 / 工具盘点 / 实操 → 极客.md
3. 种草 / 体验 / 个人故事 → 网红.md
4. 长文深度 / 案例分析 → 公众号.md

修改风格规范前必须跟 linc 确认 —— agent 不自动改。

## 发布平台（v2.0.0）

| 平台       | 状态                | 实现方式                |
|------------|---------------------|-------------------------|
| 小红书     | ✅ 可用              | xiaohongshu_poster.py   |
| 掘金       | 🚧 待配置 cookie    | juejin API              |
| 少数派     | 🚧 待配置           | sspai API               |
| 知乎       | 🚧 待配置           | zhihu API               |
| 公众号     | ⏸ 待接入 API        | **不走浏览器**，等 AppID/AppSecret |

## v1 → v2 迁移

- v1 的 `auto-content-pipeline/SKILL.md` 已替换
- v1 的 cron（acp-scan-weekly / acp-review-daily）已 disable
- SkillHub 上 `auto-flow` 已升级到 v2.0.0
- v1 的 vault 文件（07-选题与发布/）保留作为 scan 子流程的存储
