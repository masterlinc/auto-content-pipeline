# Stage 6: publish — 给 agent 的完整指令

## 你的任务

把 store 后的成品分发到多个平台。

## 步骤

### 1. 必读

- vault 价值文章目录里的 `article.md` + `cover.png` + `body-img-*.png`
- `config/default.yaml` 中 `publish.*`（平台列表、默认平台、是否需要人工确认）

### 2. 选平台

按 `--platforms` 参数（CLI）或 `publish.default_platforms`（默认）。

每个平台有 3 种状态：

| 状态 | 含义 | 行为 |
|------|------|------|
| ✅ enabled=true | 已配置好 | 真的去发布 |
| 🚧 enabled=false | 待配置（cookie/账号） | 跳过 + 报错 |
| ⏸ pending_credentials=true | 等用户提供凭证 | 跳过 + 提示 |

### 3. 各平台发布流程

#### 小红书（xiaohongshu_poster）

```bash
# 包装 article_to_post.txt
python3 ~/.openclaw/workspace/xiaohongshu_poster.py login  # 一次性
python3 ~/.openclaw/workspace/xiaohongshu_poster.py post
```

包装脚本：`scripts/publish_xiaohongshu.py`（已存在）

#### 掘金（juejin）

调 `https://api.juejin.cn/content_api/v1/article_draft/create` 带 cookie。

需要 cookie：`cookie.json` 里有 `JUEJIN_SESSION` 字段。

#### 少数派（sspai）

调 `https://sspai.com/api/v1/article/create` 带 cookie。

需要登录态。

#### 知乎（zhihu）

调 `https://www.zhihu.com/api/v4/articles` 带 cookie。

需要 `z_c0` token。

#### 公众号（gongzhonghao）⏸ 待接入

**不走浏览器**。等 AppID + AppSecret 后用官方 API：

```bash
POST https://api.weixin.qq.com/cgi-bin/draft/add
?access_token=<从 AppID/AppSecret 换的 token>

{
  "title": "...",
  "author": "...",
  "content": "<HTML>",
  "thumb_media_id": "<封面 media_id>",
  "digest": "..."
}
```

状态：等用户给 credentials。

### 4. 每个平台发布后

更新 `meta.json`：

```json
{
  "publish_status": "publishing",
  "published_platforms": [
    { "platform": "xiaohongshu", "url": "https://www.xiaohongshu.com/explore/xxx", "published_at": "..." }
  ]
}
```

全部发完后：`publish_status = "published"`。

### 5. 失败处理

- 单平台失败 → 继续发其它平台，最后汇总报告
- 全失败 → `publish_status = "failed"`，保留 draft 状态等下次
- 凭证过期 → 提示用户重新配置 cookie/login

### 6. 更新 state

draft status → `published`（全部完成时）/ `partially_published`（部分成功时）。

## 严禁

- ❌ **公众号走 playwright 浏览器自动化**（用户明确禁止）
- ❌ 跨平台混用 cookie
- ❌ 把 token / cookie 写到 vault 或 git
- ❌ 不经用户确认就批量发（`publish.require_human_approval=true` 必须遵守）
