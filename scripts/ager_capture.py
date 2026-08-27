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

AGER_TYPES = {
    "Tool",
    "AgentGraph",
    "WorkerAgent",
    "JudgeAgent",
    "OrchestratorAgent",
    "SynthesizerAgent",
    "RouterAgent",
    "GuardrailAgent",
    "AgentNode",
}


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:60] or "item"


def resolve_link_prefix(
    out_dir: Path,
    *,
    bundle_root: Path | str | None = None,
    link_prefix: str | None = None,
) -> str:
    """Prefix for OKF root-relative links when --out sits under a shared bundle.

    Empty string → `/tools/read.md` (out dir is the bundle root).
    `agent-graph` → `/agent-graph/tools/read.md` (out is knowledge/agent-graph).
    """
    if link_prefix:
        part = str(link_prefix).strip().strip("/")
        return f"/{part}" if part else ""
    if not bundle_root:
        return ""
    out = Path(out_dir).resolve()
    root = Path(bundle_root).resolve()
    try:
        rel = out.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"--out {out} is not inside --bundle-root {root}") from exc
    if rel == Path("."):
        return ""
    return "/" + rel.as_posix()


def href(prefix: str, rel: str) -> str:
    rel = str(rel).lstrip("/")
    return f"{prefix}/{rel}" if prefix else f"/{rel}"


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
    bundle_root: Path | str | None = None,
    link_prefix: str | None = None,
) -> dict:
    author = claimed_author(author)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = resolve_link_prefix(
        out_dir, bundle_root=bundle_root, link_prefix=link_prefix
    )

    def link(rel: str) -> str:
        return href(prefix, rel)

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
            "- [Discoveries](" + link("discoveries/index.md") + ")",
            "- [Frameworks](" + link("frameworks/index.md") + ")",
            "- [Agents](" + link("agents/index.md") + ")",
            "- [Skills](" + link("skills/index.md") + ")",
            "- [Prompts](" + link("prompts/index.md") + ")",
            "- [Tools](" + link("tools/index.md") + ")",
            "- [MCP](" + link("mcp/index.md") + ")",
            "- [Graphs](" + link("graphs/index.md") + ")",
            "- [Loops](" + link("runtime/index.md") + ")",
            "- [Sandboxes](" + link("runtime/sandboxes/index.md") + ")",
            "- [Hyperscaler](" + link("runtime/hyperscaler/index.md") + ")",
            "- [Orchestration](" + link("patterns/index.md") + ")",
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
        fw_index.append(f"- [{fw}]({link(rel)})")
    if not frameworks:
        fw_index.append("- (none detected)")
    _write(out_dir / "frameworks/index.md", "\n".join(fw_index))
    created.append("frameworks/index.md")

    def _ager_type(item: dict, default: str) -> str:
        role = str(item.get("role") or "").strip()
        if role in AGER_TYPES:
            return role
        maps = str(item.get("maps_to") or "").strip()
        if maps in AGER_TYPES:
            return maps
        return default

    def _emit_kind(
        kind: str,
        folder: str,
        concept_type: str,
        maps_default: str,
        index_title: str,
        skip=None,
    ) -> None:
        items = [i for i in groups.get(kind, []) if not (skip and skip(i))]
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

        used_slugs: set[str] = set()
        for idx, item in enumerate(items[:40], start=1):
            base = _slug(str(item.get("name") or item["title"]))
            slug = base if base not in used_slugs else _slug(f"{idx}-{item['title']}")
            used_slugs.add(slug)
            rel = f"{folder}/{slug}.md"
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else source_root
            item_type = _ager_type(item, concept_type)
            tags = ["reverse-engineered", kind]
            if item.get("host"):
                tags.append(str(item["host"]))
            evidence_paths = item.get("evidence_paths") or []
            body = [
                _frontmatter(
                    type=item_type,
                    title=item["title"][:120],
                    description=item.get("excerpt", "")[:240] or item["title"],
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=tags,
                    framework=item.get("framework"),
                    confidence=item.get("confidence"),
                    evidence_path=item.get("path"),
                    evidence_line=item.get("line"),
                    evidence_paths=evidence_paths or None,
                    maps_to_ager=item.get("maps_to") or maps_default,
                    host=item.get("host"),
                    plugin=item.get("plugin"),
                    tools=item.get("tools") or None,
                    links=[
                        {"target": link("discoveries/index.md"), "rel": "derived_from"},
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
            ]
            if evidence_paths:
                body.extend(["## Evidence paths", ""])
                body.extend(f"- `{path}`" for path in evidence_paths)
                body.append("")
            body.extend(
                [
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
            )
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            index_lines.append(f"- [{item['title'][:80]}]({link(rel)}) — `{loc}`")
        if len(items) > 40:
            index_lines.append(f"- … {len(items) - 40} additional findings omitted; see discoveries")
        _write(out_dir / folder / "index.md", "\n".join(index_lines))
        created.append(f"{folder}/index.md")

    def _emit_plugin_roles() -> dict[str, str]:
        """Write typed Agent / Tool / AgentGraph concepts for plugin surfaces."""
        agent_paths: dict[str, str] = {}
        findings = scan.get("findings", [])
        role_items = [
            item
            for item in findings
            if item.get("kind") in {"agent", "skill"}
            and _ager_type(item, "") in AGER_TYPES
        ]
        skill_items = [
            item
            for item in findings
            if item.get("kind") == "skill" and _ager_type(item, "Reference") not in AGER_TYPES
        ]
        plugin_tools = [
            item for item in findings if item.get("kind") == "tool" and item.get("plugin")
        ]
        graphs = [
            item
            for item in findings
            if item.get("kind") == "graph" and item.get("plugin") and _ager_type(item, "") == "AgentGraph"
        ]

        agent_index = [
            _frontmatter(
                type="Reference",
                title="Agents",
                description="Plugin subagents and skills mapped to AGER agent nouns",
                ager_version=AGER_VERSION,
                status="draft",
                timestamp=timestamp,
                author=author,
                tags=["reverse-engineered", "agent", "plugin"],
            ),
            "",
            "# Agents",
            "",
        ]
        if not role_items:
            agent_index.append("- (none)")
        seen_names: set[str] = set()
        for item in role_items:
            name = str(item.get("name") or item["title"])
            key = f"{item.get('plugin') or ''}:{name}".lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            slug = _slug(name)
            rel = f"agents/{slug}.md"
            concept = _ager_type(item, "WorkerAgent")
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else source_root
            tool_names = [t for t in (item.get("tools") or []) if t]
            links = [{"target": link("discoveries/index.md"), "rel": "derived_from"}]
            for tool_name in tool_names:
                links.append({"target": link(f"tools/{_slug(tool_name)}.md"), "rel": "uses"})
            body = [
                _frontmatter(
                    type=concept,
                    title=name,
                    description=item.get("excerpt", "")[:240] or name,
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["reverse-engineered", "plugin", concept, item.get("host") or "plugin"],
                    framework=item.get("framework"),
                    host=item.get("host"),
                    plugin=item.get("plugin"),
                    confidence=item.get("confidence"),
                    evidence_path=item.get("path"),
                    evidence_line=item.get("line"),
                    maps_to_ager=concept,
                    tools=tool_names or None,
                    links=links,
                ),
                "",
                f"# {name}",
                "",
                f"- **AGER type:** `{concept}`",
                f"- **Host:** `{item.get('host') or 'plugin'}`",
                f"- **Plugin:** `{item.get('plugin') or ''}`",
                f"- **Tools:** {', '.join(f'`{t}`' for t in tool_names) or '(none declared)'}",
                f"- **Evidence:** `{loc}`",
                "",
                "## Excerpt",
                "",
                "```text",
                (item.get("excerpt") or "")[:500],
                "```",
            ]
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            agent_paths[name] = link(rel)
            agent_index.append(f"- [{name}]({link(rel)}) — `{concept}` (`{loc}`)")
        _write(out_dir / "agents/index.md", "\n".join(agent_index))
        created.append("agents/index.md")

        skill_index = [
            _frontmatter(
                type="Reference",
                title="Skills",
                description="Plugin SKILL.md files that are not themselves AGER agent roles",
                ager_version=AGER_VERSION,
                status="draft",
                timestamp=timestamp,
                author=author,
                tags=["reverse-engineered", "skill", "plugin"],
            ),
            "",
            "# Skills",
            "",
        ]
        if not skill_items:
            skill_index.append("- (none)")
        for item in skill_items:
            name = str(item.get("name") or item["title"])
            slug = _slug(name)
            rel = f"skills/{slug}.md"
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else source_root
            body = [
                _frontmatter(
                    type="Reference",
                    title=name,
                    description=item.get("excerpt", "")[:240] or name,
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["reverse-engineered", "skill"],
                    framework=item.get("framework"),
                    host=item.get("host"),
                    plugin=item.get("plugin"),
                    evidence_path=item.get("path"),
                    maps_to_ager=item.get("maps_to") or "Skill / Prompt",
                    links=[{"target": link("discoveries/index.md"), "rel": "derived_from"}],
                ),
                "",
                f"# {name}",
                "",
                f"- **Evidence:** `{loc}`",
                "",
                "```text",
                (item.get("excerpt") or "")[:500],
                "```",
            ]
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            skill_index.append(f"- [{name}]({link(rel)}) — `{loc}`")
        _write(out_dir / "skills/index.md", "\n".join(skill_index))
        created.append("skills/index.md")

        # Unique plugin-declared tools under their real names.
        seen_tools: set[str] = set()
        tool_index_extra: list[str] = []
        for item in plugin_tools:
            tool_name = str(item.get("name") or item["title"]).strip()
            slug = _slug(tool_name)
            if not tool_name or slug in seen_tools:
                continue
            seen_tools.add(slug)
            rel = f"tools/{slug}.md"
            loc = f"{item.get('path')}:{item.get('line')}" if item.get("path") else source_root
            body = [
                _frontmatter(
                    type="Tool",
                    title=tool_name,
                    description=item.get("excerpt", "")[:240] or tool_name,
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["reverse-engineered", "tool", "plugin"],
                    framework=item.get("framework"),
                    host=item.get("host"),
                    plugin=item.get("plugin"),
                    evidence_path=item.get("path"),
                    maps_to_ager="Tool",
                    links=[{"target": link("discoveries/index.md"), "rel": "derived_from"}],
                ),
                "",
                f"# {tool_name}",
                "",
                f"- **AGER type:** `Tool`",
                f"- **Evidence:** `{loc}`",
                "",
                (item.get("excerpt") or tool_name),
            ]
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            tool_index_extra.append(f"- [{tool_name}]({link(rel)}) — `{loc}`")

        graph_index_extra: list[str] = []
        for item in graphs:
            plugin = str(item.get("plugin") or item.get("name") or "plugin")
            slug = _slug(plugin)
            rel = f"graphs/{slug}.md"
            members = [
                m
                for m in role_items
                if (m.get("plugin") or "") == (item.get("plugin") or "")
                and _ager_type(m, "") in AGER_TYPES
            ]
            nodes = []
            seen_nodes: set[str] = set()
            for member in members:
                name = str(member.get("name") or member["title"])
                target = agent_paths.get(name)
                if target and target not in seen_nodes:
                    seen_nodes.add(target)
                    nodes.append(target)
            entry = next(
                (
                    agent_paths.get(str(m.get("name") or m["title"]))
                    for m in members
                    if _ager_type(m, "") == "OrchestratorAgent"
                ),
                nodes[0] if nodes else None,
            )
            links = [{"target": link("discoveries/index.md"), "rel": "derived_from"}]
            for node in nodes:
                links.append({"target": node, "rel": "contains"})
            body = [
                _frontmatter(
                    type="AgentGraph",
                    title=f"{plugin} agent graph",
                    description=item.get("excerpt", "")[:240] or plugin,
                    ager_version=AGER_VERSION,
                    status="draft",
                    timestamp=timestamp,
                    author=author,
                    tags=["reverse-engineered", "plugin", "AgentGraph"],
                    framework=item.get("framework"),
                    host=item.get("host"),
                    plugin=plugin,
                    evidence_path=item.get("path"),
                    maps_to_ager="AgentGraph",
                    entry=entry,
                    nodes=nodes or None,
                    links=links,
                ),
                "",
                f"# {plugin} agent graph",
                "",
                f"- **AGER type:** `AgentGraph`",
                f"- **Entry:** `{entry or '(none)'}`",
                f"- **Nodes:** {', '.join(f'`{n}`' for n in nodes) or '(none)'}",
                "",
                (item.get("excerpt") or ""),
            ]
            _write(out_dir / rel, "\n".join(body))
            created.append(rel)
            graph_index_extra.append(f"- [{plugin} agent graph]({link(rel)})")

        return {
            "graph_index": "\n".join(graph_index_extra),
            "tool_index": "\n".join(tool_index_extra),
        }

    plugin_extra = _emit_plugin_roles()

    _emit_kind("system_prompt", "prompts/system", "Reference", "AgentNode.instructions", "System prompts")
    _emit_kind("prompt", "prompts", "Reference", "Prompt", "Prompts")
    _emit_kind(
        "tool",
        "tools",
        "Tool",
        "Tool",
        "Tools",
        skip=lambda i: bool(i.get("plugin")),
    )
    if plugin_extra.get("tool_index"):
        tools_index = out_dir / "tools/index.md"
        if tools_index.is_file():
            existing = tools_index.read_text(encoding="utf-8")
            if "\n- (none)\n" in existing and existing.strip().endswith("- (none)"):
                existing = existing.replace("- (none)", plugin_extra["tool_index"], 1)
                tools_index.write_text(existing.rstrip() + "\n", encoding="utf-8")
            else:
                tools_index.write_text(
                    existing.rstrip() + "\n" + plugin_extra["tool_index"] + "\n",
                    encoding="utf-8",
                )
    _emit_kind("mcp", "mcp", "Reference", "Tool + JsonRpcSchema", "MCP / JSON-RPC")
    _emit_kind("schema", "schemas", "Reference", "InputSchema / OutputSchema", "Schemas")
    _emit_kind(
        "graph",
        "graphs",
        "AgentGraph",
        "AgentGraph",
        "Graphs",
        skip=lambda i: bool(i.get("plugin") and _ager_type(i, "") == "AgentGraph"),
    )
    if plugin_extra.get("graph_index"):
        graphs_index = out_dir / "graphs/index.md"
        if graphs_index.is_file():
            graphs_index.write_text(
                graphs_index.read_text(encoding="utf-8").rstrip()
                + "\n"
                + plugin_extra["graph_index"]
                + "\n",
                encoding="utf-8",
            )
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
                "- [Loop controls](" + link("runtime/loops/index.md") + ")",
                "- [Sandboxes / microVMs](" + link("runtime/sandboxes/index.md") + ")",
                "- [Hyperscaler runtimes](" + link("runtime/hyperscaler/index.md") + ")",
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
                "- [System prompts](" + link("prompts/system/index.md") + ")",
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
    parser.add_argument(
        "--bundle-root",
        type=Path,
        default=None,
        help="OKF bundle root when --out is a nested subtree (prefixes links)",
    )
    parser.add_argument(
        "--link-prefix",
        default="",
        help="Explicit link prefix (e.g. agent-graph). Overrides --bundle-root.",
    )
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
        bundle_root=args.bundle_root,
        link_prefix=args.link_prefix or None,
    )
    print(json.dumps(report, indent=2) if args.json else f"Wrote draft AGER bundle → {report['out_dir']} ({len(report['files_written'])} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
