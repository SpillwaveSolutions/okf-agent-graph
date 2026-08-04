---
type: Reference
title: Pattern orchestrator-workers
description: Lead spawns parallel workers; KV list fan-in; judge under controls.
ager_version: "0.3.0"
status: active
timestamp: 2026-08-04T00:00:00Z
tags: [pattern]
---

# Orchestrator–Workers

1. Trigger → Run  
2. Orchestrator plans → ScratchPad set  
3. Fan-out workers → append worker_outputs  
4. Synthesizer → Judge  
5. LoopControls / FailurePolicy bound the Run  
