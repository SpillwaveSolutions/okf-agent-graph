#!/usr/bin/env python3
"""Scan a codebase for agent frameworks and extract AGER-relevant findings.

Reverse-engineering counterpart to forward authoring (ager-init / ager-author).
Mirrors system-architecture-capture / data-engineering-knowledge-capture scanners,
but for agent graphs: prompts, MCP/JSON-RPC tools, orchestration, loops, harnesses,
hyperscaler runtimes, and hardened microVM/container sandboxes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

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
}

SCAN_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
    ".txt",
    ".tf",
    ".sh",
}

MAX_FILE_BYTES = 512_000


@dataclass
class Finding:
    kind: str
    title: str
    evidence: str
    excerpt: str
    confidence: float
    maps_to: str
    framework: str | None = None
    path: str | None = None
    line: int | None = None


@dataclass
class ScanResult:
    root: str
    frameworks: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    summary: dict[str, int] = field(default_factory=dict)


FRAMEWORK_DETECTORS: list[dict] = [
    {
        "framework": "langgraph",
        "patterns": [
            r"from\s+langgraph",
            r"StateGraph\s*\(",
            r"add_conditional_edges",
            r"langgraph\.prebuilt",
            r"@langchain/langgraph",
        ],
        "maps_to": "AgentGraph + ControlEdge + LoopControl",
    },
    {
        "framework": "langchain",
        "patterns": [
            r"from\s+langchain",
            r"ChatPromptTemplate",
            r"create_react_agent",
            r"@langchain/core",
            r"langchain_core",
        ],
        "maps_to": "AgentNode + Tool + Prompt",
    },
    {
        "framework": "crewai",
        "patterns": [
            r"from\s+crewai",
            r"Crew\s*\(",
            r"Agent\s*\(\s*role\s*=",
            r"Process\.hierarchical",
            r"crewai\.process",
        ],
        "maps_to": "OrchestratorAgent + WorkerAgent + Process",
    },
    {
        "framework": "llamaindex",
        "patterns": [
            r"from\s+llama_index",
            r"llama_index\.core",
            r"AgentWorkflow",
            r"FunctionAgent",
            r"@llamaindex/",
        ],
        "maps_to": "AgentNode + Workflow + RetrievalBinding",
    },
    {
        "framework": "openai-agents",
        "patterns": [
            r"from\s+agents\s+import",
            r"openai\.agents",
            r"@openai/agents",
            r"Runner\.run",
            r"handoffs\s*=",
        ],
        "maps_to": "AgentNode + HandoffPolicy + Runner",
    },
    {
        "framework": "openai-api",
        "patterns": [
            r"from\s+openai\s+import",
            r"OpenAI\s*\(",
            r"chat\.completions\.create",
            r"responses\.create",
            r"openai\.ChatCompletion",
        ],
        "maps_to": "AgentNode + SystemPrompt + Tool",
    },
    {
        "framework": "anthropic-sdk",
        "patterns": [
            r"anthropic\.messages",
            r"from\s+anthropic",
            r"@anthropic-ai/sdk",
            r"claude-.*-(?:sonnet|opus|haiku)",
            r"messages\.create",
            r"tool_use",
        ],
        "maps_to": "AgentNode + Tool + SystemPrompt",
    },
    {
        "framework": "claude-agent-sdk",
        "patterns": [
            r"@anthropic-ai/claude-agent",
            r"claude_agent_sdk",
            r"ClaudeSDKClient",
            r"claude-code.*agent",
        ],
        "maps_to": "Harness + AgentNode + ToolRule",
    },
    {
        "framework": "deepagents",
        "patterns": [
            r"deepagents",
            r"DeepAgent",
            r"create_deep_agent",
            r"from\s+deepagents",
        ],
        "maps_to": "OrchestratorAgent + Subagent + ScratchPad",
    },
    {
        "framework": "autogen",
        "patterns": [
            r"from\s+autogen",
            r"AssistantAgent",
            r"UserProxyAgent",
            r"GroupChat",
            r"autogen_agentchat",
        ],
        "maps_to": "AgentNode + GroupChat + LoopControl",
    },
    {
        "framework": "semantic-kernel",
        "patterns": [
            r"semantic_kernel",
            r"SemanticKernel",
            r"Kernel\.CreateBuilder",
            r"Microsoft\.SemanticKernel",
        ],
        "maps_to": "AgentNode + Plugin/Tool + Planner",
    },
    {
        "framework": "mcp",
        "patterns": [
            r"@modelcontextprotocol",
            r"mcp\.server",
            r"McpServer",
            r"list_tools",
            r"CallToolRequest",
            r'"jsonrpc"\s*:\s*"2\.0"',
            r"mcpServers",
        ],
        "maps_to": "Tool + JsonRpcSchema + SecretRef",
    },
    {
        "framework": "bedrock-agentcore",
        "patterns": [
            r"bedrock-agent-runtime",
            r"bedrock-agentcore",
            r"AgentCore",
            r"invoke_agent",
            r"aws-sdk.*bedrock-agent",
        ],
        "maps_to": "Run + CheckpointPolicy + Harness",
    },
    {
        "framework": "azure-ai-agents",
        "patterns": [
            r"azure\.ai\.agents",
            r"AzureAIAgent",
            r"AIProjectClient",
            r"azure-ai-projects",
        ],
        "maps_to": "AgentNode + Run",
    },
    {
        "framework": "vertex-agent-engine",
        "patterns": [
            r"vertexai\.agent",
            r"AgentEngine",
            r"google\.cloud\.aiplatform",
            r"ReasoningEngine",
        ],
        "maps_to": "AgentNode + Run",
    },
    {
        "framework": "firecracker",
        "patterns": [
            r"firecracker",
            r"microvm",
            r"MicroVM",
            r"fc_api",
        ],
        "maps_to": "ContextIsolationPolicy + DataClassPolicy",
    },
    {
        "framework": "gvisor",
        "patterns": [
            r"gvisor",
            r"runsc",
            r"gVisor",
        ],
        "maps_to": "ContextIsolationPolicy",
    },
    {
        "framework": "kata",
        "patterns": [
            r"kata-containers",
            r"Kata Containers",
            r"kataRuntime",
        ],
        "maps_to": "ContextIsolationPolicy",
    },
    {
        "framework": "e2b",
        "patterns": [
            r"from\s+e2b",
            r"@e2b/",
            r"Sandbox\.create",
            r"e2b\.dev",
        ],
        "maps_to": "ContextIsolationPolicy + Tool",
    },
]


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _excerpt(text: str, index: int, width: int = 160) -> str:
    start = max(0, index - 40)
    end = min(len(text), index + width)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def _add(
    findings: list[Finding],
    *,
    kind: str,
    title: str,
    evidence: str,
    excerpt: str,
    confidence: float,
    maps_to: str,
    framework: str | None = None,
    path: str | None = None,
    line: int | None = None,
) -> None:
    findings.append(
        Finding(
            kind=kind,
            title=title,
            evidence=evidence,
            excerpt=excerpt[:300],
            confidence=confidence,
            maps_to=maps_to,
            framework=framework,
            path=path,
            line=line,
        )
    )


def _scan_frameworks(text: str, rel: str, findings: list[Finding]) -> set[str]:
    found: set[str] = set()
    for detector in FRAMEWORK_DETECTORS:
        for pattern in detector["patterns"]:
            match = re.search(pattern, text, re.I | re.M)
            if match:
                fw = detector["framework"]
                found.add(fw)
                _add(
                    findings,
                    kind="framework",
                    title=f"Detected {fw}",
                    evidence=pattern,
                    excerpt=_excerpt(text, match.start()),
                    confidence=0.9,
                    maps_to=detector["maps_to"],
                    framework=fw,
                    path=rel,
                    line=_line_of(text, match.start()),
                )
                break
    return found


def _scan_prompts(text: str, rel: str, findings: list[Finding], frameworks: set[str]) -> None:
    system_patterns = [
        (r"""system\s*[:=]\s*["']([^"']{12,})["']""", "System prompt string"),
        (r"""["']system["']\s*:\s*["']([^"']{12,})["']""", "System role message"),
        (r"""system\s*=\s*["']{3}([\s\S]{12,}?)["']{3}""", "System prompt triple-quoted"),
        (r"""SYSTEM_PROMPT\s*=\s*["']([^"']{12,})["']""", "SYSTEM_PROMPT constant"),
        (r"""SYSTEM_PROMPT\s*=\s*["']{3}([\s\S]{12,}?)["']{3}""", "SYSTEM_PROMPT triple-quoted"),
        (r"""You are (?:a|an|the) [A-Za-z].{20,}""", "Inline persona system text"),
    ]
    for pattern, title in system_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            body = match.group(1) if match.lastindex else match.group(0)
            _add(
                findings,
                kind="system_prompt",
                title=title,
                evidence=pattern,
                excerpt=body[:200].replace("\n", " "),
                confidence=0.85,
                maps_to="AgentNode.instructions / Prompt",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )

    prompt_patterns = [
        (r"""ChatPromptTemplate\.from_(?:messages|template)\s*\(([\s\S]{0,200})\)""", "LangChain prompt template"),
        (r"""PromptTemplate\s*\([\s\S]{0,120}template\s*=\s*["']([^"']+)["']""", "PromptTemplate"),
        (r"""backstory\s*=\s*["']([^"']{12,})["']""", "CrewAI backstory"),
        (r"""goal\s*=\s*["']([^"']{12,})["']""", "CrewAI / agent goal"),
        (r"""instructions\s*=\s*["']([^"']{12,})["']""", "Agent instructions"),
        (r"""instructions\s*=\s*["']{3}([\s\S]{12,}?)["']{3}""", "Agent instructions block"),
    ]
    for pattern, title in prompt_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            body = match.group(1) if match.lastindex else match.group(0)
            _add(
                findings,
                kind="prompt",
                title=title,
                evidence=pattern,
                excerpt=body[:200].replace("\n", " "),
                confidence=0.8,
                maps_to="Prompt / AgentNode.instructions",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )


def _scan_tools_and_mcp(text: str, rel: str, findings: list[Finding], frameworks: set[str]) -> None:
    tool_patterns = [
        (r"""@tool(?:\([^)]*\))?\s*\n\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)""", "Decorated tool function"),
        (r"""tools\s*=\s*\[([^\]]{3,})\]""", "Tools list binding"),
        (r"""["']name["']\s*:\s*["']([A-Za-z0-9_.-]+)["'][\s\S]{0,80}["']description["']""", "JSON tool schema name"),
        (r"""function\s*:\s*\{\s*name\s*:\s*["']([A-Za-z0-9_.-]+)["']""", "OpenAI function tool"),
        (r"""input_schema\s*=\s*\{""", "Anthropic tool input_schema"),
        (r"""StructuredTool\.from_function""", "LangChain StructuredTool"),
    ]
    for pattern, title in tool_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            name = match.group(1) if match.lastindex else title
            _add(
                findings,
                kind="tool",
                title=f"Tool: {name}" if match.lastindex else title,
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.82,
                maps_to="Tool + ToolRule",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )

    mcp_patterns = [
        (r"""mcpServers\s*[:=]\s*\{""", "MCP server config map"),
        (r"""["']mcpServers["']\s*:\s*\{""", "MCP servers JSON"),
        (r"""["']command["']\s*:\s*["']npx["'][\s\S]{0,120}@modelcontextprotocol""", "MCP npx server"),
        (r""""jsonrpc"\s*:\s*"2\.0"[\s\S]{0,80}"method"\s*:\s*"([^"]+)" """, "JSON-RPC method"),
        (r"""list_tools|tools/list|tools/call""", "MCP tools protocol verb"),
        (r"""FastMCP|mcp\.tool\(|@mcp\.tool""", "MCP server tool registration"),
    ]
    for pattern, title in mcp_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            detail = match.group(1) if match.lastindex else title
            _add(
                findings,
                kind="mcp",
                title=f"MCP: {detail}",
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.88,
                maps_to="Tool + JsonRpcSchema",
                framework="mcp",
                path=rel,
                line=_line_of(text, match.start()),
            )

    schema_patterns = [
        (r""""\$schema"\s*:\s*"http""", "JSON Schema document"),
        (r"""class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(.*BaseModel""", "Pydantic schema model"),
        (r"""z\.object\s*\(""", "Zod object schema"),
        (r"""input_schema\s*[:=]""", "Tool input schema field"),
        (r"""output_schema\s*[:=]""", "Tool/agent output schema field"),
    ]
    for pattern, title in schema_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            name = match.group(1) if match.lastindex else title
            _add(
                findings,
                kind="schema",
                title=f"Schema: {name}",
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.75,
                maps_to="InputSchema / OutputSchema",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )


def _scan_orchestration(text: str, rel: str, findings: list[Finding], frameworks: set[str]) -> None:
    graph_patterns = [
        (r"""StateGraph\s*\(""", "LangGraph StateGraph"),
        (r"""add_node\s*\(\s*["']([^"']+)["']""", "Graph node"),
        (r"""add_edge\s*\(""", "Graph edge"),
        (r"""add_conditional_edges\s*\(""", "Conditional graph edge"),
        (r"""workflow\s*=\s*StateGraph""", "Workflow graph assignment"),
        (r"""AgentWorkflow|Workflow\s*\(""", "Agent workflow"),
    ]
    for pattern, title in graph_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            name = match.group(1) if match.lastindex else title
            _add(
                findings,
                kind="graph",
                title=f"Graph: {name}",
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.86,
                maps_to="AgentGraph + ControlEdge",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )

    loop_patterns = [
        (r"""recursion_limit\s*[:=]\s*(\d+)""", "Recursion / loop limit"),
        (r"""max_turns\s*[:=]\s*(\d+)""", "Max turns"),
        (r"""max_iter(?:ations)?\s*[:=]\s*(\d+)""", "Max iterations"),
        (r"""max_rpm\s*[:=]\s*(\d+)""", "Rate / RPM budget"),
        (r"""deadline|timeout_ms|time_budget""", "Deadline / time budget"),
        (r"""while\s+True\s*:[\s\S]{0,120}break""", "Manual agent loop"),
        (r"""for\s+_\s+in\s+range\s*\(\s*max_""", "Bounded agent loop"),
    ]
    for pattern, title in loop_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            detail = match.group(1) if match.lastindex else title
            _add(
                findings,
                kind="loop",
                title=f"Loop control: {detail}",
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.84,
                maps_to="LoopPolicy + LoopControl",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )

    orch_patterns = [
        (r"""Process\.hierarchical|manager_agent""", "Hierarchical orchestration"),
        (r"""supervisor|orchestrator|lead[_-]?agent""", "Supervisor / orchestrator role"),
        (r"""handoffs?\s*=|handoff_to|transfer_to_""", "Handoff orchestration"),
        (r"""fan[_-]?out|Send\s*\(|asyncio\.gather""", "Fan-out / parallel"),
        (r"""crew\.kickoff|Runner\.run|graph\.invoke|app\.invoke""", "Run entrypoint"),
        (r"""Human-in-the-loop|interrupt\s*\(|require_human""", "Human gate"),
    ]
    for pattern, title in orch_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            _add(
                findings,
                kind="orchestration",
                title=title,
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.8,
                maps_to="OrchestratorAgent / HandoffPolicy / FanOut / HumanGate",
                framework=next(iter(frameworks), None),
                path=rel,
                line=_line_of(text, match.start()),
            )


def _scan_runtime_and_sandbox(text: str, rel: str, findings: list[Finding]) -> None:
    sandbox_patterns = [
        (r"""firecracker|microvm|MicroVM""", "Firecracker / microVM sandbox"),
        (r"""gvisor|runsc""", "gVisor sandbox"),
        (r"""kata-containers|Kata""", "Kata Containers"),
        (r"""e2b|Sandbox\.create""", "E2B sandbox"),
        (r"""docker\s+run|containerd|seccomp|apparmor""", "Container isolation"),
        (r"""privileged:\s*false|readOnlyRootFilesystem|seccompProfile""", "Hardened pod settings"),
    ]
    for pattern, title in sandbox_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            _add(
                findings,
                kind="sandbox",
                title=title,
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.83,
                maps_to="ContextIsolationPolicy + DataClassPolicy",
                path=rel,
                line=_line_of(text, match.start()),
            )

    hyper_patterns = [
        (r"""bedrock-agentcore|AgentCore|bedrock-agent-runtime""", "AWS Bedrock AgentCore"),
        (r"""AzureAIAgent|azure\.ai\.agents|AIProjectClient""", "Azure AI Agents"),
        (r"""AgentEngine|ReasoningEngine|vertexai\.agent""", "Vertex Agent Engine"),
        (r"""Amazon Bedrock Agents|invoke_agent""", "Bedrock Agents runtime"),
    ]
    for pattern, title in hyper_patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            _add(
                findings,
                kind="hyperscaler",
                title=title,
                evidence=pattern,
                excerpt=_excerpt(text, match.start()),
                confidence=0.87,
                maps_to="Run + CheckpointPolicy + Trigger",
                path=rel,
                line=_line_of(text, match.start()),
            )


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES and path.name not in {
            "Dockerfile",
            "Dockerfile.agent",
            "Makefile",
        }:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def scan_root(root: Path) -> ScanResult:
    root = root.resolve()
    result = ScanResult(root=str(root))
    frameworks: set[str] = set()
    findings: list[Finding] = []

    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        result.files_scanned += 1
        file_frameworks = _scan_frameworks(text, rel, findings)
        frameworks |= file_frameworks
        _scan_prompts(text, rel, findings, file_frameworks or frameworks)
        _scan_tools_and_mcp(text, rel, findings, file_frameworks or frameworks)
        _scan_orchestration(text, rel, findings, file_frameworks or frameworks)
        _scan_runtime_and_sandbox(text, rel, findings)

    # Dedupe near-identical findings (same kind+title+path+line)
    seen: set[tuple] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.kind, finding.title, finding.path, finding.line, finding.evidence)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)

    result.frameworks = sorted(frameworks)
    result.findings = unique
    counts: dict[str, int] = {}
    for finding in unique:
        counts[finding.kind] = counts.get(finding.kind, 0) + 1
    result.summary = {
        "files_scanned": result.files_scanned,
        "frameworks": len(result.frameworks),
        "findings": len(unique),
        **counts,
    }
    return result


def result_to_dict(result: ScanResult) -> dict:
    return {
        "root": result.root,
        "frameworks": result.frameworks,
        "files_scanned": result.files_scanned,
        "summary": result.summary,
        "findings": [asdict(f) for f in result.findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root to scan")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    parser.add_argument("-o", "--output", type=Path, help="Write JSON report to path")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        return 2

    result = scan_root(root)
    payload = result_to_dict(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.json or args.output:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Scan root: {root}")
        print(f"Files scanned: {result.files_scanned}")
        print(f"Frameworks: {', '.join(result.frameworks) or '(none)'}")
        for key, value in sorted(result.summary.items()):
            print(f"  {key}: {value}")
        print("Top findings:")
        for finding in result.findings[:20]:
            loc = f"{finding.path}:{finding.line}" if finding.path else "?"
            print(f"  - [{finding.kind}] {finding.title} ({loc}) → {finding.maps_to}")
        if len(result.findings) > 20:
            print(f"  … {len(result.findings) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
