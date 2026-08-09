# Framework detectors → AGER

| Detector id | Signals (examples) | Maps to AGER |
|-------------|-------------------|--------------|
| langgraph | `StateGraph`, `add_conditional_edges` | AgentGraph, ControlEdge, LoopControl |
| langchain | `ChatPromptTemplate`, `create_react_agent` | AgentNode, Tool, Prompt |
| crewai | `Crew(`, `Process.hierarchical` | OrchestratorAgent, WorkerAgent |
| llamaindex | `AgentWorkflow`, `FunctionAgent` | AgentNode, RetrievalBinding |
| openai-agents | `Runner.run`, `handoffs` | AgentNode, HandoffPolicy |
| openai-api | `chat.completions.create`, `OpenAI(` | AgentNode, SystemPrompt, Tool |
| anthropic-sdk | `messages.create`, `tool_use` | AgentNode, SystemPrompt, Tool |
| claude-agent-sdk | `claude-agent-sdk`, `ClaudeSDKClient` | Harness loop, ToolRule |
| deepagents | `create_deep_agent` | Orchestrator, ScratchPad, subagents |
| mcp | `mcpServers`, JSON-RPC `2.0`, `list_tools` | Tool, schemas, SecretRef |
| bedrock-agentcore | `AgentCore`, `bedrock-agent-runtime` | Run, CheckpointPolicy |
| azure-ai-agents | `AzureAIAgent`, `AIProjectClient` | AgentNode, Run |
| vertex-agent-engine | `AgentEngine`, `ReasoningEngine` | AgentNode, Run |
| firecracker / gvisor / kata / e2b | microVM / runsc / kata / Sandbox.create | ContextIsolationPolicy |

Reverse engineering is many-to-one: multiple frameworks can contribute evidence
for the same AGER concept. Prefer AGER as the portable source of truth after capture.
