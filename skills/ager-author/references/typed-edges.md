# AGER typed edges

| rel | Meaning |
|-----|---------|
| routes_to | Control-flow next |
| delegates_to / spawns | Orchestrator → worker |
| judges | Judge → producer |
| aggregates_from | Synthesizer fan-in |
| fans_out_to / fans_in_from | Parallel map/join |
| handoffs_to | Peer ownership |
| guards | Guardrail |
| reads_from / writes_to / appends_to | ScratchPad KV |
| records_to | Auto output recording |
| uses / blocks | Agent→Tool / ToolRule→Tool |
| controlled_by / budgets | LoopPolicy |
| on_failure / retries_with / compensates_with | Ops |
| triggered_by | Run←Trigger |
| derived_from / output_of | Lineage |
| retrieves_from | Knowledge/RAG |
| binds_secret | SecretRef |
| rate_limited_by | Quotas |
| depends_on / implements / related_to | Soft/hard links |
