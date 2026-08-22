#!/usr/bin/env python3
"""
v3: Codex Harness 薄包装

用法：
  python3 codex_runner.py review --draft-id 2026-08-22_xxx
  python3 codex_runner.py modify --draft-id 2026-08-22_xxx
  python3 codex_runner.py illustrate --draft-id 2026-08-22_xxx
  python3 codex_runner.py publish --draft-id 2026-08-22_xxx --platforms xiaohongshu
  python3 codex_runner.py run-all --draft <草稿.md>

环境要求：
  - Codex CLI 已装（npm i -g @openai/codex 或 brew install --cask codex）
  - `codex` 命令在 PATH 里
  - Codex OAuth 已完成（首次跑 codex 会引导）

降级：
  - 如果 codex 不存在，自动降级到 v2 stage 脚本
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from state import drafts_dir, vault_root  # noqa


CODEX_BIN = shutil.which("codex")  # 检测 Codex 是否装了


# ====== Prompt 构造 ======

PROMPTS = {
    "review": """你的任务：按 4 套风格模板给 vault 里的草稿打分。

草稿路径：{draft_path}
风格模板目录：{templates_dir}

步骤：
1. 读草稿全文
2. 加载 4 个模板：dankoe.md / 公众号.md / 网红.md / 极客.md
3. 按每个模板的 6 维度（标题 / 开头 / 结构 / 节奏 / CTA / 平台适配）打 0-10 分
4. 计算加权总分（dankoe 0.4 / 网红 0.3 / 极客 0.3，公众号独立评）
5. 选总分最高的风格作为 primary_style
6. 列出至少 3 条具体改稿建议（用 `suggestions: []` 数组）

输出到 {review_json_path}，严格按以下 JSON 格式：
```json
{{
  "draft_id": "{draft_id}",
  "reviewed_at": "<ISO8601>",
  "scores": {{"gongzhonghao": {{...}}, "wanghong": {{...}}, "jike": {{...}}}},
  "weighted_total": 7.2,
  "primary_style": "gongzhonghao",
  "suggestions": [
    {{"dimension": "标题", "current_score": 4.5, "suggestion": "...", "example_rewrite": "..."}}
  ],
  "status": "reviewed"
}}
```
""",

    "modify": """你的任务：按 review.json 的建议自动改稿。

原稿：{draft_path}
review.json：{review_path}
输出：{article_path}

步骤：
1. 读 review.json 里的 suggestions
2. 读原稿
3. 加载 primary_style 对应的模板（templates/style-templates/{{primary_style}}.md）
4. 逐条应用建议改稿（小改直接改，中改整段替换，大改标 `rewrite_segments`）
5. 保留原稿到 source.md.bak
6. 写到 article_path
7. 更新 frontmatter status 为 modified

注意：
- 不要凭空加事实
- 标题/开头改 1-2 个就够，不要全动
- 改完后字数应该在 300-700（小红书）或 1500-3000（公众号）
""",

    "illustrate": """你的任务：给 article.md 加封面 + 2-3 张正文配图。

文章：{article_path}
封面输出：{cover_path}
正文配图：{body_img_dir}

风格模板：templates/style-templates/dankoe.md（默认黑底白字单色调）

步骤：
1. 读文章标题 + 前 200 字
2. LLM 生成封面 prompt（按 dankoe 风格：黑底 + 大白字 + 一句话主张）
3. 调 image_generate 工具：
   - aspectRatio="3:4" 或 "16:9"
   - size="1242x1660" 或 "1200x675"
   - quality="high"
4. 封面写到 {cover_path}
5. 生成 2-3 张正文配图（每张一个核心观点，黑底大字）
6. 写到 {body_img_dir}/body-img-1.png / 2.png / 3.png
7. 把图引用插入 article.md frontmatter.illustrations 字段
""",

    "store": """你的任务：把打磨好的 draft 搬到 vault 价值文章区。

draft 目录：{draft_dir}
目标：{value_dir}/{{draft_id}}/

步骤：
1. 读 article.md / cover.png / review.json
2. 复制到 {value_dir}/{{draft_id}}/
3. 写 meta.json（draft_id / title / primary_style / review_score / word_count / publish_status: pending）
4. 更新 {value_dir}/_index.md（按时间倒序加一行）
""",

    "publish": """你的任务：把成品发到指定平台。

draft 目录：{draft_dir}
目标平台：{platforms}

支持的平台：
- xiaohongshu: ~/.openclaw/workspace/xiaohongshu_poster.py post
- juejin / sspai / zhihu: 占位（待配 cookie）
- gongzhonghao: 占位（等 AppID/AppSecret，不走浏览器）

