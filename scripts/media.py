#!/usr/bin/env python3
"""Deterministic, local-first visual cards for a Markdown article."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

PALETTE = {"ink": "#102A43", "blue": "#2563EB", "paper": "#F8FAFC", "muted": "#52606D", "line": "#CBD5E1", "accent": "#F97316"}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for raw in (os.getenv("ACP_FONT_PATH", ""), "/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if raw and Path(raw).exists():
            try:
                return ImageFont.truetype(raw, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    lines, current = [], ""
    for char in text.strip():
        trial = current + char
        if current and draw.textbbox((0, 0), trial, font=font)[2] > width:
            lines.append(current)
            current = char
        else:
            current = trial
    return lines + ([current] if current else []) or ["未命名文章"]


def _draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, width: int, fill: str, spacing: int = 14, max_lines: int | None = None) -> int:
    x, y = xy
    lines = _wrap(draw, text, font, width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("，。；：、") + "…"
    line_height = font.getbbox("中A")[3] - font.getbbox("中A")[1] + spacing
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def clean_markdown(markdown: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", markdown, count=1, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return re.sub(r"\s+", " ", re.sub(r"[*_>#]", "", text)).strip()


def article_title(markdown: str, fallback: str = "未命名文章") -> str:
    match = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", markdown, flags=re.M)
    if match:
        return match.group(1).strip()
    match = re.search(r"^#\s+(.+?)\s*$", markdown, flags=re.M)
    return match.group(1).strip() if match else fallback


def article_points(markdown: str, count: int) -> list[str]:
    headings = [re.sub(r"^#+\s*", "", line).strip() for line in markdown.splitlines() if line.startswith("##")]
    chunks = [x.strip() for x in re.split(r"[。！？]\s*", clean_markdown(markdown)) if len(x.strip()) >= 12]
    points = []
    for item in headings + chunks:
        if item and item not in points:
            points.append(item[:54])
        if len(points) == count:
            break
    return points + ["把一个观点拆成可执行的一步"] * (count - len(points))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_cover(path: Path, title: str, subtitle: str) -> None:
    image = Image.new("RGB", (1242, 1660), PALETTE["ink"])
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((74, 92, 1168, 1568), radius=34, outline=PALETTE["blue"], width=5)
    draw.rectangle((114, 166, 290, 178), fill=PALETTE["accent"])
    _draw_wrapped(draw, (114, 245), title, _font(78), 980, "#FFFFFF", 26, 7)
    draw.line((114, 1260, 1128, 1260), fill=PALETTE["line"], width=3)
    _draw_wrapped(draw, (114, 1312), subtitle, _font(34), 930, "#D9E2EC", 14, 3)
    draw.text((114, 1500), "AUTO CONTENT PACKAGE", font=_font(24), fill="#9FB3C8")
    image.save(path, "PNG", optimize=True)


def _save_body_card(path: Path, number: int, point: str, title: str) -> None:
    image = Image.new("RGB", (1600, 900), PALETTE["paper"])
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((54, 54, 1546, 846), radius=32, fill="#FFFFFF", outline=PALETTE["line"], width=4)
    draw.ellipse((114, 120, 228, 234), fill=PALETTE["blue"])
    draw.text((149, 142), f"{number:02d}", font=_font(36), fill="#FFFFFF")
    draw.text((280, 135), title[:28], font=_font(30), fill=PALETTE["muted"])
    _draw_wrapped(draw, (114, 326), point, _font(60), 1320, PALETTE["ink"], 24, 4)
    draw.rectangle((114, 737, 510, 751), fill=PALETTE["accent"])
    draw.text((114, 778), "文章核心观点", font=_font(25), fill=PALETTE["muted"])
    image.save(path, "PNG", optimize=True)


def create_assets(markdown: str, destination: Path, body_count: int = 2) -> list[dict]:
    destination.mkdir(parents=True, exist_ok=True)
    title, points = article_title(markdown), article_points(markdown, body_count)
    cover = destination / "cover.png"
    _save_cover(cover, title, points[0])
    assets = [{"file": "cover.png", "role": "cover", "alt": title, "width": 1242, "height": 1660, "sha256": sha256(cover)}]
    for number, point in enumerate(points, 1):
        name, target = f"body-img-{number:02d}.png", destination / f"body-img-{number:02d}.png"
        _save_body_card(target, number, point, title)
        assets.append({"file": name, "role": "body", "alt": point, "width": 1600, "height": 900, "sha256": sha256(target)})
    return assets


def insert_body_images(markdown: str, files: Iterable[str]) -> str:
    pending, output = list(files), []
    for line in markdown.splitlines():
        output.append(line)
        if pending and re.match(r"^##\s+", line):
            output.extend(["", f"![配图]({pending.pop(0)})", ""])
    if pending:
        output.extend(["", "## 图文要点", ""])
        for name in pending:
            output.extend([f"![配图]({name})", ""])
    return "\n".join(output).rstrip() + "\n"
