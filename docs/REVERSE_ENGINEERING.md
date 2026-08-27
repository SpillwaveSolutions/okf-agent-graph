---
doc_type: guide
slug: REVERSE_ENGINEERING
title: AGER Reverse Engineering (AGKC)
truth_state: current
wiki_key: reverse-engineering
---

# AGER Reverse Engineering (AGKC)

**AGKC** — Agent Graph Knowledge Capture — is the reverse-engineering path inside
`okf-agent-graph`. Forward skills (`ager-init`, `ager-author`) define agentic flows;
AGKC **reads codebases that already use** Claude/ChatGPT APIs, LangChain, LangGraph,
CrewAI, LlamaIndex, Claude Agent SDK, Deep Agents, MCP, and related runtimes, then
emits draft AGER knowledge. It also reads **plugin** layouts — Claude Code,
Grok Build, Codex, Cursor, and Agent Plugins 1.0 — so a repo whose agents are
subagent markdown and `SKILL.md` files still becomes real Agent/Tool/AgentGraph
nodes instead of keyword hits on the word "orchestrator".

## Why

Most production agent systems are not born as AGER bundles. Teams need to:

1. Inventory prompts / system prompts  
2. Catalog tools, JSON Schema / JSON-RPC contracts, MCP servers  
3. Recover orchestration graphs, loops, and harness policies  
4. Note hyperscaler agent cores and hardened microVM/container sandboxes  
5. Re-express the system as portable OKF/AGER for review, migration, or dual-run  

## Sibling plugins

| Plugin | Domain |
|--------|--------|
| [system-architecture-capture](https://github.com/SpillwaveSolutions/system-architecture-capture) | Services, IaC, CI/CD, identity |
| [data-engineering-knowledge-capture](https://github.com/SpillwaveSolutions/data-engineering-knowledge-capture) | Lakes, lineage, semantic models |
| **okf-agent-graph (this)** | Multi-agent graphs, prompts, tools, loops, harnesses |

## CLI

```bash
# Scan only
python3 scripts/ager_scan.py --root /path/to/project --json -o scan.json

# Scan + materialize draft AGER knowledge
python3 scripts/ager_reverse_engineer.py \
  --root /path/to/project \
  --out discovered-ager \
  --title "My agent system" \
  --scan-json discovered-ager/scan.json \
  --json

# After promotion into a full AGER bundle
python3 scripts/ager-validate.py agent-graph --strict
```

## Skills & commands

| Skill | Command | Purpose |
|-------|---------|---------|
| `ager-scan` | `/ager-scan` | Framework + artifact detection |
| `ager-reverse-engineer` | `/ager-reverse-engineer` | End-to-end AGKC capture |

Codex: `$ager-scan`, `$ager-reverse-engineer`.

## Extraction model

```text
Source tree
   │ ager_scan.py
   ▼
Findings JSON (frameworks, plugins, agents, skills, prompts, tools, mcp, schemas, graphs, loops, …)
   │ ager_capture.py
   ▼
Draft AGER knowledge (Markdown + provenance)
   │ human / ager-author
   ▼
Validated AGER bundle (ager-validate + okf validate)
```

## Planes covered

| Plane | Reverse signals |
|-------|-----------------|
| Core | Agents, graphs, edges, schemas; plugin subagents + SKILL.md frontmatter |
| Control | max turns, recursion limits, deadlines, stop heuristics |
| Memory | scratchpad / state keys, retrieval hooks |
| Ops | tools (including declared plugin `tools:`), MCP, JSON-RPC, secrets placeholders, failure cues |
| Runtime | harness loops, sandboxes, hyperscaler agent runtimes, Claude/Grok/Codex/universal plugins |

## Safety

- Scanners are read-only and dependency-free (stdlib only).  
- Do not execute untrusted project code as part of capture.  
- Redact secrets; prefer `${ENV}` / SecretRef paths in drafts.  
