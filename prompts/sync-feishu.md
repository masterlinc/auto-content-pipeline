# Stage 6: sync-feishu — 同步到飞书云文档（通用 agent 契约）

> 任何 agent 读这份文件就知道这个 stage 怎么跑。不绑定特定实现。

## 目标

把 vault 价值文章区里打磨好的 `{draft_id}/article.md` 推到飞书云空间，
发 IM 卡片给审阅人，等他在云文档里写评论反馈。

## 前置

- `store` stage 已完成（vault 价值文章区里有 `{draft_id}/article.md`）
- `lark-cli auth status` 返回 user identity: ready
- `config/default.yaml` 里 `feishu.reviewer_chat_id` 或 `feishu.reviewer_user_open_id` 已配置

## 步骤

### 1. 读产物

```
vault_path = ~/Documents/Obsidian Vault/00-转型·一人事业/04-原创写作专区/价值文章/{draft_id}/
article = {vault_path}/article.md
cover   = {vault_path}/cover.png   (可选)
```

读 `article.md`，剥掉 frontmatter（`---...---\n\n`），剩下的就是正文。

### 2. 准备云文档内容

Markdown 模板：

```markdown
# {title}

> **审阅稿** · draft_id: `{draft_id}` · 审核轮数: {review_round}

---

{article_body}
```

### 3. 找/建飞书云空间文件夹

路径：`auto-content-pipeline/审核中/`

```bash
# 1. 列父目录，找同名 folder
lark-cli drive +search --query "审核中" --type folder
# 2. 没找到就建
lark-cli drive +create-folder --name "auto-content-pipeline" --parent-token <root_token>
lark-cli drive +create-folder --name "审核中" --parent-token <auto-content-pipeline_token>
```

返回 `folder_token`，下一步用。

### 4. 创建/更新云文档

- 如果 frontmatter 已有 `feishu_doc_token` → 复用，update 内容
- 否则 → 新建

```bash
# 新建
lark-cli docs +create \
  --title "📝 审阅:{title}" \
  --content "<上面 markdown>" \
  --content-format markdown \
  --folder-token <folder_token>
# 返回里有 doc_token 和 url

# 更新已有
lark-cli docs +update \
  --doc-token <doc_token> \
  --content "<新 markdown>" \
  --content-format markdown \
  --mode overwrite
```

### 5. （可选）上传封面图

```bash
lark-cli docs +media-upload --doc-token <doc_token> --file <cover.png>
```

### 6. 发 IM 卡片

```bash
lark-cli im +messages-send \
  --chat-id <reviewer_chat_id> \
  --msg-type interactive \
  --content '<卡片 JSON>'
```

卡片 JSON 结构：

```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "📝 待审阅:{title}"},
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**draft_id**: `{draft_id}`\n**审核轮数**: {review_round}\n**状态**: 待审阅\n\n👉 [点此进入云文档审阅]({doc_url})"
      }
    },
    {
      "tag": "action",
      "actions": [
        {"tag": "button", "text": {"tag": "plain_text", "content": "🚀 确认发布"}, "type": "primary", "url": "{doc_url}"},
        {"tag": "button", "text": {"tag": "plain_text", "content": "📝 打开云文档"}, "type": "default", "url": "{doc_url}"}
      ]
    }
  ]
}
```

### 7. 写回 frontmatter

更新 `{skill_dir}/_drafts/{draft_id}/source.md` 的 frontmatter：

```yaml
feishu_doc_token: <doc_token>
feishu_doc_url: <url>
feishu_synced_at: <ISO timestamp>
status: feishu_synced
```

### 8. 触发下一阶段

通知调用方跑 `feishu-review` stage（或继续监听）。

## 输出

- 一份飞书云文档（doc_token / url）
- 一条 IM 卡片（发给审阅人）
- frontmatter 写回 `feishu_synced`

## 错误处理

| 错误 | 怎么处理 |
|------|---------|
| lark-cli 认证失败 | 提示用户跑 `lark-cli auth login` |
| 找不到/建不了"审核中"文件夹 | fallback 到云空间根目录 |
| 封面图上传失败 | 跳过，文档照常创建 |
| IM 发送失败 | 文档已创建，把 doc_url 返回给用户，让用户手动发链接 |

## agent 提示

- 不需要依赖任何特定 agent 工具，纯 CLI + JSON
- 任何 agent 调 `python3 scripts/feishu_sync.py <draft_id>` 就能跑
- 任何 agent 也可以自己按上面步骤实现
