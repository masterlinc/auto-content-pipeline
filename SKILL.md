---
name: auto-content-pipeline
description: "内容打磨 + 飞书云文档审核 + 多平台发布流水线（v2.1）：拿到草稿后按公众号 / 网红 / 极客 / dankoe 四种风格模板 review → 自动 modify → 图文并茂 illustrate → 入库到 Obsidian 价值文章区 → **同步到飞书云文档供审阅**（v2.1 新增）→ **拉飞书云文档评论循环改稿**（v2.1 新增）→ 通过审核后一键分发到小红书 / 掘金 / 少数派 / 知乎 / 公众号（API 待接入）。任意 OpenClaw agent 都可通过 CLI / sub-agent / 对话驱动三种方式调用。v3 Codex Harness 集成作为可选项（ACP_USE_CODEX=1）。"
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

# Auto Content Pipeline v2.1 — 打磨工坊 + 飞书云文档审核

把"草稿 → 公众号/网红/极客/dankoe 风爆款文 → **飞书云文档审核** → 多平台分发"做成端到端自动化。**任意 agent 都可以调用**——不绑定特定 agent 实现。

> **版本说明**：当前活跃版本是 **v2.1**。v3（OpenAI Codex Harness 集成）的代码保留在树里，通过 `ACP_USE_CODEX=1` 启用。v2.1 新增飞书云文档审核循环（sync-feishu + feishu-review 两个 stage）。

## 7 阶段流水线（含审核循环）

```
[ingest] → [review] → [modify] → [illustrate] → [store]
  拿草稿     风格评审     自动润色     图文并茂      入库
                                                 ↓
                              ┌──→ [sync-feishu]    推飞书云文档 + 发 IM 卡片
                              │         ↓
                              │  [feishu-review] 拉评论，分类
                              │         ↓
                              │  分类: pass → 跳到 publish
                              │         ↓ reject
                              │  [modify]   按评论改稿
                              │         ↓
                              │  [sync-feishu] 重新推飞书（update 不是 create）
                              │         ↓
                              │  [feishu-review] 重新拉评论
                              │         ↓
                              └──┘ loop until pass
                                                 ↓
                                              [publish] 多平台分发
```

| Stage        | 做什么                                              | 输入                          | 输出                                              | Prompt |
|--------------|-----------------------------------------------------|-------------------------------|---------------------------------------------------|--------|
| **ingest**   | 拿草稿                                              | vault 草稿 / 手动 / scan 子流程 | `_drafts/{id}/source.md`                          | `prompts/ingest.md` |
| **review**   | 按 dankoe/公众号/网红/极客 4 套风格模板打分 | source + 4 个模板             | `review.json`（每维度得分 + 改稿建议）           | `prompts/review.md` |
| **modify**   | 自动按 review 结果改稿                              | source + review.json          | `_drafts/{id}/article.md`                         | `prompts/modify.md` |
| **illustrate** | 配图（封面 + 正文 2-3 张）                        | article.md                    | cover.png + body-img-{n}.png                      | `prompts/illustrate.md` |
| **store**    | 入库到 Obsidian 价值文章区                          | 全部 draft 产物               | vault `04-原创写作专区/价值文章/{id}/`            | `prompts/store.md` |
| **sync-feishu** ⭐ | 推到飞书云文档 + 发 IM 卡片给审阅人       | store 后的 article.md         | 飞书 doc_token + IM 消息                          | `prompts/sync-feishu.md` |
| **feishu-review** ⭐ | 拉飞书云文档评论，分类 + 更新 status | doc_token                     | JSON: verdict / suggestions / next_action         | `prompts/review-loop.md` |
| **publish**  | 多平台分发                                          | store 后的成品                | 小红书 + 掘金 + 少数派 + 知乎（公众号待接入 API） | `prompts/publish.md` |

## 三种调用方式

### 1. CLI（默认走 v2.1）

