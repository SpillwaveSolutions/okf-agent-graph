---
type: OrchestratorAgent
title: Lead researcher
description: Plans research facets, spawns isolated workers, drives outer loop.
role: lead_researcher
ager_version: "0.3.0"
input_schema: /schemas/user-query.schema.json
output_schema: /schemas/final-report.schema.json
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
retry_policy: /ops/retry-policy.md
retrievals:
  - /memory/retrieval-hybrid.md
timeout_ms: 120000
record_output_to:
  key: orchestrator_plans
  mode: append
status: active
timestamp: 2026-08-04T00:00:00Z
links:
  - target: /agents/worker.md
    rel: spawns
  - target: /agents/judge.md
    rel: routes_to
  - target: /runtime/loop-policy.md
    rel: controlled_by
  - target: /ops/failure-policy.md
    rel: on_failure
  - target: /runtime/scratchpad.md
    rel: writes_to
  - target: /memory/retrieval-hybrid.md
    rel: retrieves_from
---

# Lead researcher
