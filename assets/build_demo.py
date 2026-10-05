#!/usr/bin/env python3
"""Abridged reconstruction, derived from an actual synthetic-fixture output.

uv run --python 3.13 --with Pillow==11.3.0 assets/build_demo.py
Add --check to compare deterministic rebuilds without writing.
"""

import argparse
import hashlib
import io
import json
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "evidence/transcripts/2026-10-05-codex-mixed.txt"
BG, FG, MUTED, AGENT, HUMAN = "#0d1117", "#e6edf3", "#8b949e", "#7ee787", "#ffa657"
WIDTH, HEIGHT = 1500, 1180
FONT = ImageFont.load_default(size=26)
SMALL = ImageFont.load_default(size=22)


def session_lines(text):
    lines = [("what-next / v1.0.0", FG), ("Abridged reconstruction of a synthetic fixture; not a screen recording", MUTED)]
    for raw in text.splitlines():
        if re.match(r"^#{2,3} ", raw):
            heading = raw.lstrip("# ")
            lines.append((heading, AGENT if heading.startswith("Agent") else HUMAN if heading.startswith("Human") else FG))
        elif re.match(r"\|\s*[AH]\d+\s*\|", raw):
            row = [cell.strip().replace("`", "") for cell in raw.strip("|").split("|")]
            content = f"{row[0]}  {row[1]}  /  {row[3] if row[0].startswith('A') else 'unblocks ' + row[4]}"
            for part in textwrap.wrap(content, 94):
                lines.append((part, AGENT if row[0].startswith("A") else HUMAN))
        elif re.match(r"(?:- |\d+\. )[AH]\d+:", raw):
            lines.append((raw.lstrip("-0123456789. ").replace("`", ""), FG))
        elif "additional actionable choices" in raw:
            lines.append((raw, MUTED))
    return lines


def render(lines, visible):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(im)
    y = 55
    for index, (line, color) in enumerate(lines):
        if index >= visible:
            break
        heading = line.startswith(("what-next", "Agent lane", "Human lane", "Next"))
        if heading and index > 1:
            y += 28
        visible_text = line.replace("—", "-").replace("→", "->")
        draw.text((60, y), visible_text, fill=color, font=FONT if heading else SMALL)
        y += 48 if index == 0 else 42
    assert y < HEIGHT - 45, "completed session exceeds the canvas"
    draw.text((60, HEIGHT - 48), "Source: evidence/transcripts/2026-10-05-codex-mixed.txt", font=SMALL, fill=MUTED)
    return im


def build():
    lines = session_lines(SOURCE.read_text())
    human = next(i for i, (line, _) in enumerate(lines) if line == "Human lane")
    next_index = next(i for i, (line, _) in enumerate(lines) if line == "Next")
    visible = [2, human, next_index, len(lines)]
    frames = [render(lines, count) for count in visible]
    gif, poster = io.BytesIO(), io.BytesIO()
    frames[0].save(gif, format="GIF", append_images=frames[1:], save_all=True, duration=[1000, 2000, 2000, 5000], loop=0, optimize=False, disposal=1)
    frames[-1].save(poster, format="PNG")
    assets = {"demo.gif": gif.getvalue(), "demo-poster.png": poster.getvalue()}
    manifest = {"kind": "abridged reconstruction of a synthetic fixture", "source": str(SOURCE.relative_to(ROOT)), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "dependency": "Pillow==11.3.0", "canvas": [WIDTH, HEIGHT], "cumulative_visible_lines": visible, "loop": 0, "assets": {name: hashlib.sha256(data).hexdigest() for name, data in assets.items()}}
    assets["demo.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return assets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, data in build().items():
        path = HERE / name
        if args.check:
            assert path.read_bytes() == data, name + " differs from a rebuild"
        else:
            path.write_bytes(data)
    print("demo rebuild: PASS" if args.check else "wrote demo, poster and provenance")


if __name__ == "__main__":
    main()
