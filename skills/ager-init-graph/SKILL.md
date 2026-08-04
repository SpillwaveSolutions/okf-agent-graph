---
name: ager-init-graph
description: Scaffold an OKF Agent Graph (AGER) bundle with orchestrator/workers/judge layout, LoopPolicy, ScratchPad, FailurePolicy, and sample Tool. Use when starting multi-agent graphs, AGER configs, or loop-engineering scaffolds. Requires okf-plugin (okf-graph-eng).
---

# AGER Init Graph

Scaffold a multi-agent **loop engineering** OKF bundle (AGER v0.3).

## Prerequisite

**okf-graph-eng** must be installed ([SpillwaveSolutions/okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin)). Use it for final `validate` / `impact`.

## When to use

- New multi-agent system design in OKF
- User asks for orchestrator/workers, judges, loop budgets, tool policies
- Converting a project to AGER layout

## Steps

1. Confirm target directory (default `.okf/` or `agent-graph/` at repo root).
2. Create structure:

```
<bundle>/
├── index.md
├── log.md
├── agents/
├── runtime/          # LoopPolicy, ScratchPad, Checkpoint, edges
├── ops/              # Failure, Retry, Run, Trigger, limits
├── evaluation/       # Rubrics
├── memory/           # KnowledgeBind, Retrieval
├── tools/
├── models/
├── patterns/
└── schemas/
```

3. Root `index.md`: `okf_version: "0.2"`, `ager_version: "0.3.0"`, dual purpose description.
4. Seed from templates in this skill:
   - OrchestratorAgent, WorkerAgent, JudgeAgent, SynthesizerAgent
   - LoopPolicy (all 5 control axes)
   - ScratchPad (lineage: full)
   - FailurePolicy + RetryPolicy
   - One Tool with block rules
   - Optional Trigger (ticket_event if wiki_ticket present)
5. Absolute links only: `[Lead](/agents/orchestrator.md)`.
6. Validate:
   - AGER structural checks (required fields per type)
   - `okf validate` / `okf-graph.py validate` from **okf-plugin**
7. Report paths + any errors.

## Rules

- Do not invent domain content beyond one illustrative research/example graph.
- Every file: YAML frontmatter with `type`, `title`, `description`, `timestamp` (and `ager_version` on AGER types).
- Prefer `record_output_to: { key, mode: append }` on workers/judges.
- Link FailurePolicy via `on_failure` / `failure_policy` field.

## Templates

- `templates/orchestrator.md`
- `templates/worker.md`
- `templates/judge.md`
- `templates/loop-policy.md`
- `templates/scratchpad.md`
- `templates/failure-policy.md`
- `templates/tool.md`
- `templates/index-root.md`

## Done when

- Bundle exists with agents + runtime + ops
- LoopPolicy includes goal + deadline + price + max_turns + no_progress
- okf validate (if available) reports no broken links
