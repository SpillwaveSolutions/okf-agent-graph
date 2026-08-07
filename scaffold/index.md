---
okf_version: "0.2"
ager_version: "0.3.0"
type: Reference
title: "{{TITLE}}"
description: Self-describing multi-agent research graph with loop controls, tools, lineage KV, and ops policies.
timestamp: {{TIMESTAMP}}
status: active
tags: [sample, ager, research]
verified: true
links:
  - target: /agents/lead-researcher.md
    rel: related_to
  - target: /runtime/agent-graph.md
    rel: implements
---

# {{TITLE}}

Depends on **okf-graph-eng** for `validate` / `impact` / `pack`.

## Layout

- [AgentGraph](/runtime/agent-graph.md)
- [Lead](/agents/lead-researcher.md) · [Worker](/agents/worker.md) · [Judge](/agents/judge.md) · [Synthesizer](/agents/synthesizer.md)
- [LoopPolicy](/runtime/loop-policy.md) · [ScratchPad](/runtime/scratchpad.md)
- [FailurePolicy](/ops/failure-policy.md) · [Trigger](/ops/trigger-on-plan.md)
- [Tool web_search](/tools/web-search.md)
- [KnowledgeBind](/memory/knowledge-project.md)
