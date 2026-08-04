# LoopControls

| type | Key fields | Stops when |
|------|------------|------------|
| goal | expression | predicate true (success) |
| deadline | max_ms or deadline_at | wall clock exceeded |
| price_budget | max, currency, includes | cost ≥ max |
| max_turns | max, counter | counter ≥ max |
| no_progress | metric, window, min_delta | plateau |

Default priority: goal → deadline → price → max_turns → no_progress.

Expression context: `state`, `scratchpad`, `run.cost`, `run.turns`, `run.elapsed_ms`, `agent`, `last_output`, `now`.
