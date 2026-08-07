---
type: Trigger
title: On WikiTicket plan capture
ager_version: "0.3.0"
kind: ticket_event
graph: /runtime/agent-graph.md
filter:
  event: plan_captured
input_template:
  plan_path: "${event.plan_path}"
  worklog_id: "${event.epic}"
enabled: true
status: active
timestamp: {{TIMESTAMP}}
links:
  - target: /runtime/agent-graph.md
    rel: related_to
---

# Trigger

Requires [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) events when used in production.
