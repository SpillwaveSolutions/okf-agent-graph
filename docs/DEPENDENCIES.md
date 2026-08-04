# Dependencies

## Required: okf-plugin (`okf-graph-eng`)

| Item | Value |
|------|--------|
| Repository | https://github.com/SpillwaveSolutions/okf-plugin |
| Plugin name | `okf-graph-eng` |
| Marketplace | `okf-plugin-marketplace` |
| Min version | 0.3.0 (tested against 0.3.2) |

### Why required

AGER concepts are **OKF documents**. Validation of links, typed edges, impact analysis, progressive disclosure packs, and graph visualization are implemented in **okf-graph-eng**. This plugin does **not** reimplement the graph engine.

### What okf-agent-graph adds

- AGER concept types and templates (OrchestratorAgent, JudgeAgent, LoopPolicy, Tool, ScratchPad, Run, FailurePolicy, …)
- Skills that enforce AGER field rules and loop/tool/ops conventions
- Sample `sample-ager/` bundle
- Compile guidance to external frameworks (LangGraph, CrewAI, OpenAI, Anthropic)

### Install order

1. `SpillwaveSolutions/okf-plugin` → install `okf-graph-eng`
2. `SpillwaveSolutions/okf-agent-graph` → install `okf-agent-graph`

### Runtime resolution

Skills look for okf tooling in this order:

1. `okf` / `okfcli` on PATH  
2. `${CLAUDE_PLUGIN_ROOT}` of **okf-graph-eng** if discoverable  
3. Sibling checkout `../okf-plugin/scripts/okf-graph.py`  
4. User-provided path

If none found, `ager-validate` still runs **AGER structural checks** and warns that full OKF link validation was skipped.

## Optional

| Project | Use |
|---------|-----|
| [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) | `Trigger.kind: ticket_event`, worklog attribution on `Run` |
| Project Knowledge Capture (future) | `KnowledgeBind` / PKC materialization into `./knowledge` |
