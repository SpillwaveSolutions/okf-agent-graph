---
name: ager-compile
description: Map an AGER AgentGraph to a target framework (LangGraph, CrewAI, OpenAI Agents, Anthropic lead/subagents) and emit adapter notes or stub skeletons. Not a full codegen runtime.
---

# AGER Compile (adapter guidance)

## Steps

1. Load AgentGraph + linked agents, loop policy, tools, scratchpad.
2. Ask or detect target: `langgraph` | `crewai` | `openai` | `anthropic` | `custom`.
3. Emit mapping table:
   - nodes → framework primitives
   - LoopControls → recursion limits / break conditions
   - ScratchPad list keys → state channels / memory
   - Tool rules → pre-hooks / guardrails
   - FailurePolicy → retry nodes
4. Optional: write stub files under `adapters/<target>/` as **comments + signatures only** unless user asks for full code.
5. Never claim production-ready runtime without tests.

## Reference

- `references/framework-map.md`