```bash
ACP=~/.openclaw/workspace/skills/auto-content-pipeline
python3 $ACP/scripts/pipeline.py ingest       <草稿路径>
python3 $ACP/scripts/pipeline.py review      <draft_id>
python3 $ACP/scripts/pipeline.py modify      <draft_id>
python3 $ACP/scripts/pipeline.py illustrate  <draft_id>
python3 $ACP/scripts/pipeline.py store       <draft_id>
python3 $ACP/scripts/pipeline.py sync-feishu <draft_id>     # v2.1 新增
python3 $ACP/scripts/pipeline.py feishu-review <draft_id>   # v2.1 新增
python3 $ACP/scripts/pipeline.py publish     <draft_id> --platforms xiaohongshu,juejin
python3 $ACP/scripts/pipeline.py run-all     <草稿>
python3 $ACP/scripts/pipeline.py status
```

### 2. CLI（v3 Codex Harness 模式）

```bash
# 装 Codex CLI（一次性）
npm install -g @openai/codex

# 启用 v3
ACP_USE_CODEX=1 python3 $ACP/scripts/pipeline.py review <draft_id>
ACP_DRY_RUN=1 ACP_USE_CODEX=1 python3 $ACP/scripts/pipeline.py review <draft_id>  # 只打印 prompt
```

### 3. Sub-agent（被其他 agent 调用 — **推荐方式**）

**任意 agent**（Mavis / Codex / Claude Code / Cursor / 任何 CLI LLM agent）都可以这样调：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: <ingest|review|modify|illustrate|store|sync-feishu|feishu-review|publish>。
draft_id: <id>
```

子 agent 读 SKILL.md → 知道 stage 是什么 → 读 `prompts/<stage>.md` → 自己决定怎么实现。

不绑定任何 agent 的工具——所有 stage 都用 `lark-cli` + `python3` 实现，任何 agent 都能跑。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `ACP_USE_CODEX` | `0`（v2） | `1` 走 v3 Codex Harness |
| `ACP_DRY_RUN` | `0` | `1` 让 Codex 只打印 prompt 不真跑 |
| `ACP_USE_V2` | `1`（v2） | 冗余写明，强制 v2 |

## 配置 / 状态文件

### Skill 端

```
skills/auto-content-pipeline/
├── ARCHITECTURE.md       ← v3 设计文档（参考）
├── SKILL.md               ← 本文件（v2）
├── README.md
├── CHANGELOG.md
├── VERSION                ← 2.0.0
├── config/
│   ├── default.yaml       ← 平台 + 路径 + 模板
│   └── codex.toml.example ← v3 Codex 配置示例
├── prompts/               ← 每个 stage 的 prompt
├── scripts/
│   ├── pipeline.py        ← CLI 入口（v2/v3 双轨）
│   ├── codex_runner.py    ← v3 Codex 薄包装
│   └── state.py / brief.py / ingest.py / review.py / modify.py / illustrate.py / store.py / publish.py
└── templates/style-templates/
    ├── dankoe.md          ⭐ 默认
    ├── 公众号.md / 网红.md / 极客.md
```

### Vault 端

```
~/Documents/Obsidian Vault/
├── 00-转型·一人事业/04-原创写作专区/
│   ├── 草稿/             ← ingest 来源
│   ├── 价值文章/         ← store 目标
│   └── _config/style-templates/  ← 4 风格模板
└── 07-选题与发布/        ← v1 遗留，仍兼容
```

## Draft 状态机（v2.1 含飞书审核循环）

```
ingest_done → reviewed → modified → illustrated → stored
                                                ↓
                                   feishu_sync_pending
                                                ↓
                                   feishu_synced
                                                ↓
                                   feishu_review_pending
                                                ↓ (有评论)
                                   feishu_review_modifying
                                                ↓
                                   feishu_review_syncing
                                                ↓
                                   feishu_review_pending  ← loop
                                                ↓ (pass)
                                   feishu_review_passed
                                                ↓
                                   publish_pending → published
                                       ↓
                                   failed（任意 stage 可失败）
