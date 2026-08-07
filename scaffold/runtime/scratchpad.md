---
type: ScratchPad
title: Run KV scratchpad
description: set/append working memory with lineage.
ager_version: "0.3.0"
backend: memory
namespace: runs/${run_id}/kv
lineage: full
max_list_len: 100
default_record_mode: append
status: active
timestamp: {{TIMESTAMP}}
---

# ScratchPad KV

| Key | Mode | Purpose |
|-----|------|---------|
| plan | set | Strategy |
| worker_outputs | append | Worker results |
| judgments | append | Score history |
| best_draft | set | Best candidate |
