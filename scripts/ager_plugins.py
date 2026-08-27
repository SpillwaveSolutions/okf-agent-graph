#!/usr/bin/env python3
"""Discover Claude / Grok / Codex / universal agent plugins as first-class AGER sources.

Plugin surfaces are YAML-frontmatter markdown (subagents + SKILL.md) and plugin.json
manifests — not SDK imports. This pass runs before the generic keyword scan so those
files become Agent / Tool / AgentGraph findings instead of orchestrator-word noise.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "coverage",
    ".next",
    "target",
    "vendor",
    ".work",
}

SKIP_AGENT_NAMES = {"readme.md", "index.md", "changelog.md", "license.md"}

# Claude Code write tools (and close cousins on other hosts).
WRITE_TOOLS = {
    "write",
    "edit",
    "multiedit",
    "notebookedit",
    "writefile",
    "strreplace",
    "apply_patch",
    "create_file",
    "delete",
    "delete_file",
}

PLUGIN_META_DIRS = {
    ".claude-plugin": ("claude-code", "claude-code-plugin"),
    ".codex-plugin": ("codex", "codex-plugin"),
    ".grok-plugin": ("grok-build", "grok-plugin"),
    ".cursor-plugin": ("cursor", "cursor-plugin"),
}

# Project-local host folders, dotted and undotted, at any depth.
HOST_DIR_NAMES: dict[str, tuple[str, str]] = {
    ".claude": ("claude-code", "claude-code-plugin"),
    "claude": ("claude-code", "claude-code-plugin"),
    ".grok": ("grok-build", "grok-plugin"),
    "grok": ("grok-build", "grok-plugin"),
    ".codex": ("codex", "codex-plugin"),
    "codex": ("codex", "codex-plugin"),
    ".cursor": ("cursor", "cursor-plugin"),
    "cursor": ("cursor", "cursor-plugin"),
}

MANIFEST_NAMES = {"plugin.json", "marketplace.json"}

SKILL_SKIP_PARTS = {"references", "scripts", "assets", "templates", "examples"}

ORCHESTRATOR_PHRASES = (
    "you are the orchestrator",
    "you are the only role",
    "the only role in this loop that writes",
    "only role in this loop that writes",
    "you are the supervisor",
)

JUDGE_PHRASES = (
    "never writes",
    "never grades its own",
    "does not write",
    "holds no write",
    "no write tool",
    "you are the judge",
    "you are a judge",
    "scores candidates",
    "against a rubric",
)


@dataclass
class PluginFinding:
    kind: str
    title: str
    evidence: str
    excerpt: str
    confidence: float
    maps_to: str
    framework: str | None = None
    path: str | None = None
    line: int | None = None
    name: str | None = None
    role: str | None = None
    tools: list[str] = field(default_factory=list)
    host: str | None = None
    plugin: str | None = None


@dataclass
class PluginScan:
    findings: list[PluginFinding] = field(default_factory=list)
    frameworks: set[str] = field(default_factory=set)
    consumed_paths: set[str] = field(default_factory=set)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML-ish markdown frontmatter without PyYAML."""
    if not text.startswith("---"):
        return {}, text
    rest = text[3:]
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    match = re.search(r"\n---\s*(?:\n|$)", rest)
    if not match:
        return {}, text
    block = rest[: match.start()]
    body = rest[match.end() :]
    return _parse_simple_yaml(block), body


def classify_agent_role(
    *,
    name: str,
    description: str,
    body: str,
    tools: list[str],
    kind: str,
) -> str:
    """Map a plugin subagent or skill onto an AGER agent noun."""
    blob = f"{name}\n{description}\n{body}".lower()
    namel = name.lower()
    toolset = {_tool_key(t) for t in tools}
    has_write = any(t in WRITE_TOOLS or "write" in t for t in toolset)

    if _is_orchestrator(namel, blob, kind):
        return "OrchestratorAgent"

    judge_named = any(token in namel for token in ("judge", "critic", "evaluator"))
    judge_prose = any(phrase in blob for phrase in JUDGE_PHRASES) or "judge" in blob
    if not has_write and (judge_named or judge_prose):
        # Issue #14: Judge only when write tools are omitted *and* the text says so.
        if judge_named or any(
            phrase in blob
            for phrase in (
                "never writes",
                "never grades its own",
                "you are the judge",
                "you are a judge",
                "scores candidates",
            )
        ):
            return "JudgeAgent"

    if kind == "skill":
        return "Skill"
    return "WorkerAgent"


