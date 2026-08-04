# okf-agent-graph

**OKF Agent Graph Engineering Runtime (AGER)** — a Claude Code / Grok Build plugin for authoring **multi-agent loop graphs** as OKF (Markdown + YAML).

| | |
|---|---|
| **Plugin name** | `okf-agent-graph` |
| **Version** | 0.3.0 |
| **Depends on** | [`okf-plugin`](https://github.com/SpillwaveSolutions/okf-plugin) → plugin **`okf-graph-eng`** |
| **Related** | [`wiki_ticket_sdd`](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) (ticket triggers / worklog) |
| **License** | MIT |

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

Grok Build loads Claude-compatible plugins with zero extra config.

### Dependency contract

| Capability | Provided by |
|------------|-------------|
| `okf validate` / `okf-graph.py validate` | **okf-graph-eng** |
| Impact / pack / edges / visualize | **okf-graph-eng** |
| Authoring AgentNode basics | **okf-graph-eng** (`okf-author`) |
| AGER types, loop policies, tools+rules, ops plane | **okf-agent-graph** (this repo) |
| Validate AGER field rules | **okf-agent-graph** (`ager-validate`) + okf validate |

See [docs/DEPENDENCIES.md](./docs/DEPENDENCIES.md).

## Quick start

1. Ensure `okf-graph-eng` is installed  
2. `/ager-init` — scaffold an AGER bundle (or `.okf/` with agent-graph layout)  
3. `/ager-author` — add Orchestrator, Workers, Judge, LoopPolicy, Tools  
4. `/ager-validate` — AGER rules + delegate to okf validate  
5. Optional: `/ager-compile` — emit adapter notes / stubs for a target framework  

Sample self-describing graph:

```bash
# Requires okf-plugin scripts on path or clone sibling
python3 ../okf-plugin/scripts/okf-graph.py validate sample-ager
```

## Skills & commands

| Skill | Command | Purpose |
|-------|---------|---------|
| `ager-init-graph` | `/ager-init` | Scaffold AGER OKF tree |
| `ager-author` | `/ager-author` | Author agents, tools, loop policies, ops concepts |
| `ager-validate` | `/ager-validate` | AGER conformance + okf validate |
| `ager-compile` | `/ager-compile` | Framework mapping / stub notes |

### Agent

- **agent-graph-engineer** — designs multi-agent loops using AGER + okf impact/pack

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
