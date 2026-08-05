---
type: WorkerAgent
title: Specialist worker
description: Isolated doer; appends structured results to ScratchPad.
role: worker
specialty: general_research
ephemeral: true
can_spawn: false
ager_version: "0.3.0"
input_schema: /schemas/task.schema.json
output_schema: /schemas/findings.schema.json
instructions: /prompts/worker.txt
max_turns: 12
timeout_ms: 180000
tools:
  - web_search
record_output_to:
  key: worker_outputs
  mode: append
failure_policy: /ops/failure-policy.md
retry_policy: /ops/retry-policy.md
status: active
timestamp: {{TIMESTAMP}}
links:
  - target: /runtime/scratchpad.md
    rel: appends_to
  - target: /tools/web-search.md
    rel: uses
---

# Worker

Return structured findings only. Prefer artifact refs for large blobs.
