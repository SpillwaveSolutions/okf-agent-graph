---
type: Tool
tool_id: web_search
title: Web search
description: Example tool with budget and duplicate block rules.
ager_version: "0.3.0"
side_effects: external
input_schema:
  type: object
  required: [q]
  properties:
    q: { type: string }
cost:
  fixed_usd: 0.002
idempotency:
  mode: at_least_once
  key_expression: "args.q"
rules:
  - id: block-if-budget
    when: "run.cost.usd >= run.budget.usd"
    action: block
    message: Price budget exhausted
    priority: 100
  - id: block-dup
    when: "scratchpad.get_list('tool:web_search').slice(-5).some(c => c.args && c.args.q == args.q)"
    action: block
    message: Duplicate query
    priority: 50
record_output_to:
  key: tool:web_search
  mode: append
status: active
timestamp: 2026-08-04T00:00:00Z
---

# web_search