```

**关键约定**：
- 任何 stage 写 status 到 `_drafts/{draft_id}/source.md` 的 frontmatter
- 飞书相关字段：`feishu_doc_token` / `feishu_doc_url` / `review_round` / `last_seen_comment_id`
- 飞书评论拉取用 `lark-cli drive +list-comments`，不依赖 SDK
- 评论分类逻辑在 `scripts/state.py::classify_feishu_comment()`，agent 可以复用

## 风格模板（review + illustrate 阶段必读）

`templates/style-templates/` 目录下放 4 份风格规范：

### ⭐ 默认模板：`dankoe.md`

**所有 illustrate 出图默认走这个**（除非 frontmatter 显式指定）。

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
- `公众号-图文增强.md` —— **v2 升级版**：4 版本同存 + Obsidian callouts + mermaid + LaTeX + Unicode 条 + 10 维度评分表。基于 2026-08-07 Tsipursky manager audit 图文增强版。**这是「AI 管理现场」系列的默认模板。**
- `网红.md` —— 短句 / emoji 多 / 情绪化 / 个人化视角 / 一句话金句
- `极客.md` —— 技术准确 / 代码块 / 工具对比表 / 客观中立

### 选模板顺序（illustrate stage 默认）

1. **观点 / 强情绪 / 反常识** → **`dankoe.md`**（默认）
2. 教程 / 工具盘点 / 实操 → 极客.md
3. 种草 / 体验 / 个人故事 → 网红.md
4. 长文深度 / 案例分析 → 公众号.md
5. **AI 管理现场 / 战略 / 一人事业** → **`公众号-图文增强.md`** ⭐ 推荐

修改风格规范前必须跟 linc 确认 —— agent 不自动改。

## 发布平台（v2.0.0）

| 平台       | 状态                | 实现方式                |
|------------|---------------------|-------------------------|
| 小红书     | ✅ 可用              | xiaohongshu_poster.py   |
| 掘金       | 🚧 待配置 cookie    | juejin API              |
| 少数派     | 🚧 待配置           | sspai API               |
| 知乎       | 🚧 待配置           | zhihu API               |
| 公众号     | ⏸ 待接入 API        | **不走浏览器**，等 AppID/AppSecret |

## v1 → v2 → v2.1 → v3 迁移

| 版本 | 时间 | 状态 |
|------|------|------|
| v1 | 2026-08-22 上午 | 已弃用（scan → write → cover → publish） |
| v2 | 2026-08-22 下午 | 6 stage 独立 Python 脚本 |
| **v2.1** | **2026-08-23** | **当前默认**（+ sync-feishu + feishu-review 两个 stage，飞书云文档审核循环） |
| v3 | 2026-08-22 深夜 | 暂缓（Codex Harness 集成，文件保留在树里，ACP_USE_CODEX=1 启用） |

- v1 cron（`acp-scan-weekly` / `acp-review-daily`）已 disable
<<<<<<< SKILL.md
- v2 stage 脚本**保留可用**
- v2.1 新增：`scripts/feishu_sync.py` / `scripts/feishu_review.py` / `prompts/sync-feishu.md` / `prompts/review-loop.md`
- v3 文件保留：codex_runner.py / ARCHITECTURE.md / codex.toml.example

## v2.1 飞书云文档审核配置

在 `config/default.yaml` 里配 `feishu` 段：

```yaml
feishu:
  reviewer_chat_id: "oc_xxxx"           # 必填，审阅人飞书 chat_id
  reviewer_user_open_id: ""             # 备选，自动解析成 chat_id
  audit_folder: "auto-content-pipeline/审核中"
  title_prefix: "📝 审阅:"
  dry_run: false
  pass_keywords: [确认发布, 通过, approved, ...]
  reject_keywords: [打回, 重写, 退回, ...]
