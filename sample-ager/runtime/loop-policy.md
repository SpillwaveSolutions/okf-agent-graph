---
type: LoopPolicy
title: Default loop controls
description: Goal, deadline, price, max turns, no-progress.
ager_version: "0.3.0"
scope: graph
priority: [goal, deadline, price, max_turns, no_progress]
controls:
  - type: goal
    id: goal_pass
    expression: "state.judgment.pass == true"
  - type: deadline
    id: wall_clock
    max_ms: 600000
    on_hit: exhaust
  - type: price_budget
    id: cost_cap
    max: 2.5
    currency: USD
    includes: [model_tokens, tool_calls]
  - type: max_turns
    id: outer
    max: 6
    counter: outer_iteration
  - type: no_progress
    id: plateau
    metric: "state.judgment.score"
    window: 3
    min_delta: 0.02
    direction: increase
on_exhaust: return_best
on_goal: return
status: active
timestamp: 2026-08-04T00:00:00Z
---

# Loop policy

Evaluate after turns, tools, and judgments as configured.
