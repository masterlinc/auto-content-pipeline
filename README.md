# Auto Content Pipeline

小红书 / 公众号**端到端自动化**内容流水线。

## 它做什么

```
周日 20:00  抓全网热点 → 评估 → 5-10 个选题 brief
每天 09:00  复核 brief → 选 3 个 → 推送飞书等你点头
你回复 OK   自动写文章 + 生成封面 + 发布到小红书
```

## 快速跑一遍

```bash
ACP=/Users/masterlinc/.openclaw/workspace/skills/auto-content-pipeline

# 1. 跑一次 scan（生成 brief）
python3 $ACP/scripts/pipeline.py scan

# 2. 看 brief 状态
python3 $ACP/scripts/pipeline.py status

# 3. 手动触发 review（不等 cron）
python3 $ACP/scripts/pipeline.py review

# 4. 模拟你确认一个 brief
python3 $ACP/scripts/pipeline.py confirm approved 2026-08-24_xxx

# 5. 一条龙跑完剩下的
python3 $ACP/scripts/pipeline.py run-all
```

## 文件地图

```
skills/auto-content-pipeline/
├── SKILL.md               ← 必读！agent 调用契约
├── README.md              ← 你正在读
├── scripts/
│   ├── pipeline.py       ← CLI 入口
│   ├── state.py          ← vault 状态 I/O
│   ├── brief.py          ← brief frontmatter 读写
│   ├── scan.py           ← Stage 1
│   ├── review.py         ← Stage 2
│   ├── confirm.py        ← Stage 3
│   ├── write.py          ← Stage 4
│   ├── cover.py          ← Stage 5
│   └── publish.py        ← Stage 6 (包装 xiaohongshu_poster.py)
├── prompts/              ← 每个 stage 的 prompt 模板
├── config/default.yaml   ← 默认配置
└── tests/install-cron.sh ← 装 cron 的脚本
```

## Vault 那边的样子

```
~/Documents/Obsidian Vault/07-选题与发布/
├── _config/      风格固化 + 源配置（linc 自己改）
├── _briefs/      当前在跑的选题
├── _drafts/      草稿 + 封面
├── _published/   已发布（按 brief_id 归档）
├── _rejected/    已拒绝（保留 30 天做参考）
└── _state.json   流水线心跳
```

## 风格改了怎么办

`_config/style-document.md` 和 `_config/style-cover.md` 是**锁定**的。
要改直接告诉我，我会改并写到 `MEMORY.md` 记一笔。

## 给其他 agent 怎么调

最小调用：

```
请按 ~/.openclaw/workspace/skills/auto-content-pipeline/SKILL.md 执行 stage: review。
完成后回报：哪些 brief 进了 awaiting_user、推送结果。
```

子 agent 会自己读 SKILL.md、自己读 prompt、自己跑。