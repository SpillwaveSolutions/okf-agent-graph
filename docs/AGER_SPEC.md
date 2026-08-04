# AGER Specification v0.3.0

**OKF Agent Graph Engineering Runtime** — portable multi-agent loop config as OKF.

Spec id: `okf-ager` · `ager_version: "0.3.0"`

## Design principles

1. **Config, not framework** — concepts map to LangGraph / CrewAI / OpenAI Agents / Anthropic patterns via adapters  
2. **Contracts first** — every AgentNode and Tool has JSON Schema I/O  
3. **Loop engineering** — explicit LoopControls  
4. **Salient KV** — ScratchPad stores plans and agent outputs (lists), not full transcripts  
5. **Ops under uncertainty** — failure, retry, deadline, lineage, secrets  

## Four planes

### 1. Core graph

| Type | Role |
|------|------|
| AgentNode | Base executable unit |
| OrchestratorAgent | Plan / spawn / re-plan |
| WorkerAgent | Isolated doer |
| JudgeAgent | Rubric scorer |
| SynthesizerAgent | Fan-in reduce |
| RouterAgent | Route only |
| GuardrailAgent | I/O validation |
| HumanGate | Approval interrupt |
| AgentGraph | Load root |
| AgentGraphModule | Versioned subgraph |
| FanOut / FanIn / ParallelGroup | Parallel topology |
| ControlEdge | Conditional edge |
| InputSchema / OutputSchema | JSON Schema contracts |

### 2. Control

| Type | Role |
|------|------|
| LoopPolicy | Binds controls + on_exhaust / on_goal |
| LoopControl | `goal` \| `deadline` \| `price_budget` \| `max_turns` \| `no_progress` |

Default check order: **goal → deadline → price → max_turns → no_progress**.

### 3. Memory

| Type | Role |
|------|------|
| ScratchPad | Run KV: set / append; lineage on writes |
| LineageRecord | Provenance event |
| EpisodeStore | Cross-run summaries |
| KnowledgeBind | OKF/wiki long-term knowledge root |
| RetrievalBinding | How agents query memory tiers |
| SharedChannel | Framework-native reducers |
| MemoryArtifact | Large blob by ref |
| ContextIsolationPolicy | Subagent context walls |

### 4. Ops / action

| Type | Role |
|------|------|
| Tool | Schemas, cost, rules, idempotency, secrets |
| ToolRule | Expression → block / allow / require_human / rewrite_args |
| SecretRef | Vault pointer only |
| RateLimit / ConcurrencyLimit | Quotas |
| Run | Execution instance + status machine |
| Trigger | manual / webhook / cron / ticket_event / okf_change / ci |
| FailurePolicy | Error class → route |
| RetryPolicy | Backoff / jitter |
| Compensation | Saga undo |
| CircuitBreaker / DeadLetter | Resilience |
| DataClassPolicy | public/internal/pii/secret |
| CheckpointPolicy / RunTrace / StreamPolicy | Durability & observability |
| HandoffPolicy | Peer ownership transfer |
| Rubric / Criterion / Judgment / EvalSuite | Evaluation |

## Typed edges (AGER additions)

`routes_to`, `delegates_to`, `spawns`, `judges`, `aggregates_from`, `fans_out_to`, `fans_in_from`, `handoffs_to`, `guards`, `reads_from`, `writes_to`, `appends_to`, `records_to`, `models_with`, `isolates_context`, `uses`, `blocks`, `budgets`, `controlled_by`, `retries_with`, `compensates_with`, `on_failure`, `triggered_by`, `derived_from`, `output_of`, `retrieves_from`, `rate_limited_by`, `binds_secret`, `depends_on`, `implements`, `related_to`

## Framework crosswalk (summary)

| AGER | Anthropic | LangGraph | CrewAI | OpenAI |
|------|-----------|-----------|--------|--------|
| OrchestratorAgent | Lead | Supervisor | manager_agent | Triage / agents-as-tools |
| WorkerAgent | Subagent | Send worker | Agent | Specialist |
| LoopControl | Budgets | Recursion + breaks | Max iter | Max turns |
| ScratchPad KV | Artifacts/memory | State channels | Memory | Session |
| Tool + rules | Permissions | ToolNode hooks | Tools | Functions + guardrails |
| Run + Trigger | Job/session | thread invoke | kickoff | Runner.run |
| HumanGate | Review | interrupt() | Human input | Approvals |

## Normative frontmatter (common)

```yaml
type: <ConceptType>
title: string
description: string
tags: [string]
timestamp: ISO-8601
status: draft | active | deprecated
ager_version: "0.3.0"
okf_version: "0.2"   # on bundle index
links:
  - target: /absolute/path.md
    rel: <RelType>
```

See `sample-ager/` for a complete worked research graph.
