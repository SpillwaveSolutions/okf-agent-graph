---
name: ager-author
description: Author or update AGER concepts — OrchestratorAgent, WorkerAgent, JudgeAgent, LoopPolicy/LoopControl, Tool+ToolRule, ScratchPad, Run/Trigger, FailurePolicy, KnowledgeBind. Use when editing multi-agent graphs, budgets, tool rules, or ops policies. Requires okf-plugin for link validation.
---

# AGER Author

Create/update **AGER v0.3** OKF concepts with correct fields, typed edges, and provenance.

## Prerequisite

Use **okf-author** patterns from okf-graph-eng for general OKF rules; this skill adds AGER-specific fields.

## Concept quick rules

### Agents
- Always set `input_schema` + `output_schema` (path or inline)
- Workers: `record_output_to: { key: worker_outputs, mode: append }`
- Judges: rubrics + `record_output_to: { key: judgments, mode: append }`
- Optional: `timeout_ms`, `failure_policy`, `retry_policy`, `retrievals`

### LoopPolicy
- Include controls covering: goal, deadline, price_budget, max_turns, no_progress as appropriate
- Set `on_exhaust` and `on_goal`
- Link graph with `rel: controlled_by`

### Tool
- `side_effects`, schemas, `rules[]` with `when` + `action`
- Hardening: `idempotency`, `secrets` (SecretRef only), `rate_limit`, `compensation`, `dual_control`

### ScratchPad
- Document conventional keys; `lineage: full` for production
- Never store SecretRef material in plaintext

### Run / Trigger
- Trigger kinds: manual | webhook | cron | ticket_event | okf_change | ci
- Run status machine: queued → running → paused_human → terminal

## Steps

1. Identify concept type and target path under the bundle.
2. Copy nearest template from `templates/` or `sample-ager/`.
3. Fill required fields; add typed `links`.
4. Update parent catalog `index.md`.
5. Append `log.md` entry.
6. Run **ager-validate** / okf validate.

## References

- `references/typed-edges.md`
- `references/loop-controls.md`
- `../ager-init-graph/templates/`
