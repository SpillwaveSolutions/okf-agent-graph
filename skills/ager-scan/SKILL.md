---
name: ager-scan
description: Scan a codebase for agent frameworks (LangGraph, CrewAI, LlamaIndex, Claude/OpenAI APIs, MCP, Deep Agents, hyperscalers, microVMs) and for Claude/Grok/Codex/universal plugin agents and skills. Extracts prompts, tools, schemas, orchestration, loops, harness signals, and plugin frontmatter. Use when reverse-engineering an existing agent project into AGER concepts.
---

# AGER Scan

Deterministic filesystem scan — the reverse-engineering detector for agent stacks.
Sibling of SAC `sac-scan` / DEKC `dekc-walk`, specialized for multi-agent runtimes.

## What it extracts

| Finding kind | Maps toward AGER |
|--------------|------------------|
| plugin | Harness + AgentGraph |
| agent / skill | WorkerAgent / JudgeAgent / OrchestratorAgent |
| framework | Framework adapter notes |
| system_prompt / prompt | AgentNode.instructions / Prompt |
| tool | Tool + ToolRule |
| mcp | Tool + JSON-RPC schema |
| schema | InputSchema / OutputSchema |
| graph | AgentGraph + ControlEdge |
| loop | LoopPolicy + LoopControl |
| orchestration | Orchestrator / Handoff / FanOut / HumanGate |
| sandbox | ContextIsolationPolicy |
| hyperscaler | Run + CheckpointPolicy (AgentCore, Azure AI, Vertex) |

## Supported detectors (non-exhaustive)

- **Claude Code plugins**: `.claude-plugin/plugin.json`, `.claude/agents/*.md`, `.claude/skills/*/SKILL.md` (and undotted `claude/`)
- **Grok Build plugins**: `.grok-plugin/`, `.grok/agents`, `.grok/skills` (and undotted `grok/`)
- **Codex plugins**: `.codex-plugin/plugin.json`, `.codex/agents`, `.codex/skills` (and undotted `codex/`)
- **Agent Plugins 1.0**: root `plugin.json` (`$schema` agent-plugins.org) + `agents/` + `skills/`
- Raw **Claude / Anthropic API**, **OpenAI API**
- **LangChain**, **LangGraph**, **CrewAI**, **LlamaIndex**
- **OpenAI Agents SDK**, **Claude Agent SDK**, **Deep Agents**, AutoGen, Semantic Kernel
- **MCP** servers / JSON-RPC tool catalogs
- Hyperscalers: **Bedrock AgentCore**, Azure AI Agents, Vertex Agent Engine
- Hardened runtimes: **Firecracker** microVMs, **gVisor**, **Kata**, **E2B**, hardened containers

## Steps

1. Confirm the source root (repo path or clone).
2. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_scan.py" --root "$SOURCE_ROOT" --json -o scan.json
```

3. Summarize frameworks + counts for the user.
4. For materialization into a draft AGER bundle, continue with **ager-reverse-engineer**.

## Notes

- Scan is best-effort and confidence-scored; it does not execute untrusted code.
- Prefer promoting high-confidence findings via **ager-author** after human review.
- Generic keyword hits (`Supervisor / orchestrator role`, container isolation, …)
  collapse to one finding with multiple `evidence_paths` instead of one node per
  file. Tool matches without a real identifier (`Tool: { json blob }`) are dropped.
