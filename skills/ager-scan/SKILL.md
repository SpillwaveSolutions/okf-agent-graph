---
name: ager-scan
description: Scan a codebase for agent frameworks (LangGraph, CrewAI, LlamaIndex, Claude/OpenAI APIs, MCP, Deep Agents, hyperscalers, microVMs) and extract prompts, tools, schemas, orchestration, loops, and harness signals. Use when reverse-engineering an existing agent project into AGER concepts.
---

# AGER Scan

Deterministic filesystem scan — the reverse-engineering detector for agent stacks.
Sibling of SAC `sac-scan` / DEKC `dekc-walk`, specialized for multi-agent runtimes.

## What it extracts

| Finding kind | Maps toward AGER |
|--------------|------------------|
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