步骤：
1. 读 article.md / cover.png / meta.json
2. 对每个平台调对应的 publish 工具
3. 失败继续，不要中断
4. 更新 meta.json.published_platforms + publish_status
5. 失败原因写进 meta.json.errors
""",
}


# ====== Codex 调用 ======

def call_codex(prompt: str, dry_run: bool = False, timeout: int = 300) -> dict:
    """调 Codex CLI 执行 prompt。"""
    if not CODEX_BIN:
        return {
            "ok": False,
            "error": "codex CLI 未装。装：`npm i -g @openai/codex` 或 `brew install --cask codex`",
        }

    if dry_run:
        print(f"\n[dry-run] 会调：")
        print(f"  {CODEX_BIN} -p \"<prompt>\"")
        print(f"  prompt 前 200 字符: {prompt[:200]}...")
        return {"ok": True, "dry_run": True}

    try:
        result = subprocess.run(
            [CODEX_BIN, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[-1000:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Codex 超时（>{timeout}s）"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ====== Stage 实现 ======

def run_review(draft_id: str, dry_run: bool = False) -> dict:
    draft_path = drafts_dir() / draft_id / "source.md"
    review_path = drafts_dir() / draft_id / "review.json"
    templates_dir = HERE.parent / "templates" / "style-templates"

    prompt = PROMPTS["review"].format(
        draft_path=draft_path,
        review_json_path=review_path,
        templates_dir=templates_dir,
        draft_id=draft_id,
    )
    return call_codex(prompt, dry_run=dry_run, timeout=300)


def run_modify(draft_id: str, dry_run: bool = False) -> dict:
    draft_path = drafts_dir() / draft_id / "source.md"
    review_path = drafts_dir() / draft_id / "review.json"
    article_path = drafts_dir() / draft_id / "article.md"

    prompt = PROMPTS["modify"].format(
        draft_path=draft_path,
        review_path=review_path,
        article_path=article_path,
    )
    return call_codex(prompt, dry_run=dry_run, timeout=300)


def run_illustrate(draft_id: str, dry_run: bool = False) -> dict:
    article_path = drafts_dir() / draft_id / "article.md"
    cover_path = drafts_dir() / draft_id / "cover.png"
    body_img_dir = drafts_dir() / draft_id

    prompt = PROMPTS["illustrate"].format(
        article_path=article_path,
        cover_path=cover_path,
        body_img_dir=body_img_dir,
    )
    return call_codex(prompt, dry_run=dry_run, timeout=300)


def run_store(draft_id: str, dry_run: bool = False) -> dict:
    draft_dir = drafts_dir() / draft_id
    value_dir = vault_root() / "00-转型·一人事业" / "04-原创写作专区" / "价值文章"

    prompt = PROMPTS["store"].format(
        draft_dir=draft_dir,
        value_dir=value_dir,
        draft_id=draft_id,
    )
    return call_codex(prompt, dry_run=dry_run, timeout=120)


def run_publish(draft_id: str, platforms: list, dry_run: bool = False) -> dict:
    draft_dir = drafts_dir() / draft_id

    prompt = PROMPTS["publish"].format(
        draft_dir=draft_dir,
        platforms=", ".join(platforms),
    )
    return call_codex(prompt, dry_run=dry_run, timeout=300)


# ====== CLI ======

def main() -> int:
    if not CODEX_BIN:
        print("⚠️  codex CLI 没装。装一下：")
        print("   npm install -g @openai/codex")
        print("   或 brew install --cask codex")
        print()
        print("   或者用 --fallback-v2 降级到 v2 stage 脚本")
        return 1

    parser = argparse.ArgumentParser(description="v3 Codex runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--draft-id", required=True)
    common.add_argument("--dry-run", action="store_true", help="只打印 prompt 不真跑")

    sub.add_parser("review", parents=[common], help="review stage via Codex")
    sub.add_parser("modify", parents=[common], help="modify stage via Codex")
    sub.add_parser("illustrate", parents=[common], help="illustrate stage via Codex")
    sub.add_parser("store", parents=[common], help="store stage via Codex")

    p_pub = sub.add_parser("publish", parents=[common], help="publish stage via Codex")
    p_pub.add_argument("--platforms", default="xiaohongshu",
                       help="逗号分隔平台列表（默认 xiaohongshu）")

    args = parser.parse_args()

    handlers = {
        "review": run_review,
        "modify": run_modify,
        "illustrate": run_illustrate,
        "store": run_store,
        "publish": lambda **kw: run_publish(kw["draft_id"], kw.get("platforms", "xiaohongshu").split(","), dry_run=kw.get("dry_run", False)),
    }

    kwargs = vars(args).copy()
    cmd = kwargs.pop("cmd")
    platforms = kwargs.pop("platforms", None)

    handler = handlers[cmd]
    if cmd == "publish":
        result = handler(draft_id=kwargs["draft_id"], platforms=platforms, dry_run=kwargs["dry_run"])
    else:
        result = handler(**kwargs)

    if result.get("ok"):
        print(f"✅ {cmd} OK")
        if result.get("stdout"):
            print("--- stdout ---")
            print(result["stdout"])
    else:
        print(f"❌ {cmd} 失败: {result.get('error', result.get('stderr', 'unknown'))}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
