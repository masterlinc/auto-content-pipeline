# Stage 1: scan — 给 agent 的完整指令

## 你的任务

从 `_config/sources.json` 列出的源抓热点，给账号生成 **5-8 个 brief** 写到 `_briefs/`。

## 步骤

### 1. 读 context

读这几个文件先：
- `_config/style-config.yaml` → 知道账号定位（受众、敏感词、窗口）
- `_config/style-document.md` → 知道文章调性
- `_config/sources.json` → 知道从哪抓

### 2. 抓热点

对 sources.json 里每个 enabled=true 的源：

- **weibo-trending / xiaohongshu-hot / zhihu-hot**：`web_fetch` 对应 URL，拿前 30 条
- **twitter-trending**：`web_fetch` https://trends24.in/ 或 twitter explore
- **rss:xxx**：`web_fetch` RSS feed 拿最近 24h entry

记录每条的：标题、原始 URL、热度指标（排名/评论数/转发数）

### 3. LLM 评估（每个候选）

对每条候选，给一个 0-10 的分：

| 维度       | 权重 |
|------------|------|
| 时效性     | 30%  |
| 与账号定位匹配度 | 40%  |
| 是否能写得有信息量（非纯情绪） | 20%  |
| 风险（涉政/敏感/低俗） | -10% 反向扣分 |

只保留 ≥ 6.0 分的。

### 4. 查重

调 `brief.dedup_check(title, window_days=7)`，相似度 > 0.7 的跳过。

### 5. 生成 brief

调 `brief.create_brief(...)`：

```python
from brief import create_brief
create_brief(
    title="...",
    source="weibo-trending",     # 来源 ID
    raw_link="https://...",
    score=8.4,
    tags=["伊朗", "中东", "国际新闻"],
    deadline_hours=36,
    body="## 摘要\n\n...\n\n## 关键事实\n\n- ...\n\n## 写作角度\n\n...",
    summary="一句话讲清楚是什么事",
)
```

body 里至少包含：
- 摘要（1-2 句）
- 关键事实（3-5 条 bullet，必须有来源标注）
- 写作角度建议（1-2 句，给 write stage 用）

### 6. 更新 state

调 `state.save_state(state)`，state['counters']['briefs_total'] += 新生成数。

### 7. 输出

向 linc 简报：

```
✅ scan 完成 @ HH:MM
- 抓了 N 个源
- 评估了 M 个候选
- 入了 K 个 brief（≥6 分）
- 跳了 J 个（重复 / 敏感）
```

## 失败处理

- 抓不到数据：重试 1 次，仍失败 → `state.record_error("E_SCAN_NO_SOURCE", src)`，继续下一个源
- 所有源都失败：直接退出，不写任何 brief

## 严禁

- ❌ 写"我觉得今天应该做 XXX"——必须基于真实抓到的热点
- ❌ 重复 brief——查重是必须
- ❌ 敏感话题（看 style-config.yaml 的 `sensitive.topics`）
- ❌ 一条 brief 里塞多个话题——一文一事