---
type: JudgeAgent
title: Quality judge
description: Scores candidates against a rubric; drives goal / no_progress controls.
ager_version: "0.3.0"
rubrics:
  - /evaluation/quality-rubric.md
threshold: 0.72
on_fail: retry_producer
input_schema: /schemas/judge-input.schema.json
output_schema: /schemas/judgment.schema.json
record_output_to:
  key: judgments
  mode: append
status: active
timestamp: {{TIMESTAMP}}
links:
  - target: /evaluation/quality-rubric.md
    rel: depends_on
  - target: /runtime/scratchpad.md
    rel: appends_to
---

# Judge

Emit score, pass, feedback, revise.
