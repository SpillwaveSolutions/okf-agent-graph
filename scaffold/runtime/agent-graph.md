---
type: AgentGraph
title: Parallel research graph
ager_version: "0.3.0"
description: Orchestrator-workers research with judge and ops controls.
entry: /agents/lead-researcher.md
nodes:
  - /agents/lead-researcher.md
  - /agents/worker.md
  - /agents/synthesizer.md
  - /agents/judge.md
state_schema: /schemas/research-state.schema.json
loop_policy: /runtime/loop-policy.md
scratchpad: /runtime/scratchpad.md
failure_policy: /ops/failure-policy.md
concurrency: /ops/concurrency.md
status: active
verified: true
timestamp: {{TIMESTAMP}}
links:
  - target: /runtime/loop-policy.md
    rel: controlled_by
  - target: /ops/failure-policy.md
    rel: on_failure
  - target: /patterns/orchestrator-workers.md
    rel: implements
---

# Parallel research graph
