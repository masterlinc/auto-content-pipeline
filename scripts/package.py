#!/usr/bin/env python3
"""One-command Markdown -> visual, manual-publish content package."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from media import article_points, article_title, clean_markdown, create_assets, insert_body_images, sha256

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = Path.home() / "Documents" / "Obsidian Vault" / "00-转型·一人事业" / "04-原创写作专区" / "发布包"


def configured_output() -> Path:
    for name in ("user.yaml", "default.yaml"):
        config = ROOT / "config" / name
        if config.exists():
            match = re.search(r"^\s*output_dir:\s*[\"']?(.+?)[\"']?\s*$", config.read_text(encoding="utf-8"), re.M)
            if match:
                return Path(match.group(1)).expanduser()
    return DEFAULT_OUTPUT


def slug(title: str) -> str:
    return (re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", title).strip("-") or "untitled")[:48]


def without_frontmatter(markdown: str) -> str:
    return re.sub(r"^---\n.*?\n---\n?", "", markdown, count=1, flags=re.S).lstrip()


def xiaohongshu_copy(title: str, markdown: str) -> str:
    return f"# {title[:20]}\n\n{clean_markdown(markdown)[:900]}\n\n#内容创作 #知识管理 #个人成长\n\n上传顺序：media/cover.png → media/body-img-01.png → media/body-img-02.png"


def jike_copy(title: str, markdown: str) -> str:
    points = article_points(markdown, 2)
    return f"{title}\n\n{points[0]}。\n\n{points[1]}。\n\n完整内容见长文。"


def build_package(source: Path, output_root: Path, force: bool = False) -> Path:
    if not source.exists() or source.suffix.lower() != ".md":
        raise ValueError(f"找不到 Markdown 文章：{source}")
    markdown = source.read_text(encoding="utf-8")
    title = article_title(markdown, source.stem)
    target = output_root / f"{datetime.now():%Y%m%d}-{slug(title)}"
    if target.exists() and not force:
        raise FileExistsError(f"发布包已存在：{target}；如需覆盖，请加 --force")
    if target.exists():
        shutil.rmtree(target)
    media_dir = target / "media"
    target.mkdir(parents=True, exist_ok=True)
    assets = create_assets(markdown, media_dir, body_count=2)
    body_files = [f"media/{asset['file']}" for asset in assets if asset["role"] == "body"]
    illustrated = insert_body_images(markdown, body_files)
    (target / "article.md").write_text(illustrated, encoding="utf-8")
    (target / "微信公众号.md").write_text(f"# {title}\n\n" + without_frontmatter(illustrated), encoding="utf-8")
    (target / "小红书.md").write_text(xiaohongshu_copy(title, markdown) + "\n", encoding="utf-8")
    (target / "即刻.md").write_text(jike_copy(title, markdown) + "\n", encoding="utf-8")
    (target / "使用说明.md").write_text(
        "# 手动发布\n\n1. 公众号：复制 `微信公众号.md`，按文中位置上传 `media/` 内图片。\n2. 小红书：依次上传封面和两张正文图，再复制 `小红书.md`。\n3. 即刻：上传 `media/cover.png`，再复制 `即刻.md`。\n4. 发布前运行：`python3 scripts/pipeline.py check <本发布包目录>`。\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": "auto-content-package/v3",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "title": title,
        "source": str(source.resolve()),
        "mode": "manual_publish",
        "assets": assets,
        "platforms": {
            "wechat": {"file": "微信公众号.md", "status": "ready_for_manual_publish"},
            "xiaohongshu": {"file": "小红书.md", "status": "ready_for_manual_publish", "images": ["media/cover.png", *body_files]},
            "jike": {"file": "即刻.md", "status": "ready_for_manual_publish", "images": ["media/cover.png"]},
        },
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def validate_package(target: Path) -> list[str]:
    manifest_path = target / "manifest.json"
    if not manifest_path.exists():
        return ["缺少 manifest.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema") != "auto-content-package/v3":
        errors.append("manifest schema 不匹配")
    for asset in manifest.get("assets", []):
        path = target / "media" / asset["file"]
        if not path.exists():
            errors.append(f"缺少图片：{path.name}")
        elif sha256(path) != asset.get("sha256"):
            errors.append(f"图片已变更：{path.name}")
    for item in manifest.get("platforms", {}).values():
        if not (target / item["file"]).exists():
            errors.append(f"缺少平台文案：{item['file']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Markdown → 图文发布包（本地、可验收、手动发布）")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make", help="生成图文发布包")
    make.add_argument("article", type=Path)
    make.add_argument("--output", type=Path, default=None, help="发布包根目录")
    make.add_argument("--force", action="store_true", help="覆盖同名发布包")
    check = sub.add_parser("check", help="检查发布包是否完整")
    check.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "make":
            target = build_package(args.article.expanduser(), (args.output or configured_output()).expanduser(), args.force)
            errors = validate_package(target)
            if errors:
                raise RuntimeError("；".join(errors))
            print(f"✅ 发布包已生成：{target}")
            print("   公众号：微信公众号.md")
            print("   小红书：小红书.md + 3 张图")
            print("   即刻：即刻.md + 1 张图")
            return 0
        errors = validate_package(args.package.expanduser())
        if errors:
            print("❌ 发布包不完整：\n- " + "\n- ".join(errors))
            return 1
        print("✅ 发布包完整，可手动发布")
        return 0
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
