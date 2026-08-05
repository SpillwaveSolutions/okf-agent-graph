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
timestamp: 2026-08-04T00:00:00Z
links:
  - target: /runtime/agent-graph.md
    rel: related_to
---

# Trigger

Requires [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd) events when used in production.
