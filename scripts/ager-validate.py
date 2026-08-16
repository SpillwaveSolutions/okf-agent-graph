#!/usr/bin/env python3
"""Deterministic, dependency-free structural validation for AGER bundles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_VERSION = "0.3.0"
AGER_TYPES = {
    "AgentNode", "OrchestratorAgent", "WorkerAgent", "JudgeAgent",
    "SynthesizerAgent", "RouterAgent", "GuardrailAgent", "HumanGate",
    "AgentGraph", "AgentGraphModule", "FanOut", "FanIn", "ParallelGroup",
    "ControlEdge", "InputSchema", "OutputSchema", "LoopPolicy", "LoopControl",
    "ScratchPad", "LineageRecord", "EpisodeStore", "KnowledgeBind",
    "RetrievalBinding", "SharedChannel", "MemoryArtifact",
    "ContextIsolationPolicy", "Tool", "ToolRule", "SecretRef", "RateLimit",
    "ConcurrencyLimit", "Run", "Trigger", "FailurePolicy", "RetryPolicy",
    "Compensation", "CircuitBreaker", "DeadLetter", "DataClassPolicy",
    "CheckpointPolicy", "RunTrace", "StreamPolicy", "HandoffPolicy", "Rubric",
    "Criterion", "Judgment", "EvalSuite",
}
AGENT_TYPES = {
    "AgentNode", "OrchestratorAgent", "WorkerAgent", "JudgeAgent",
    "SynthesizerAgent", "RouterAgent", "GuardrailAgent",
}
PATH_KEYS = {
    "entry", "input_schema", "output_schema", "state_schema", "instructions",
    "loop_policy", "scratchpad", "failure_policy", "retry_policy",
    "compensation", "target", "knowledge",
}
PATH_LIST_KEYS = {"nodes", "rubrics", "worker_pool", "judge_pool", "retrievals"}
CONTROL_TYPES = {"goal", "deadline", "price_budget", "max_turns", "no_progress"}
SECRET_KEY = re.compile(r"(?:secret|password|token|api[_-]?key)", re.I)


@dataclass
class Document:
    path: Path
    rel: str
    block: str
    values: dict[str, str]
    sections: dict[str, list[str]]


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_document(path: Path, bundle: Path) -> Document | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    block = text[4:end]
    values: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            current = key.strip()
            values[current] = _unquote(value)
            sections[current] = []
        elif current is not None:
            sections[current].append(stripped)
    return Document(path, path.relative_to(bundle).as_posix(), block, values, sections)


def _issue(issues: list[dict[str, str]], severity: str, doc: Document | None, message: str) -> None:
    issues.append({"severity": severity, "path": doc.rel if doc else "index.md", "message": message})


def _section_items(doc: Document, key: str) -> list[str]:
    items: list[str] = []
    for line in doc.sections.get(key, []):
        if line.startswith("- "):
            value = line[2:].strip()
            if ":" not in value:
                items.append(_unquote(value))
    return items


def _section_value(doc: Document, section: str, key: str) -> str:
    for line in doc.sections.get(section, []):
        if line.startswith(f"{key}:"):
            return _unquote(line.split(":", 1)[1])
    return ""


def _reference_values(doc: Document) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for raw in doc.block.splitlines():
        stripped = raw.strip()
        if ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            value = _unquote(value)
            if key.strip() in PATH_KEYS and value.startswith("/"):
                refs.append((key.strip(), value))
    for key in PATH_LIST_KEYS:
        refs.extend((key, value) for value in _section_items(doc, key) if value.startswith("/"))
    return refs


def _validate_reference(bundle: Path, doc: Document, key: str, value: str, issues: list[dict[str, str]]) -> None:
    target = (bundle / value.lstrip("/")).resolve()
    try:
        target.relative_to(bundle.resolve())
    except ValueError:
        _issue(issues, "error", doc, f"{key} escapes bundle: {value}")
        return
    if not target.is_file():
        _issue(issues, "error", doc, f"{key} target does not exist: {value}")
        return
    if target.suffix == ".json":
        try:
            json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _issue(issues, "error", doc, f"invalid JSON schema {value}: {exc}")


def validate(bundle: Path, strict: bool = False) -> dict[str, object]:
    bundle = bundle.resolve()
    issues: list[dict[str, str]] = []
    documents: list[Document] = []
    if not (bundle / "index.md").is_file():
        issues.append({"severity": "error", "path": "index.md", "message": "bundle index.md is missing"})
    for path in sorted(bundle.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(bundle).parts):
            continue
        doc = parse_document(path, bundle)
        if doc is None:
            if path.relative_to(bundle).as_posix() == "log.md":
                continue
            issues.append({"severity": "warn", "path": path.relative_to(bundle).as_posix(), "message": "missing or malformed frontmatter"})
            continue
        documents.append(doc)

    root = next((doc for doc in documents if doc.rel == "index.md"), None)
    if root:
        if root.values.get("okf_version") != "0.2":
            _issue(issues, "error", root, 'bundle requires okf_version: "0.2"')
        if root.values.get("ager_version") != SUPPORTED_VERSION:
            _issue(issues, "error", root, f'bundle requires ager_version: "{SUPPORTED_VERSION}"')

    for doc in documents:
        if "{{" in doc.path.read_text(encoding="utf-8"):
            _issue(issues, "error", doc, "unresolved scaffold placeholder")
        concept_type = doc.values.get("type", "")
        version = doc.values.get("ager_version", "")
        if version and concept_type not in AGER_TYPES | {"Reference", "WriteEvent"}:
            _issue(issues, "error", doc, f"unknown AGER type: {concept_type or '<missing>'}")
        if concept_type in AGER_TYPES and version != SUPPORTED_VERSION:
            _issue(issues, "error", doc, f'{concept_type} requires ager_version: "{SUPPORTED_VERSION}"')

        if concept_type in AGENT_TYPES:
            for key in ("input_schema", "output_schema"):
                if not doc.values.get(key) and not doc.sections.get(key):
                    _issue(issues, "error", doc, f"{concept_type} missing {key}")
        if concept_type == "AgentGraph":
            for key in ("entry", "nodes", "state_schema", "loop_policy", "scratchpad", "failure_policy"):
                if not doc.values.get(key) and not doc.sections.get(key):
                    _issue(issues, "error", doc, f"AgentGraph missing {key}")
        if concept_type == "LoopPolicy":
            found = {
                match.group(1)
                for line in doc.sections.get("controls", [])
                if (match := re.match(r"-\s+type:\s*([A-Za-z0-9_-]+)", line))
            }
            if not found:
                _issue(issues, "error", doc, "LoopPolicy has no controls")
            for missing in sorted(CONTROL_TYPES - found):
                _issue(issues, "warn", doc, f"LoopPolicy missing recommended {missing} control")
            for key in ("on_exhaust", "on_goal"):
                if not doc.values.get(key):
                    _issue(issues, "error", doc, f"LoopPolicy missing {key}")
        if concept_type in {"WorkerAgent", "JudgeAgent"}:
            if _section_value(doc, "record_output_to", "mode") != "append":
                _issue(issues, "error", doc, f"{concept_type} record_output_to.mode must be append")
        if concept_type == "Tool" and doc.values.get("side_effects") == "irreversible":
            guarded = doc.values.get("dual_control", "").lower() == "true"
            guarded = guarded or bool(doc.values.get("compensation"))
            guarded = guarded or any("action: require_human" in line for line in doc.sections.get("rules", []))
            if not guarded:
                _issue(issues, "error", doc, "irreversible Tool requires dual_control, compensation, or require_human rule")

        for raw in doc.block.splitlines():
            stripped = raw.strip()
            if ":" not in stripped or stripped.startswith("-"):
                continue
            key, value = stripped.split(":", 1)
            value = _unquote(value)
            if SECRET_KEY.search(key) and value and not value.startswith(("/", "${")):
                _issue(issues, "error", doc, f"inline secret-like value in {key.strip()}; use SecretRef")

        for key, value in _reference_values(doc):
            _validate_reference(bundle, doc, key, value, issues)

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warn" for issue in issues)
    return {
        "bundle": str(bundle),
        "ager_version": SUPPORTED_VERSION,
        "document_count": len(documents),
        "issues": issues,
        "error_count": errors,
        "warn_count": warnings,
        "strict": strict,
        "valid": errors == 0 and (not strict or warnings == 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    result = validate(args.bundle, args.strict)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