def scan_plugin_surfaces(root: Path) -> PluginScan:
    root = root.resolve()
    result = PluginScan()
    seen_files: set[Path] = set()

    for manifest in _iter_manifests(root):
        _ingest_manifest(root, manifest, result, seen_files)

    for host_dir, host, framework in _iter_host_dirs(root):
        result.frameworks.add(framework)
        plugin_name = host_dir.parent.name if host_dir.parent != root else host_dir.name
        _ingest_agent_dir(
            root,
            host_dir / "agents",
            result,
            seen_files,
            host=host,
            framework=framework,
            plugin=plugin_name,
        )
        _ingest_skill_dir(
            root,
            host_dir / "skills",
            result,
            seen_files,
            host=host,
            framework=framework,
            plugin=plugin_name,
        )

    _emit_cluster_graphs(result)
    return result


def _tool_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _is_orchestrator(namel: str, blob: str, kind: str) -> bool:
    if any(token in namel for token in ("orchestrator", "supervisor", "conductor")):
        return True
    if any(phrase in blob for phrase in ORCHESTRATOR_PHRASES):
        return True
    if kind == "skill" and "orchestrator" in blob and "only role" in blob:
        return True
    return False


def _coerce_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(part) for part in _split_csv(inner)]
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _split_csv(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_quote = False
    quote = ""
    for char in text:
        if in_quote:
            current.append(char)
            if char == quote:
                in_quote = False
            continue
        if char in {'"', "'"}:
            in_quote = True
            quote = char
            current.append(char)
            continue
        if char == ",":
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current or parts:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _parse_simple_yaml(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: list[Any] | None = None
    current_key: str | None = None
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        list_item = re.match(r"^(\s+)-\s+(.*)$", raw)
        if list_item and current_list is not None:
            current_list.append(_coerce_scalar(list_item.group(2)))
            continue
        current_list = None
        if ":" not in raw:
            continue
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in {"", "|", ">", ">-", "|-"}:
            current_key = key
            current_list = []
            data[key] = current_list
            continue
        value = _coerce_scalar(rest)
        if key in {"tools", "allowed-tools", "allowed_tools"} and isinstance(value, str) and "," in value:
            value = [_coerce_scalar(part) for part in _split_csv(value)]
        data[key] = value
        current_key = key
    if current_key and current_list == []:
        # Empty nested value: keep as empty string rather than an unused list
        # unless the key is a known list field.
        if current_key not in {"tools", "allowed-tools", "allowed_tools", "tags", "keywords"}:
            data[current_key] = ""
    return data


def _skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif item is not None and str(item).strip():
                out.append(str(item).strip())
        return out
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "," in text:
            return [part.strip() for part in _split_csv(text) if part.strip()]
        return [text]
    return [str(value)]


def _tools_of(meta: dict[str, Any]) -> list[str]:
    for key in ("tools", "allowed-tools", "allowed_tools"):
        if key in meta:
            return _as_str_list(meta.get(key))
    return []


def _iter_manifests(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or _skipped(path):
            continue
        if path.name in MANIFEST_NAMES:
            found.append(path)
    return found


def _iter_host_dirs(root: Path) -> list[tuple[Path, str, str]]:
    found: list[tuple[Path, str, str]] = []
    seen: set[Path] = set()
    for path in root.rglob("*"):
        if not path.is_dir() or _skipped(path):
            continue
        spec = HOST_DIR_NAMES.get(path.name)
        if not spec:
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        # A host dir is interesting when it actually holds agents or skills.
        if not (path / "agents").is_dir() and not (path / "skills").is_dir():
            continue
        seen.add(resolved)
        host, framework = spec
        found.append((path, host, framework))
    return found


def _looks_like_agent_plugin(data: dict[str, Any], plugin_root: Path, manifest: Path) -> bool:
    schema = str(data.get("$schema") or "")
    if "agent-plugins.org" in schema:
        return True
    if manifest.parent.name in PLUGIN_META_DIRS:
        return bool(data.get("name") or data.get("plugins"))
    if data.get("skills") or data.get("agents"):
        return True
    if data.get("name") and (
        (plugin_root / "skills").is_dir() or (plugin_root / "agents").is_dir()
    ):
        return True
    plugins = data.get("plugins")
    if isinstance(plugins, list) and plugins:
        return True
    return False


def _plugin_root_for(manifest: Path) -> Path:
    if manifest.parent.name in PLUGIN_META_DIRS:
        return manifest.parent.parent
    return manifest.parent


def _host_for_manifest(manifest: Path, data: dict[str, Any]) -> tuple[str, str]:
    meta = PLUGIN_META_DIRS.get(manifest.parent.name)
    if meta:
        return meta
    schema = str(data.get("$schema") or "")
    if "agent-plugins.org" in schema:
        return "universal", "agent-plugins"
    return "universal", "agent-plugins"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _ingest_manifest(
    root: Path,
    manifest: Path,
    result: PluginScan,
    seen_files: set[Path],
) -> None:
    data = _load_json(manifest)
    if not data:
        return
    plugin_root = _plugin_root_for(manifest)
    if not _looks_like_agent_plugin(data, plugin_root, manifest):
        return

    host, framework = _host_for_manifest(manifest, data)
    result.frameworks.add(framework)
    rel = _rel(root, manifest)
    result.consumed_paths.add(rel)

    plugin_name = str(data.get("name") or plugin_root.name)
    plugins = data.get("plugins")
    if not data.get("name") and isinstance(plugins, list) and plugins:
        first = plugins[0] if isinstance(plugins[0], dict) else {}
        plugin_name = str(first.get("name") or plugin_name)

    excerpt = str(data.get("description") or plugin_name)[:240]
    result.findings.append(
        PluginFinding(
            kind="plugin",
            title=plugin_name,
            evidence=manifest.name,
            excerpt=excerpt,
            confidence=0.96,
            maps_to="Harness + AgentGraph",
            framework=framework,
            path=rel,
            line=1,
            name=plugin_name,
            host=host,
            plugin=plugin_name,
        )
    )

    _ingest_agent_dir(
        root,
        plugin_root / "agents",
        result,
        seen_files,
        host=host,
        framework=framework,
        plugin=plugin_name,
    )
    _ingest_skill_dir(
        root,
        plugin_root / "skills",
        result,
        seen_files,
        host=host,
        framework=framework,
        plugin=plugin_name,
    )

    for key in ("agents", "skills"):
        for declared in _as_str_list(data.get(key)):
            target = (plugin_root / declared).resolve()
            if target.is_file() and target.name == "SKILL.md":
                _ingest_skill_file(
                    root, target, result, seen_files, host, framework, plugin_name
                )
            elif target.is_dir() and (target / "SKILL.md").is_file():
                _ingest_skill_file(
                    root,
                    target / "SKILL.md",
                    result,
                    seen_files,
                    host,
                    framework,
                    plugin_name,
                )
            elif target.is_dir() and key == "skills":
                _ingest_skill_dir(
                    root, target, result, seen_files, host, framework, plugin_name
                )
            elif target.is_dir() and key == "agents":
                _ingest_agent_dir(
                    root, target, result, seen_files, host, framework, plugin_name
                )
            elif target.is_file() and target.suffix.lower() == ".md":
                _ingest_agent_file(
                    root, target, result, seen_files, host, framework, plugin_name
                )

    if isinstance(plugins, list):
        for entry in plugins:
            if not isinstance(entry, dict):
                continue
            source = str(entry.get("source") or "").strip()
            if not source or source in {".", "./"}:
                continue
            child = (plugin_root / source).resolve()
            if (child / "plugin.json").is_file():
                _ingest_manifest(root, child / "plugin.json", result, seen_files)
            else:
                child_name = str(entry.get("name") or child.name)
                _ingest_agent_dir(
                    root, child / "agents", result, seen_files, host, framework, child_name
                )
                _ingest_skill_dir(
                    root, child / "skills", result, seen_files, host, framework, child_name
                )


def _ingest_agent_dir(
    root: Path,
    agents_dir: Path,
    result: PluginScan,
    seen_files: set[Path],
    host: str,
    framework: str,
    plugin: str,
) -> None:
    if not agents_dir.is_dir():
        return
    for path in sorted(agents_dir.iterdir()):
        if path.is_file() and path.suffix.lower() == ".md":
            _ingest_agent_file(root, path, result, seen_files, host, framework, plugin)


def _ingest_skill_dir(
    root: Path,
    skills_dir: Path,
    result: PluginScan,
    seen_files: set[Path],
    host: str,
    framework: str,
    plugin: str,
) -> None:
    if not skills_dir.is_dir():
        return
    for path in sorted(skills_dir.rglob("SKILL.md")):
        rel_parts = path.relative_to(skills_dir).parts
        if any(part.lower() in SKILL_SKIP_PARTS for part in rel_parts[:-1]):
            continue
        _ingest_skill_file(root, path, result, seen_files, host, framework, plugin)


def _ingest_agent_file(
    root: Path,
    path: Path,
    result: PluginScan,
    seen_files: set[Path],
    host: str,
    framework: str,
    plugin: str,
) -> None:
    if path.resolve() in seen_files:
        return
    if path.name.lower() in SKIP_AGENT_NAMES:
        return
    seen_files.add(path.resolve())
    _ingest_markdown(
        root,
        path,
        result,
        host=host,
        framework=framework,
        plugin=plugin,
        kind="agent",
    )


def _ingest_skill_file(
    root: Path,
    path: Path,
    result: PluginScan,
    seen_files: set[Path],
    host: str,
    framework: str,
    plugin: str,
) -> None:
    if path.resolve() in seen_files:
        return
    seen_files.add(path.resolve())
    _ingest_markdown(
        root,
        path,
        result,
        host=host,
        framework=framework,
        plugin=plugin,
        kind="skill",
    )


def _ingest_markdown(
    root: Path,
    path: Path,
    result: PluginScan,
    *,
    host: str,
    framework: str,
    plugin: str,
    kind: str,
) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    rel = _rel(root, path)
    result.consumed_paths.add(rel)
    meta, body = parse_frontmatter(text)
    name = str(meta.get("name") or path.parent.name if kind == "skill" else path.stem)
    description = str(meta.get("description") or "").strip()
    tools = _tools_of(meta)
    role = classify_agent_role(
        name=name,
        description=description,
        body=body,
        tools=tools,
        kind=kind,
    )
    maps_to = role if role != "Skill" else "Skill / Prompt"
    excerpt = (description or body).replace("\n", " ").strip()[:240]
    title = name
    result.findings.append(
        PluginFinding(
            kind=kind,
            title=title,
            evidence="frontmatter",
            excerpt=excerpt or title,
            confidence=0.95,
            maps_to=maps_to,
            framework=framework,
            path=rel,
            line=1,
            name=name,
            role=role,
            tools=tools,
            host=host,
            plugin=plugin,
        )
    )
    for tool_name in tools:
        result.findings.append(
            PluginFinding(
                kind="tool",
                title=tool_name,
                evidence=f"frontmatter tools of {name}",
                excerpt=f"{name} declares tool {tool_name}",
                confidence=0.94,
                maps_to="Tool",
                framework=framework,
                path=rel,
                line=1,
                name=tool_name,
                tools=[tool_name],
                host=host,
                plugin=plugin,
            )
        )


def _emit_cluster_graphs(result: PluginScan) -> None:
    clusters: dict[str, list[PluginFinding]] = {}
    for finding in result.findings:
        if finding.kind not in {"agent", "skill"}:
            continue
        if finding.maps_to in {"Skill / Prompt", "Skill"}:
            continue
        key = finding.plugin or finding.host or "plugin"
        clusters.setdefault(key, []).append(finding)
    for plugin, members in clusters.items():
        if not members:
            continue
        roles = sorted({m.role or m.maps_to for m in members})
        names = [m.name or m.title for m in members]
        entry = next(
            (m for m in members if (m.role or m.maps_to) == "OrchestratorAgent"),
            members[0],
        )
        result.findings.append(
            PluginFinding(
                kind="graph",
                title=f"{plugin} agent graph",
                evidence="plugin agent/skill cluster",
                excerpt=f"Roles: {', '.join(roles)}. Nodes: {', '.join(names)}.",
                confidence=0.93,
                maps_to="AgentGraph",
                framework=entry.framework,
                path=entry.path,
                line=1,
                name=plugin,
                role="AgentGraph",
                tools=[],
                host=entry.host,
                plugin=plugin,
            )
        )
