#!/usr/bin/env python3
"""Render and atomically install a complete AGER starter bundle."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ager_common import emit_write_event, resolve_author, stamp_frontmatter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO / "scaffold"
VALIDATOR = REPO / "scripts" / "ager-validate.py"
TEXT_SUFFIXES = {".md", ".txt", ".json"}


def render_tree(root: Path, title: str, timestamp: str) -> None:
    replacements = {"{{TITLE}}": title, "{{TIMESTAMP}}": timestamp}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for marker, value in replacements.items():
            text = text.replace(marker, value)
        path.write_text(text, encoding="utf-8")


def stamp_tree(root: Path, author: str) -> None:
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        path.write_text(stamp_frontmatter(path.read_text(encoding="utf-8"), author), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--title", default="AGER Agent Graph")
    parser.add_argument("--author", default="")
    args = parser.parse_args()

    destination = args.destination.resolve()
    if destination.exists():
        parser.error(f"destination already exists; refusing to overwrite: {destination}")
    author = resolve_author(args.author)
    destination.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    temp_root = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    staged = temp_root / destination.name
    try:
        shutil.copytree(SCAFFOLD, staged)
        render_tree(staged, args.title, timestamp)
        stamp_tree(staged, author)
        check = subprocess.run(
            [sys.executable, str(VALIDATOR), str(staged), "--strict"],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            print(check.stdout, file=sys.stderr)
            print("generated scaffold failed AGER validation", file=sys.stderr)
            return 1
        validation = json.loads(check.stdout)
        os.replace(staged, destination)
        emit_write_event(
            destination,
            author=author,
            typ="Reference",
            dest=destination / "index.md",
        )
        validation["bundle"] = str(destination)
        print(json.dumps({
            "bundle": str(destination),
            "title": args.title,
            "file_count": sum(path.is_file() for path in destination.rglob("*")),
            "ager_validation": validation,
        }, indent=2))
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
