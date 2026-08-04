---
type: OrchestratorAgent
title: Lead orchestrator
description: Plans work, spawns workers, owns outer loop and scratchpad.
role: lead
ager_version: "0.3.0"
input_schema: /schemas/user-query.schema.json
output_schema: /schemas/final-output.schema.json
instructions: /prompts/lead.md
worker_pool:
  - /agents/worker.md
judge_pool:
  - /agents/judge.md
max_workers: 5
spawn_policy: dynamic
owns_scratchpad: true
loop_policy: /runtime/loop-policy.md
failure_policy: /ops/failure-policy.md
timeout_ms: 120000
record_output_to:
  key: orchestrator_plans
  mode: append
status: active
timestamp: 2026-08-04T00:00:00Z
links:
  - target: /agents/worker.md
    rel: spawns
  - target: /runtime/loop-policy.md
    rel: controlled_by
  - target: /ops/failure-policy.md
    rel: on_failure
  - target: /runtime/scratchpad.md
    rel: writes_to
---

# Lead orchestrator

Plan → fan-out workers → synthesize → judge → re-plan under LoopControls.