```

**前置**：
- `lark-cli auth status` 返回 user identity: ready
- 飞书云空间根目录有写权限
- 审阅人 chat_id 拿到（p2p 个人聊天 或 群聊）
=======
- v2 stage 脚本**保留可用**（当前默认）
- v3 文件保留：codex_runner.py / ARCHITECTURE.md / codex.toml.example
---

# 附录 A：踩坑记录 & 最佳实践

> **版本**：2026-08-26（基于 v2 升级 + 三平台发布的实际经验）
> **目的**：把每次踩过的坑沉淀下来，下次少走弯路。

## A.1 文件写入 & shell 坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **shell heredoc 吃特殊字符** | `<<'EOF'` 里中文弯引号 `""` / 反引号 / `$` 被 shell 解析，文件实际写入内容跟 heredoc 里的不一样 | 用 Python `Path.write_text()` 代替 heredoc；或者把内容先 base64 编码再 heredoc |
| **zsh `UID` 是只读** | `UID=xxx` 报「failed to change user ID: operation not permitted」 | 改用 `OUID` 或 `USER_ID` |
| **heredoc 静默失败** | echo "✓" 打出来了，但文件实际没创建（heredoc EOF 标记写错） | heredoc 后立刻 `ls` 验证文件存在 + 大小 > 0 |
| **路径里有「的」字漏写** | 路径少一个「的」导致 cp / open 全部找不到 | 脚本里路径用变量传递，不要手敲 |

## A.2 公众号（wechat_draft_push.py）坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **access_token 缓存假永不过期** | cache 文件写 `expires_at: 9999999999`，但实际 API 已过期（errcode 42001）| cache 用真实 unix 时间戳（`time.time() + 7200`），agent 不要手工改 |
| **IP 白名单 40164** | 跨网络 / 重启后公网 IP 变了，公众号 API 拒 | 跑前 `curl ifconfig.me` 拿当前 IP，去 mp.weixin.qq.com 加白 |
| **AppSecret 重生后旧值失效** | 重生后所有缓存 token 都作废 | 重生后必删 `~/.openclaw/workspace/.secrets/wechat_access_token.json` 强制刷新 |
| **⚠️ 中文成 \uXXXX 转义乱码**（2026-08-30 重犯） | `requests.post(url, json=...)` 默认 `ensure_ascii=True`，中文全转义成 `\u4e2d\u53f0...`；WeChat 服务端不解 JSON 转义，把字面字符串存进草稿箱 → 编辑器看到 `\u4e2d` 这种字面字符，全篇乱码。**踩过两次，必须背下来** | 手动序列化为 UTF-8 字节：`json.dumps(payload, ensure_ascii=False).encode("utf-8")` + `headers={"Content-Type": "application/json; charset=utf-8"}`，**不要**用 `requests.post(url, json=...)`（它强制 ensure_ascii=True）。验证：拉草稿回来 title/digest 必须是真中文而非 `\u` 序列 |

## A.3 小红书（xhs_cdp_publisher.py）坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **click_publish selector 失效** | 标题/正文/图都填好了，但 `RuntimeError: 发布按钮没出现` | selector 写死了，小红书偶尔改版会失效；**降级方案是手动点**（脚本退出后 Chrome 里直接点发布按钮） |
| **kill Chrome → launch → 登录态掉了** | kill + launch 后 persistent profile 登录态被清，post 检测到 `未登录` | kill+launch 后必须跑 `check-login` 验证；如掉登录，提示用户扫 QR |
| **持久 profile 路径要写对** | `--user-data-dir=~/.config/xiaohongshu-cdp/XhsAutoProfile` 必须每次都带 | 写到 `xhs_cdp_publisher.py launch()` 里，不要让用户传参 |

## A.4 即刻（jike_publisher.py）坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **token 过期 401** | 图片上传七牛失败、动态创建鉴权失败 | 跑 `jike_publisher.py login` 扫码刷新 token（Playwright 抓 `JK_ACCESS_TOKEN` from localStorage）|
| **cookies 0 条** | login 后 `auth.json` 里 `cookies: 0 条` — 正常，即刻只用 token 不用 cookies | 无需修复 |

## A.5 图像生成坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **AI 直接生成中文错字** | 封面图里的中文字经常多笔少画 | **AI 出底图（无文字）+ PIL 后处理叠字**；中文字体用 `/System/Library/Fonts/STHeiti Medium.ttc` |
| **3+ 并发触发 RPM 限流** | `minimax/image-01: rate limit exceeded(RPM)` | 串行调用，每次跑完再启下一个 |
| **mermaid Chrome headless 渲染空** | SVG 没绘制完就 screenshot，得到空白 PNG | 加 `--virtual-time-budget=5000`（等 JS 跑完）|
| **overlay 文字宽度算错** | 副标题偏移后被截断 | 用 `textbbox()` 量实际宽度，居中公式 `(W - text_w)//2` |

