#!/usr/bin/env python3
"""Materialize ager_scan findings into a draft AGER OKF knowledge bundle.

Turns reverse-engineering scan output into Markdown concepts that map into the
AGER planes (core / control / memory / ops), with provenance pointing back to
source files. Pattern mirrors sac_capture / dekc_capture for agent graphs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ager_common import claimed_author, emit_write_event, resolve_author  # noqa: E402
from ager_scan import scan_root, result_to_dict  # noqa: E402

AGER_VERSION = "0.3.0"
OKF_VERSION = "0.2"


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:60] or "item"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def _frontmatter(**fields: object) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"  - target: {item['target']}")
                    lines.append(f"    rel: {item['rel']}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            text = str(value).replace('"', '\\"')
            lines.append(f'{key}: "{text}"')
    lines.append("---")
    return "\n".join(lines)


def _group_findings(findings: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for finding in findings:
        groups[finding["kind"]].append(finding)
    return groups


def capture_from_scan(
    scan: dict,
    *,
    out_dir: Path,
    title: str,
    source_root: str,
    author: str | None = None,
) -> dict:
    author = claimed_author(author)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = _group_findings(scan.get("findings", []))
    frameworks = scan.get("frameworks", [])
    created: list[str] = []
    timestamp = _now()

    # Root index
    index_body = "\n".join(
        [
            _frontmatter(
                type="Reference",
                title=title,
                description=f"Reverse-engineered agent graph knowledge from {source_root}",
                okf_version=OKF_VERSION,
                ager_version=AGER_VERSION,
                status="draft",
                timestamp=timestamp,
                author=author,
                tags=["reverse-engineered", "ager", "agkc"],
                source_root=source_root,
                frameworks=frameworks,
            ),
            "",
            f"# {title}",
            "",
            "Draft AGER knowledge bundle produced by **ager reverse-engineering**.",
            "Review, tighten contracts, then run `ager-validate` / `okf validate`.",
            "",
            "## Detected frameworks",
            "",
        ]
        + ([f"- `{fw}`" for fw in frameworks] or ["- (none)"])
        + [
            "",
            "## Scan summary",
            "",
            "```json",
            json.dumps(scan.get("summary", {}), indent=2),
            "```",
            "",
            "## Catalog",
            "",
            "- [Discoveries](/discoveries/index.md)",
            "- [Frameworks](/frameworks/index.md)",
            "- [Prompts](/prompts/index.md)",
            "- [Tools](/tools/index.md)",
            "- [MCP](/mcp/index.md)",
            "- [Graphs](/graphs/index.md)",
            "- [Loops](/runtime/index.md)",
            "- [Sandboxes](/runtime/sandboxes/index.md)",
            "- [Hyperscaler](/runtime/hyperscaler/index.md)",
            "- [Orchestration](/patterns/index.md)",
        ]
    )
    _write(out_dir / "index.md", index_body)
    created.append("index.md")

    # Discoveries summary
    disc_lines = [
        _frontmatter(
            type="Reference",
            title="Discoveries",
            description="Raw reverse-engineering discoveries",
            ager_version=AGER_VERSION,
            status="draft",
            timestamp=timestamp,
            author=author,
            tags=["discovery"],
        ),
        "",
        "# Discoveries",
        "",
        f"Source root: `{source_root}`",
        "",
        f"Total findings: **{len(scan.get('findings', []))}**",
        "",
    ]
    for kind, items in sorted(groups.items()):
        disc_lines.append(f"## {kind} ({len(items)})")
        disc_lines.append("")
        for item in items[:50]:
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else "?"
            disc_lines.append(f"- **{item['title']}** (`{loc}`) → `{item['maps_to']}`")
        if len(items) > 50:
            disc_lines.append(f"- … {len(items) - 50} more")
        disc_lines.append("")
    _write(out_dir / "discoveries/index.md", "\n".join(disc_lines))
    created.append("discoveries/index.md")

    # Framework adapters
    fw_index = [
        _frontmatter(
            type="Reference",
            title="Framework adapters",
            description="Detected agent frameworks and AGER mapping",
            ager_version=AGER_VERSION,
            status="draft",
            timestamp=timestamp,
            author=author,
            tags=["framework"],
        ),
        "",
        "# Framework adapters",
        "",
    ]
    for fw in frameworks:
        related = [f for f in scan.get("findings", []) if f.get("framework") == fw][:8]
        maps = next((f["maps_to"] for f in related if f.get("maps_to")), "AgentNode")
        body = [
            _frontmatter(
                type="Reference",
                title=fw,
                description=f"Detected framework {fw}",
                ager_version=AGER_VERSION,
                status="draft",
                timestamp=timestamp,
                author=author,
                tags=["framework", "reverse-engineered", fw],
                framework=fw,
                maps_to_ager=maps,
            ),
            "",
            f"# {fw}",
            "",
            f"Maps to AGER: `{maps}`",
            "",
            "## Evidence",
            "",
        ]
        for item in related:
            loc = f"{item.get('path')}:{item.get('line')}"
            body.append(f"- {item['title']} (`{loc}`)")
            body.append(f"  - `{item.get('excerpt', '')[:160]}`")
        rel = f"frameworks/{_slug(fw)}.md"
        _write(out_dir / rel, "\n".join(body))
        created.append(rel)
        fw_index.append(f"- [{fw}](/{rel})")
    if not frameworks:
        fw_index.append("- (none detected)")
    _write(out_dir / "frameworks/index.md", "\n".join(fw_index))
    created.append("frameworks/index.md")

    def _emit_kind(
        kind: str,
        folder: str,
        concept_type: str,
        maps_default: str,
        index_title: str,
    ) -> None:
        items = groups.get(kind, [])
        index_lines = [
            _frontmatter(
                type="Reference",
                title=index_title,
                description=f"Reverse-engineered {index_title.lower()}",
                ager_version=AGER_VERSION,
                status="draft",
                timestamp=timestamp,
                author=author,
                tags=["reverse-engineered", kind],
            ),
            "",
            f"# {index_title}",
            "",
        ]
        if not items:
            index_lines.append("- (none)")
            _write(out_dir / folder / "index.md", "\n".join(index_lines))
            created.append(f"{folder}/index.md")
            return

        # Cap concept files to keep bundles reviewable
        for idx, item in enumerate(items[:40], start=1):
            slug = _slug(f"{idx}-{item['title']}")
            rel = f"{folder}/{slug}.md"
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else source_root
            body = [
                _frontmatter(
                    type=concept_type,
                    title=item["title"][:120],
                    description=item.get("excerpt", "")[:240] or item["title"],
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["reverse-engineered", kind],
                    framework=item.get("framework"),
                    confidence=item.get("confidence"),
                    evidence_path=item.get("path"),
                    evidence_line=item.get("line"),
                    maps_to_ager=item.get("maps_to") or maps_default,
                    links=[
                        {"target": "/discoveries/index.md", "rel": "derived_from"},
                    ],
                ),
                "",
                f"# {item['title']}",
                "",
                f"- **Kind:** `{kind}`",
                f"- **Maps to AGER:** `{item.get('maps_to') or maps_default}`",
                f"- **Confidence:** {item.get('confidence')}",
                f"- **Evidence:** `{loc}`",
                "",
                "## Excerpt",
                "",
                "```text",
                (item.get("excerpt") or "")[:500],
                "```",
                "",
                "## Next authoring steps",
                "",
                "1. Promote this draft into a typed AGER concept under the main bundle.",
                "2. Attach JSON Schema I/O where applicable.",
                "3. Link with typed edges (`uses`, `delegates_to`, `controlled_by`, …).",
                "4. Run `ager-validate` / `okf validate`.",
            ]
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            index_lines.append(f"- [{item['title'][:80]}](/{rel}) — `{loc}`")
        if len(items) > 40:
            index_lines.append(f"- … {len(items) - 40} additional findings omitted; see discoveries")
        _write(out_dir / folder / "index.md", "\n".join(index_lines))
        created.append(f"{folder}/index.md")

    _emit_kind("system_prompt", "prompts/system", "Reference", "AgentNode.instructions", "System prompts")
    _emit_kind("prompt", "prompts", "Reference", "Prompt", "Prompts")
    _emit_kind("tool", "tools", "Reference", "Tool", "Tools")
    _emit_kind("mcp", "mcp", "Reference", "Tool + JsonRpcSchema", "MCP / JSON-RPC")
    _emit_kind("schema", "schemas", "Reference", "InputSchema / OutputSchema", "Schemas")
    _emit_kind("graph", "graphs", "Reference", "AgentGraph", "Graphs")
    _emit_kind("loop", "runtime/loops", "Reference", "LoopPolicy + LoopControl", "Loop controls")
    _emit_kind("orchestration", "patterns", "Reference", "OrchestratorAgent / HandoffPolicy", "Orchestration patterns")
    _emit_kind("sandbox", "runtime/sandboxes", "Reference", "ContextIsolationPolicy", "Hardened sandboxes")
    _emit_kind("hyperscaler", "runtime/hyperscaler", "Reference", "Run + CheckpointPolicy", "Hyperscaler runtimes")

    # Runtime index
    _write(
        out_dir / "runtime/index.md",
        "\n".join(
            [
                _frontmatter(
                    type="Reference",
                    title="Runtime & harness",
                    description="Loops, sandboxes, hyperscaler runtimes",
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["runtime"],
                ),
                "",
                "# Runtime & harness",
                "",
                "- [Loop controls](/runtime/loops/index.md)",
                "- [Sandboxes / microVMs](/runtime/sandboxes/index.md)",
                "- [Hyperscaler runtimes](/runtime/hyperscaler/index.md)",
            ]
        ),
    )
    created.append("runtime/index.md")

    # Combined prompts index
    _write(
        out_dir / "prompts/index.md",
        "\n".join(
            [
                _frontmatter(
                    type="Reference",
                    title="Prompts",
                    description="System and task prompts extracted from source",
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["prompt"],
                ),
                "",
                "# Prompts",
                "",
                "- [System prompts](/prompts/system/index.md)",
                "- Task / template prompts are listed in this tree after capture.",
            ]
        ),
    )
    created.append("prompts/index.md")

    log_body = "\n".join(
        [
            f"# Capture log",
            "",
            f"- {timestamp} reverse-engineered from `{source_root}`",
            f"- frameworks: {', '.join(frameworks) or '(none)'}",
            f"- findings: {len(scan.get('findings', []))}",
            f"- files written: {len(created)}",
        ]
    )
    _write(out_dir / "log.md", log_body)
    created.append("log.md")

    # Machine-readable capture report
    report = {
        "title": title,
        "out_dir": str(out_dir),
        "source_root": source_root,
        "frameworks": frameworks,
        "summary": scan.get("summary", {}),
        "files_written": created,
        "ager_version": AGER_VERSION,
        "status": "draft",
    }
    _write(out_dir / "capture-report.json", json.dumps(report, indent=2))
    created.append("capture-report.json")
    emit_write_event(
        out_dir,
        author=author,
        typ="Reference",
        dest=out_dir / "index.md",
    )
    report["files_written"] = created
    report["author"] = author
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Source repo root to scan (unless --scan-json)")
    parser.add_argument("--scan-json", type=Path, help="Existing ager_scan JSON report")
    parser.add_argument("--out", required=True, help="Output draft AGER knowledge directory")
    parser.add_argument("--title", default="Reverse-engineered agent graph")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--author", default="")
    args = parser.parse_args(argv)
    author = resolve_author(args.author)

    if args.scan_json:
        scan = json.loads(args.scan_json.read_text(encoding="utf-8"))
        source_root = scan.get("root") or str(Path(args.root).resolve())
    else:
        root = Path(args.root).resolve()
        scan = result_to_dict(scan_root(root))
        source_root = str(root)

    report = capture_from_scan(
        scan,
        out_dir=Path(args.out),
        title=args.title,
        source_root=source_root,
        author=author,
    )
    print(json.dumps(report, indent=2) if args.json else f"Wrote draft AGER bundle → {report['out_dir']} ({len(report['files_written'])} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
