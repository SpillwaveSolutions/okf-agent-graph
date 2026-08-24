---
type: SynthesizerAgent
title: Report synthesizer
description: Reduces worker_outputs list into one draft report.
ager_version: "0.3.0"
reduce_strategy: merge
input_from_kv: worker_outputs
input_schema: /schemas/synth-input.schema.json
output_schema: /schemas/final-report.schema.json
record_output_to:
  key: best_draft
  mode: set
status: active
verified: true
timestamp: 2026-08-04T00:00:00Z
links:
  - target: /runtime/scratchpad.md
    rel: reads_from
  - target: /agents/worker.md
    rel: aggregates_from
---

# Synthesizer
