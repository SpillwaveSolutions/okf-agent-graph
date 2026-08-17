# okf-agent-graph

**OKF Agent Graph Engineering Runtime (AGER)** — a Claude Code, Codex, Grok Build, Grok Bot, and LangChain Deep Agents plugin for authoring **multi-agent loop graphs** as OKF (Markdown + YAML).

| | |
|---|---|
| **Plugin name** | `okf-agent-graph` |
| **Version** | 0.6.2 |
| **Depends on** | [`okf-plugin`](https://github.com/SpillwaveSolutions/okf-plugin) → plugin **`okf-graph-eng`** |
| **Related** | [`wiki_ticket_sdd`](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) (ticket triggers / worklog) |
| **Docs** | [User guide](./docs/user_guide/user-guide.md) · [AGER spec](./docs/AGER_SPEC.md) · [Reverse engineering](./docs/REVERSE_ENGINEERING.md) · [Design doc](./docs/designs/current_design_doc.md) · [Code walkthrough](./docs/designs/current_code_walkthrough.md) |
| **License** | MIT |


## Multi-host

| Host | How it loads |
|------|----------------|
| Claude Code | Marketplace / local plugin (`.claude-plugin`) |
| Grok Build | Claude-compatible, zero-config (`.grok-plugin` pins identity) |
| Codex | `.codex-plugin` (skills; no extra Codex hooks — existing git hooks stay as-is) |
| Agent Plugins 1.0 | Root `plugin.json` |
| Grok Bot | Skills + [docs/GROK_BOT.md](docs/GROK_BOT.md) |
| LangChain Deep Agents | `skills=` / SkillsMiddleware — [docs/LANG_CHAIN_DEEP_AGENTS.md](docs/LANG_CHAIN_DEEP_AGENTS.md) |

Write isolation: [docs/ISOLATION.md](docs/ISOLATION.md). LoopPolicy / KnowledgeBind read `main` and write `brain/<actor>/<session-id>`. Public examples use fictional **lumenfield-detector** and **northstar-console** only.

Also: [Onboarding](./docs/ONBOARDING.md) · skill `ager-session`.

## Why this plugin

[`okf-graph-eng`](https://github.com/SpillwaveSolutions/okf-plugin) gives you portable OKF graphs, impact analysis, validation, and progressive disclosure.

**okf-agent-graph** adds the **domain model for multi-agent runtime config**:

- Orchestrator / Doer / Judge / Synthesizer roles  
- **LoopControls**: goal, deadline, price, max_turns, no_progress  
- **Tools** with expression **block rules**, idempotency, secrets  
- **ScratchPad KV** (`set` / `append` lists) + **lineage**  
- **Run + Trigger**, FailurePolicy, RetryPolicy, Compensation  
- KnowledgeBind / RetrievalBinding (OKF / project knowledge)

Use as a **spec** and as **runtime-loadable config** (adapters map to LangGraph, CrewAI, OpenAI Agents, Anthropic patterns).

**Reverse engineering (AGKC):** point the plugin at an existing agent repo — Claude/ChatGPT API, LangChain, LangGraph, CrewAI, LlamaIndex, Claude Agent SDK, Deep Agents, MCP, Bedrock AgentCore, hardened microVMs/containers — and extract prompts, tools/JSON-RPC/MCP schemas, orchestration graphs, loop/harness policies, and runtime isolation into draft AGER knowledge. Same shape as [system-architecture-capture](https://github.com/SpillwaveSolutions/system-architecture-capture) and [data-engineering-knowledge-capture](https://github.com/SpillwaveSolutions/data-engineering-knowledge-capture), for the agent-graph domain.

## Dependency (required)

Install **okf-plugin first** — this plugin reuses its graph validate/impact/query tooling.

```bash
# 1) Core OKF graph engineering
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace

# 2) Agent graph / AGER domain
claude plugin marketplace add SpillwaveSolutions/okf-agent-graph
claude plugin install okf-agent-graph@okf-agent-graph-marketplace
```

For Codex, add the same repository marketplace, open `/plugins`, install
`okf-agent-graph`, and start a new session:

```bash
codex plugin marketplace add SpillwaveSolutions/okf-agent-graph
codex
# /plugins
```

The pinned `okf-plugin` v0.3.2 dependency does not ship a Codex manifest. Run
full OKF validation through an `okf` executable, a sibling `../okf-plugin`
checkout, or an explicitly supplied path to `okf-graph.py`.

Grok Build loads Claude-compatible plugins with zero extra config.

### Dependency contract

| Capability | Provided by |
|------------|-------------|
| `okf validate` / `okf-graph.py validate` | **okf-graph-eng** |
| Impact / edges / visualize | **okf-graph-eng** |
| ContextPack (1/4-window, fail-closed) | **okf-agent-graph** (`ager_pack.py`) |
| Authoring AgentNode basics | **okf-graph-eng** (`okf-author`) |
| AGER types, loop policies, tools+rules, ops plane | **okf-agent-graph** (this repo) |
| Validate AGER field rules | **okf-agent-graph** (`ager-validate`) + okf validate |

See [docs/DEPENDENCIES.md](./docs/DEPENDENCIES.md).

## Quick start

1. Ensure `okf-graph-eng` is installed  
2. `/ager-init` or `$ager-init-graph` — scaffold an AGER bundle
3. `/ager-author` or `$ager-author` — add Orchestrator, Workers, Judge, LoopPolicy, Tools
4. `/ager-validate` or `$ager-validate` — AGER rules + delegate to okf validate
5. `/ager-pack` — tiny or 2-hop ContextPack. Fail-closed over the token budget.
6. Optional: `/ager-compile` — emit adapter notes / stubs for a target framework  

The scripts are also directly callable:

```bash
python3 scripts/ager-init.py agent-graph --title "My agent graph"
python3 scripts/ager-validate.py agent-graph --strict

# Reverse engineer an existing agent project
python3 scripts/ager_scan.py --root /path/to/agent-project --json -o scan.json
python3 scripts/ager_reverse_engineer.py --root /path/to/agent-project --out discovered-ager --json
```

Sample self-describing graph:

```bash
# Requires okf-plugin scripts on path or clone sibling
python3 scripts/ager-validate.py sample-ager --strict
python3 ../okf-plugin/scripts/okf-graph.py validate sample-ager --strict
```

## Skills & commands

| Skill | Command | Purpose |
|-------|---------|---------|
| `ager-init-graph` | `/ager-init` | Scaffold AGER OKF tree |
| `ager-author` | `/ager-author` | Author agents, tools, loop policies, ops concepts |
| `ager-validate` | `/ager-validate` | AGER conformance + okf validate |
| `ager-compile` | `/ager-compile` | Framework mapping / stub notes |
| `ager-scan` | `/ager-scan` | Scan code for frameworks, prompts, tools, MCP, loops |
| `ager-reverse-engineer` | `/ager-reverse-engineer` | AGKC: reverse engineer → draft AGER knowledge |

Codex invokes the same skills with `$ager-init-graph`, `$ager-author`,
`$ager-validate`, `$ager-compile`, `$ager-scan`, and `$ager-reverse-engineer`.

### Agent

- **agent-graph-engineer** — designs multi-agent loops using AGER + okf impact/pack
- **agent-graph-re-orchestrator** — reverse-engineers existing agent codebases into AGER (AGKC)

## Concept planes (AGER v0.3)

1. **Core** — AgentNode roles, AgentGraph, FanOut/In, modules, I/O schemas  
2. **Control** — LoopPolicy / LoopControl (goal, deadline, price, max_turns, no_progress)  
3. **Memory** — ScratchPad KV + lineage, EpisodeStore, KnowledgeBind, RetrievalBinding  
4. **Ops / action** — Run, Trigger, Failure/Retry/Compensation, Tool+ToolRule, SecretRef, quotas  

Full catalog: [docs/AGER_SPEC.md](./docs/AGER_SPEC.md) · sample: [`sample-ager/`](./sample-ager/)

## Ecosystem map

```text
okf-plugin (okf-graph-eng)     portable OKF graph ops
        ▲
        │ depends on
okf-agent-graph (this)         multi-agent loop domain
        │
        ├── wiki_ticket_sdd    Trigger kind: ticket_event
        └── knowledge/ (PKC)   KnowledgeBind source
```

## License

MIT — see [LICENSE](./LICENSE).
