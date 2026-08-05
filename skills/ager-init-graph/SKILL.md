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
2. Run the deterministic generator from the plugin root:

```bash
python3 <plugin-root>/scripts/ager-init.py <bundle> --title "<graph title>"
```

The command refuses an existing destination, renders into a temporary directory,
runs strict AGER validation, and installs the bundle atomically.
3. The generated structure is:

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

4. Customize the illustrative research graph without deleting required contracts.
5. Root `index.md` keeps `okf_version: "0.2"` and `ager_version: "0.3.0"`.
6. Absolute links only: `[Lead](/agents/lead-researcher.md)`.
7. Validate:
   - AGER structural checks (required fields per type)
   - `okf validate` / `okf-graph.py validate` from **okf-plugin**
8. Report paths + any errors.

## Rules

- Do not invent domain content beyond one illustrative research/example graph.
- Every file: YAML frontmatter with `type`, `title`, `description`, `timestamp` (and `ager_version` on AGER types).
- Prefer `record_output_to: { key, mode: append }` on workers/judges.
- Link FailurePolicy via `on_failure` / `failure_policy` field.

## Canonical scaffold

The complete source tree lives at `<plugin-root>/scaffold/`. Do not recreate a
second template tree under this skill; tests keep the generated scaffold valid.

## Done when

- Bundle exists with agents + runtime + ops
- LoopPolicy includes goal + deadline + price + max_turns + no_progress
- okf validate (if available) reports no broken links