## A.6 内容生产坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **具体公司名（云滇/翰文）漏改** | 草稿里的真名进了发布版 | modify 阶段专门一轮「脱敏 pass」，把公司名/真人名替换为中性词 |
| **单一平台写一稿，跨平台手动复制** | 4 个平台各写一遍，重复劳动 | **4 版本同存**结构：调整版 / 图文增强版 / 小红书版 / 即刻版，同一文件 `---` 分隔 |
| **封面叠字没规范** | 不同稿子叠字位置 / 字体不一致 | 用 `<!-- 封面叠字建议 -->` HTML 注释固化建议，主标题 ≤12 字，副标题 ≤20 字 |
| **公众号不支持 mermaid 渲染** | 草稿里 mermaid 代码块在公众号显示为乱码 | 公众号用 `图文增强版` 的文字 + 表格 + emoji 子标题；mermaid 仅在小红书 / 自留地有用 |

## A.7 流程级坑

| 坑 | 症状 | 修复 |
|----|------|------|
| **publish 全自动化期望太高** | 以为脚本能一键全发 | 实际是：**自动填内容 + 半自动点发布**。每个平台都有最后一步需要人工（小红书 selector 失效 / 公众号订阅号必须人工群发 / 即刻 100 字内但 token 要刷）|
| **跨网络 → 全部 API 失败** | 换 WiFi 后 access_token、IP 白名单、cookies 全失效 | 跨网络场景下必跑「4 件事」：①check 公网 IP ②刷公众号白名单 ③即刻 token ④小红书 Chrome QR 登录 |

## A.8 推荐默认设置（基于本次实战）

```yaml
默认模板: 公众号-图文增强.md（AI 管理现场系列必选）
默认封面策略: 1242x1660（3:4）/ 900x383（公众号）/ AI 底图 + PIL 叠字
默认正文长度: 1500-2500 字（公众号）/ 600 字（小红书）/ 200 字（即刻）
默认 publish 顺序: 即刻 → 公众号 → 小红书（即刻最易，小红书 selector 最 flaky）
默认 token 缓存: 用真实 unix 时间戳，禁止 9999999999 假永不过期
默认 mermaid 渲染: Chrome headless + virtual-time-budget=5000
默认文件写入: Python Path.write_text()，不用 shell heredoc（除非纯英文）
```

---

# 附录 B：本次会话（2026-08-26）升级清单

| 改动 | 文件 | 原因 |
|------|------|------|
| 新增「公众号-图文增强.md」模板 | `templates/style-templates/` | 参考 2026-08-07 Tsipursky manager audit 图文增强版 |
| SKILL.md 选模板顺序加 v2 入口 | `SKILL.md` | AI 管理现场系列默认走 v2 |
| 本附录 A/B | `SKILL.md` | 把本次 12 条踩坑沉淀 |

## B.1 还没修的坑（建议下个版本修）

- [ ] `xhs_cdp_publisher.py click_publish()` 改用更鲁棒的 selector（找含「发布」文本的按钮，过滤「草稿」）
- [ ] `publish.py` 拆出独立的 `publish_xiaohongshu.py`，支持 `--no-auto-publish` 模式
- [ ] 公众号自动获取公网 IP + 检查白名单 + 提示用户
- [ ] 即刻 login 失败时降级方案
- [ ] 多平台并发 publish 的 lock（避免同时改 `05-发布结果.md` 冲突）
>>>>>>> /tmp/skill_mine.md
