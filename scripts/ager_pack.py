#!/usr/bin/env python3
"""Progressive disclosure context packs from an AGER bundle.

Bodies off unless that node is the pack root. Token budget is fail-closed
(default 1/4 of SECOND_BRAIN_WINDOW_TOKENS). Node clip is not a token budget.

AGER historically delegated pack to okf-graph-eng. This packer is local so
auto-inject can fail closed without that plugin on the path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

DEFAULT_WINDOW_TOKENS = 128_000
PACK_BUDGET_DENOMINATOR = 4
SKIP_DIR_NAMES = {"packs", "write-events", "schemas", ".git", "__pycache__"}


class PackBudgetError(Exception):
    def __init__(self, tokens: int, budget: int, window: int, nodes: list[str]):
        self.tokens = tokens
        self.budget = budget
        self.window = window
        self.nodes = nodes
        super().__init__(f"pack exceeds token budget ({tokens}/{budget})")


def estimate_tokens(text: str) -> int:
    """Cheap chars/4 estimator. Not a model tokenizer."""
    if not text:
        return 0
    return (len(text) + 3) // 4


def resolve_pack_budget(
    max_tokens: str | int | None = None,
    window_tokens: str | int | None = None,
) -> tuple[int, int]:
    raw_window = (
        window_tokens
        if window_tokens not in (None, "")
        else os.environ.get("SECOND_BRAIN_WINDOW_TOKENS") or ""
    )
    window = int(raw_window) if str(raw_window).strip() else DEFAULT_WINDOW_TOKENS
    if window < 1:
        raise SystemExit("error: window tokens must be >= 1")
    raw_budget = (
        max_tokens
        if max_tokens not in (None, "")
        else os.environ.get("SECOND_BRAIN_PACK_MAX_TOKENS") or ""
    )
    budget = int(raw_budget) if str(raw_budget).strip() else max(1, window // PACK_BUDGET_DENOMINATOR)
    if budget < 1:
        raise SystemExit("error: max tokens must be >= 1")
    return window, budget


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    block = text[4:end]
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    fm: dict = {}
    links: list[dict] = []
    in_links = False
    current: dict | None = None
    for line in block.splitlines():
        if line.startswith("links:"):
            in_links = True
            continue
        if in_links:
            if re.match(r"^  - ", line):
                if current:
                    links.append(current)
                current = {}
                rest = line[4:].strip()
                if rest and ":" in rest:
                    key, val = rest.split(":", 1)
                    current[key.strip()] = val.strip().strip('"')
                continue
            if line.startswith("    ") and current is not None and ":" in line:
                key, val = line.strip().split(":", 1)
                current[key.strip()] = val.strip().strip('"')
                continue
            in_links = False
            if current:
                links.append(current)
                current = None
        if not in_links and ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"')
    if current:
        links.append(current)
    fm["links"] = links
    return fm, body


def resolve_knowledge_root(repo: Path, bundle: str | None) -> Path:
    if bundle:
        path = Path(bundle)
        if not path.is_absolute():
            path = repo / path
        return path.resolve()
    for cand in (repo / "sample-ager", repo / "knowledge", repo):
        if (cand / "index.md").is_file():
            return cand.resolve()
    return repo.resolve()


def is_concept(bundle: Path, path: Path) -> bool:
    if path.suffix != ".md":
        return False
    try:
        rel = path.relative_to(bundle)
    except ValueError:
        return False
    parts = rel.parts
    if any(part in SKIP_DIR_NAMES for part in parts[:-1]):
        return False
    name = path.name.lower()
    if name == "log.md":
        return False
    if name == "index.md" and rel != Path("index.md"):
        return False
    return True


def iter_concepts(bundle: Path):
    for path in sorted(bundle.rglob("*.md")):
        if not is_concept(bundle, path):
            continue
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        rel = "/" + path.relative_to(bundle).as_posix()
        yield rel, fm, body


def concept_ref(start: str, default_dir: str = "agents") -> str:
    start = start.strip()
    if not start:
        return start
    if not start.startswith("/"):
        if "/" not in start and not start.endswith(".md"):
            start = f"{default_dir}/{start}.md"
        elif not start.endswith(".md"):
            start = start + ".md"
        start = "/" + start.lstrip("./")
    return start


def mermaid(nodes: list[dict], edges: list[dict], max_nodes: int = 20) -> str:
    shown = nodes[:max_nodes]
    ids = {n["id"] for n in shown}
    lines = ["graph LR"]
    for node in shown:
        nid = re.sub(r"[^A-Za-z0-9_]", "_", node["id"].strip("/").replace(".md", ""))
        title = str(node.get("title") or node["id"]).replace('"', "'")
        lines.append(f'  {nid}["{title}"]')
    for edge in edges:
        if edge["from"] not in ids or edge["to"] not in ids:
            continue
        src = re.sub(r"[^A-Za-z0-9_]", "_", edge["from"].strip("/").replace(".md", ""))
        dst = re.sub(r"[^A-Za-z0-9_]", "_", edge["to"].strip("/").replace(".md", ""))
        rel = str(edge.get("rel") or "related_to")
        lines.append(f"  {src} -- {rel} --> {dst}")
    if len(lines) == 1:
        lines.append("  empty[no nodes]")
    return "\n".join(lines) + "\n"


def pack(
    bundle: Path,
    start: str,
    *,
    hops: int = 2,
    max_nodes: int = 20,
    tiny: bool = False,
) -> dict:
    if tiny:
        hops = 1
        max_nodes = 8
    start = concept_ref(start)
    catalog: dict[str, tuple[dict, str]] = {}
    outbound: dict[str, list[tuple[str, str]]] = defaultdict(list)
    inbound: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel, fm, body in iter_concepts(bundle):
        catalog[rel] = (fm, body)
        for link in fm.get("links") or []:
            target = str(link.get("target") or "").strip()
            if not target:
                continue
            if not target.startswith("/"):
                target = "/" + target.lstrip("./")
            rel_name = str(link.get("rel") or "related_to")
            outbound[rel].append((target, rel_name))
            inbound[target].append((rel, rel_name))

    if start not in catalog:
        stem = Path(start).stem
        for rel in catalog:
            if Path(rel).stem == stem or start.rstrip(".md") in rel:
                start = rel
                break

    ordered = [start]
    seen = {start}
    q = deque([(start, 0)])
    while q and len(ordered) < max_nodes:
        cur, depth = q.popleft()
        if depth >= hops:
            continue
        neighbors = outbound.get(cur, []) + inbound.get(cur, [])
        for nxt, _rel in neighbors:
            if nxt not in seen:
                seen.add(nxt)
                ordered.append(nxt)
                q.append((nxt, depth + 1))
            if len(ordered) >= max_nodes:
                break

    concepts = []
    nodes = []
    edges = []
    for path in ordered:
        rec = catalog.get(path)
        if rec is None:
            concepts.append({"path": path, "missing": True})
            continue
        fm, body = rec
        is_root = path == start
        concepts.append(
            {
                "path": path,
                "type": fm.get("type"),
                "title": fm.get("title"),
                "description": fm.get("description"),
                "tags": fm.get("tags") or [],
                "links": fm.get("links") or [],
                "body": body if is_root else "",
            }
        )
        nodes.append({"id": path, "title": fm.get("title"), "type": fm.get("type")})
        for target, rel_name in outbound.get(path, []):
            if target in seen:
                edges.append({"from": path, "to": target, "rel": rel_name})

    return {
        "start": start,
        "hops": hops,
        "max_nodes": max_nodes,
        "node_count": len(concepts),
        "concepts": concepts,
        "mermaid": mermaid(nodes, edges, max_nodes=max_nodes),
        "excluded_note": (
            "Nodes beyond hops/max_nodes omitted for progressive disclosure. "
            "Node clip is not a token budget."
        ),
    }


def render_markdown(
    pack_data: dict,
    *,
    tokens: int | None = None,
    budget: int | None = None,
) -> str:
    start = pack_data["start"]
    token_bit = f"Tokens: {tokens}/{budget} | " if tokens is not None and budget is not None else ""
    lines = [
        f"# Context pack: {start}",
        "",
        f"{token_bit}Hops: {pack_data['hops']} · nodes: {pack_data['node_count']}",
        "",
    ]
    for concept in pack_data["concepts"]:
        if concept.get("missing"):
            lines.append(f"## {concept['path']} (missing)")
            lines.append("")
            continue
        is_root = concept["path"] == start
        lines.append(f"## {concept.get('title')} (`{concept.get('type')}`)")
        lines.append("")
        lines.append(f"Path: `{concept['path']}`")
        if is_root:
            body = (concept.get("body") or "").strip()
            if body:
                lines.append("")
                lines.append(body)
        elif concept.get("description"):
            lines.append("")
            lines.append(str(concept["description"]))
        lines.append("")
    lines.append("## Graph")
    lines.append("")
    lines.append("```mermaid")
    lines.append(pack_data["mermaid"].rstrip())
    lines.append("```")
    lines.append("")
    if pack_data.get("excluded_note"):
        lines.append(f"_{pack_data['excluded_note']}_")
        lines.append("")
    return "\n".join(lines)


def finalize_markdown(
    pack_data: dict,
    *,
    max_tokens: str | int | None = None,
    window_tokens: str | int | None = None,
) -> tuple[str, dict[str, int]]:
    """Render the pack and fail closed if it exceeds the token budget."""
    window, budget = resolve_pack_budget(max_tokens, window_tokens)
    draft = render_markdown(pack_data, tokens=0, budget=budget)
    tokens = estimate_tokens(draft)
    md = render_markdown(pack_data, tokens=tokens, budget=budget)
    tokens = estimate_tokens(md)
    meta = {"tokens": tokens, "budget": budget, "window": window}
    if tokens > budget:
        raise PackBudgetError(
            tokens, budget, window, [c.get("path", "") for c in pack_data["concepts"]]
        )
    return md, meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AGER context pack")
    parser.add_argument("concept")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--hops", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=20)
    parser.add_argument("--max-tokens", default="")
    parser.add_argument("--window-tokens", default="")
    parser.add_argument("--tiny", action="store_true")
    parser.add_argument("--mermaid", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", default=None, help="Directory or file to write pack markdown")
    args = parser.parse_args(argv)
    bundle = resolve_knowledge_root(Path(args.repo).resolve(), args.bundle)
    data = pack(bundle, args.concept, hops=args.hops, max_nodes=args.max_nodes, tiny=args.tiny)
    try:
        if args.mermaid:
            window, budget = resolve_pack_budget(args.max_tokens, args.window_tokens)
            tokens = estimate_tokens(data["mermaid"])
            if tokens > budget:
                raise PackBudgetError(
                    tokens, budget, window, [c.get("path", "") for c in data["concepts"]]
                )
            print(data["mermaid"])
            return 0
        md, meta = finalize_markdown(
            data, max_tokens=args.max_tokens, window_tokens=args.window_tokens
        )
    except PackBudgetError as exc:
        payload = {
            "error": "pack exceeds token budget",
            "tokens": exc.tokens,
            "budget": exc.budget,
            "window": exc.window,
            "nodes": exc.nodes,
            "hint": "narrow --hops / --tiny; node clip is not a token budget",
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                f"error: pack exceeds token budget ({exc.tokens}/{exc.budget})",
                file=sys.stderr,
            )
        return 1

    data.update(meta)

    if args.write:
        out = Path(args.write)
        if out.is_dir() or str(args.write).endswith("/"):
            out.mkdir(parents=True, exist_ok=True)
            slug = Path(str(data["start"])).stem + ("-tiny" if args.tiny else "")
            out = out / f"{slug}-pack.md"
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}")

    if args.json:
        print(json.dumps(data, indent=2, default=str))
    elif not args.write:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
