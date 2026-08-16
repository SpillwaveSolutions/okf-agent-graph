#!/usr/bin/env python3
"""Shared identity helpers for AGER knowledge writes."""

from __future__ import annotations

import contextvars
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

_AUTHOR: contextvars.ContextVar[str] = contextvars.ContextVar("ager_author", default="")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_author(explicit: str | None = None) -> str:
    """Fail-closed identity claim. Prefer --author, else SECOND_BRAIN_IDENTITY."""
    author = (explicit or os.environ.get("SECOND_BRAIN_IDENTITY") or "").strip()
    if not author:
        print(
            json.dumps(
                {
                    "error": "claim an identity first",
                    "hint": "pass --author or set SECOND_BRAIN_IDENTITY",
                }
            )
        )
        raise SystemExit(1)
    _AUTHOR.set(author)
    return author


def claimed_author(explicit: str | None = None) -> str:
    author = (explicit or "").strip() or _AUTHOR.get()
    if not author:
        return resolve_author(explicit)
    return author


def stamp_frontmatter(text: str, author: str) -> str:
    """Insert author into YAML frontmatter if the file has a block and no author yet."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end < 0:
        return text
    block = text[4:end]
    if re_has_author(block):
        return text
    return "---\nauthor: " + author + text[3:]


def re_has_author(block: str) -> bool:
    for line in block.splitlines():
        if line.startswith("author:"):
            return True
    return False


def emit_write_event(
    bundle: Path,
    *,
    author: str,
    typ: str,
    dest: Path,
    host: str = "",
) -> Path | None:
    """Record a WriteEvent node. Skip self. Do not set ager_version (not an AGER type)."""
    if typ == "WriteEvent":
        return None
    try:
        rel = "/" + dest.relative_to(bundle).as_posix()
    except ValueError:
        rel = "/" + dest.name
    event_id = f"{int(datetime.now(timezone.utc).timestamp())}-{secrets.token_hex(3)}"
    ev_path = bundle / "write-events" / f"{event_id}.md"
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "type: WriteEvent\n"
        f'title: "write {typ} {dest.name}"\n'
        "status: recorded\n"
        f"timestamp: {utc_now()}\n"
        f"author: {author}\n"
        "tags:\n"
        "  - write-event\n"
        f"  - {typ.lower()}\n"
        "links:\n"
        f"  - target: {rel}\n"
        "    rel: documents\n"
        "---\n\n"
        f"# Write {typ}\n\n"
        f"- actor: `{author}`\n"
        f"- host: `{host or os.environ.get('SECOND_BRAIN_HOST', '') or 'unknown'}`\n"
        f"- path: `{rel}`\n"
        f"- type: `{typ}`\n"
    )
    ev_path.write_text(body, encoding="utf-8")
    return ev_path
