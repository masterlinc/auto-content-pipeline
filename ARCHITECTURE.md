# Architecture — auto-content-pipeline v3

> **v3 = v2 stages + OpenAI Codex Harness as runtime**

## TL;DR

v2 是 6 个独立 Python 脚本串起来的 pipeline。**v3 把"agent runtime"换成 OpenAI 开源的 Codex Harness**——Codex 管 memory/loop/permission/tools，我们的 stage 逻辑变成 Codex 的 sub-tasks。

## 为什么这么改

| 问题 | v2 怎么解决 | v3 怎么更好解决 |
|------|------------|----------------|
| **跨 session 记忆** | 手动读 `_state.json` | Codex 内置 memory，自动持久化 |
| **复杂任务拆解** | stage 之间手动传文件 | Codex sub-agent 派发 |
| **工具调用权限** | 自己写 if-else | Codex 内置 permission system |
| **LLM 调用** | agent 手动调 image_generate 等 | Codex tool registry 自动管理 |
| **回放/审计** | 手动 log | Codex session log 全程 |

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│  Feishu IM (UI 触发)                                          │
│  linc 喊："pipeline 跑一下"                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ OpenClaw 接收
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  OpenClaw Cron / Sub-agent Dispatcher                         │
│  根据用户指令 → 派发到 Codex session                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Codex Harness (openai/codex)  ← v3 新引入的 runtime           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Agent Loop                                         │    │
│  │  ├─ memory (跨 session 持久)                         │    │
│  │  ├─ permission (工具调用授权)                        │    │
│  │  ├─ tool registry (web_search / image_generate / ...)│    │
│  │  └─ sub-agent (派发给下层)                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ↓ 触发                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  我们的 v3 stages（每个 stage = Codex sub-task）       │    │
│  │                                                      │    │
│  │  1. ingest     读 vault 草稿 / 写 _drafts/{id}/      │    │
│  │  2. review     Codex LLM + 4 风格模板评分             │    │
│  │  3. modify     Codex LLM + 自动改稿                   │    │
│  │  4. illustrate Codex LLM + image_generate 工具调用    │    │
│  │  5. store      Codex 写 vault 价值文章                │    │
│  │  6. publish    Codex 调 xiaohongshu_poster.py 等       │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Vault (Obsidian) + 5 个发布平台                               │
│  ~/Documents/Obsidian Vault/00-转型·一人事业/04-原创写作专区/  │
│  小红书 ✅ / 掘金 🚧 / 少数派 🚧 / 知乎 🚧 / 公众号 ⏸ API      │
└─────────────────────────────────────────────────────────────┘
```

## v2 → v3 的具体变化

| 组件 | v2 (Stage 脚本) | v3 (Codex sub-task) |
|------|----------------|---------------------|
| **ingest** | `python3 ingest.py file.md` | `codex -p "读 X 写到 Y"` |
| **review** | `python3 review.py draft_id`（占位）| `codex -p "按 4 模板给 X 评分"` |
| **modify** | `python3 modify.py draft_id`（占位）| `codex -p "按 review 改 X"` |
| **illustrate** | `python3 illustrate.py draft_id`（占位）| `codex -p "生成封面+正文图"` |
| **store** | `python3 store.py draft_id` | `codex -p "复制到 vault 价值文章"` |
| **publish** | `python3 publish.py draft_id --platforms` | `codex -p "发布到小红书"` |

**关键变化**：v3 把 stage 脚本从"执行者"变成"调度者"——脚本只是写好 prompt 喂给 Codex，真正的 LLM 调用 / 文件编辑 / 工具使用都由 Codex 自己干。

## Codex 给我们带来的能力

### 1. Memory（跨 session 持久化）

```bash
# v2: 每次跑都要从 _state.json 读
# v3: Codex 自动记住之前 run 过哪些 draft、改过什么

codex -p "继续昨天那个伊朗文章的 review"
# Codex 自己知道"昨天"是哪个 draft
```

### 2. Permission system（危险操作授权）

```bash
# v2: 自己写 require_human_approval
# v3: Codex 自带 — publish / delete 等动作前会问 linc

codex -p "把这篇发到小红书"
# Codex: "I'll publish this. Confirm? [Y/n]"
```

### 3. Tool registry

```bash
# v2: scripts/ 里手写调 image_generate / web_search
# v3: Codex 在 ~/.codex/config.toml 里注册一次，全局可用
#      Codex 会自己决定什么时候调哪个
```

### 4. Sub-agent 派发

```bash
# v2: stage 之间手动传文件
# v3: Codex 可以派 sub-agent 处理子任务

codex -p "review 这篇并把 review 拆成 3 个 sub-task 给不同 model"
# Codex 自己拆分 + 汇总
```

## 文件改动清单

```
NEW:
  ARCHITECTURE.md          ← 本文件
  scripts/codex_runner.py  ← Codex CLI 薄包装（v3 的入口）
  config/codex.toml.example ← Codex 配置示例

UPDATED:
  SKILL.md                 ← 改 v3（指向 Codex Harness）
  CHANGELOG.md             ← 加 v3.0.0
  VERSION                  ← 3.0.0
  prompts/*.md             ← 改为 Codex sub-task 风格
  scripts/pipeline.py      ← 改为 Codex runner 调度器
  README.md                ← 同步 v3 描述
```

## 安装 Codex

```bash
# 任选一种
npm install -g @openai/codex
brew install --cask codex

# 验证
codex --version
```

## 给 linc 的迁移清单

v2 → v3 切换步骤：

1. [ ] 装 Codex CLI（上面命令）
2. [ ] `codex` 第一次跑通 OAuth（跟 OpenAI 账号绑定）
3. [ ] 把 v2 stage 脚本改成 Codex prompt（参考 `prompts/` 目录）
4. [ ] 在 `~/.codex/config.toml` 注册我们的工具（image_generate / xiaohongshu_poster / web_fetch）
5. [ ] smoke test：`codex -p "跑一遍 auto-content-pipeline v3"`
6. [ ] 在 Feishu 触发一次完整 run
7. [ ] 对比 v2 vs v3 输出质量，决定是否完全切换

## 风险

| 风险 | 缓解 |
|------|------|
| Codex 是 Rust + Bazel，环境装不上 | 走 npm 路径（npm 一定装得上） |
| Codex OAuth 失败 | 用 API key fallback |
| Codex sub-agent 太慢 | 加 timeout，每个 stage 限 5 分钟 |
| Codex 改了 API 跟咱 prompts 不匹配 | pin Codex 版本，定期 review |

## 短期 / 中期 / 长期

| 时间 | 行动 |
|------|------|
| **短期**（现在） | v3 双轨：v2 脚本保留可独立运行，v3 Codex runner 可选启用 |
| **中期**（1 月） | 验证 Codex 在 production 的稳定性，逐步切流 |
| **长期**（3 月+） | 看 OpenClaw 是否原生集成 Codex，是的话把 OpenClaw 当 harness |

---

linc 改 → 更新 version → 通知 agent 重读。
agent **不会**自动改这份。