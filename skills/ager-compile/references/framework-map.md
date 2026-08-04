# Framework map

| AGER | LangGraph | CrewAI | OpenAI | Anthropic |
|------|-----------|--------|--------|-----------|
| AgentGraph | StateGraph | Crew | multi-agent setup | workflow definition |
| OrchestratorAgent | supervisor | manager_agent | triage / tools | lead agent |
| WorkerAgent | node / Send | Agent | specialist | subagent |
| FanOut | Send map | parallel tasks | parallel tools | parallel subagents |
| LoopControl | conditional + limits | max iter | max turns | stop heuristics |
| ScratchPad | state keys | memory | session | artifacts |
| ToolRule | pre-tool hook | tool wrap | guardrails | permissions |
| HumanGate | interrupt | human input | approval | external review |
| CheckpointPolicy | checkpointer | — | resumable runs | durable patterns |
