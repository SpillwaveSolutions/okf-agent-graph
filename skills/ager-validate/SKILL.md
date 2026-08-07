---
name: ager-validate
description: Validate AGER bundle structure and field rules, then delegate link/graph validation to okf-plugin (okf-graph-eng). Use before merge or after authoring multi-agent graphs.
---

# AGER Validate

## Run AGER validation

```bash
python3 <plugin-root>/scripts/ager-validate.py <bundle> --strict
```

The command emits JSON and exits non-zero on errors; `--strict` also gates
warnings. It requires only the Python standard library.

## Checks (this plugin)

1. Bundle root has `okf_version` and preferably `ager_version: "0.3.0"`.
2. Every AgentNode-like concept has `input_schema` and `output_schema` (or documents exception).
3. AgentGraph (if present) links LoopPolicy and ScratchPad.
4. LoopPolicy has ≥1 control; warn if missing deadline or price on production graphs.
5. Tools with `side_effects: irreversible` should have dual_control or require_human rule or compensation.
6. No inline secret values — only SecretRef paths.
7. Workers that claim parallel use should `record_output_to` with `mode: append`.

## Delegate to okf-graph-eng

```bash
okf validate <bundle> --strict
# or
python3 <okf-plugin>/scripts/okf-graph.py validate <bundle> --strict
```

If okf tooling missing, report AGER checks only and instruct user to install okf-plugin.

## Done when

- AGER structural issues listed (errors vs warnings)
- OKF validation results included or skip reason stated
