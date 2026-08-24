---
doc_type: guide
slug: noun-ownership-migration
title: Noun-ownership migration (AGER)
truth_state: current
---

# Noun-ownership migration (AGER 0.7.0)

Family runbook: [okf-plugin noun-ownership migration](https://github.com/SpillwaveSolutions/okf-plugin/blob/main/docs/user_guide/noun-ownership-migration.md).

AGER now ships JSON Schema for the harness nouns and `x-impact` so okf-plugin can rank blast radius **without owning those types**. Authoring `AgentNode` / `Workflow` is `/ager-author`, not `/okf-author`.

## Upgrade

1. Pin **okf-plugin v0.8.0** (CI that still checks out `v0.3.2` will not merge AGER schemas or `x-impact`). Then this plugin **v0.7.0**.
2. Keep `type:` on existing agents, workflows, loop policies, tools, ops, eval nodes.
3. Validate:

```bash
python3 scripts/ager-validate.py sample-ager --strict
python3 path/to/okf-plugin/scripts/okf-graph.py validate sample-ager --strict
```

## `WriteEvent`

`WriteEvent` is **not** an AGER noun. 0.7.0 deleted `schemas/okf-concepts/WriteEvent.schema.json`.

- Nodes under `write-events/` stay `type: WriteEvent`.
- `ager_common.emit_write_event` still writes them and **does not** set `ager_version`.
- Do not add a replacement AGER alias in this cut.
- Isolated `okf-graph.py validate --strict` reports unknown type unless `second-brain-core` (or another pack that registers the journal) is on the schema path. That is an info/error on the journal, not a reason to retype harness nodes.

## Unverified high-impact

These types now carry `x-impact: high` (non-exhaustive): `AgentNode`, `OrchestratorAgent`, `WorkerAgent`, `JudgeAgent`, `SynthesizerAgent`, `RouterAgent`, `GuardrailAgent`, `HumanGate`, `AgentGraph`, `Workflow`, `Harness`, `SharedState`, `LoopPolicy`.

`okf-graph.py validate --strict` warns (and therefore fails) on `verified: false` for those types. Canonical samples set `verified: true`. A draft graph can stay unverified: use lenient validate, or verify the node when it is no longer a draft.

## DEKC `Workflow` vs AGER `Workflow`

If a data-engineering tree stored Glue/ADF/Airflow jobs as `type: Workflow`, those are **not** AGER graphs. Retype them to `IngestionJob` in the DEKC pack (see the DEKC migration guide). Leave `type: Workflow` only for multi-agent loop graphs.

## Dual-owned name

`RateLimit` is also a SAC gateway noun. AGER `RateLimit` is runtime quota on a tool or loop. One tree, one meaning.

## What not to do

- Do not impersonate the AGER actor in a private knowledge tree to “fix” schemas.
- Do not copy `WriteEvent` back into `registry.json`.
- Do not author AgentNode via okf-plugin templates (they were removed).

## Done when

- `WriteEvent` is absent from this plugin’s `registry.json`.
- `ager-validate --strict` is green on the graph.
- okf-plugin pin is v0.8.0+ so `x-impact` actually loads.
