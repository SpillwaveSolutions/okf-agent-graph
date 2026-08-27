---
name: ager-reverse-engineer
description: End-to-end reverse engineer of agent codebases (Claude/ChatGPT APIs, LangChain/LangGraph, CrewAI, LlamaIndex, Claude Agent SDK, Deep Agents, MCP, AgentCore, microVMs) into a draft AGER OKF knowledge graph. Primary reverse entry skill for okf-agent-graph (AGKC).
---

# AGER Reverse Engineer (AGKC)

Populate **agent-graph knowledge** from an existing project that was *not* authored
as AGER — the inverse of `/ager-init` + `/ager-author`.

Pattern siblings:

- [system-architecture-capture](https://github.com/SpillwaveSolutions/system-architecture-capture) (SAC)
- [data-engineering-knowledge-capture](https://github.com/SpillwaveSolutions/data-engineering-knowledge-capture) (DEKC)

This skill is **AGKC** — Agent Graph Knowledge Capture — shipped inside `okf-agent-graph`.

## Process

1. Confirm source root(s) and a destination for the draft bundle (default `discovered-ager/`).
2. Run the orchestrator:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_reverse_engineer.py" \
  --root "$SOURCE_ROOT" \
  --out "$DEST_BUNDLE" \
  --title "$TITLE" \
  --scan-json "$DEST_BUNDLE/scan.json" \
  --json
```

When `$DEST_BUNDLE` is a subtree of a shared OKF bundle (typical: `knowledge/agent-graph` next to PKC/SAC packs), pass the bundle root so links resolve from there, not from the subtree:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_reverse_engineer.py" \
  --root "$SOURCE_ROOT" \
  --out knowledge/agent-graph \
  --bundle-root knowledge \
  --title "$TITLE" \
  --json
```

That writes `/agent-graph/tools/read.md` instead of `/tools/read.md`. `--link-prefix agent-graph` does the same when the bundle root is implied.

3. Review the draft tree:

```text
discovered-ager/
├── index.md
├── discoveries/
├── frameworks/
├── agents/            # typed WorkerAgent / JudgeAgent / OrchestratorAgent from plugins
├── skills/
├── prompts/ (+ system/)
├── tools/             # real tool names from frontmatter, not "Tool: …"
├── mcp/
├── graphs/            # AgentGraph nodes wiring plugin agents
├── patterns/
├── schemas/
├── runtime/ (loops, sandboxes, hyperscaler)
├── log.md
└── capture-report.json
```

4. Enrich with judgment (agent-graph-re-orchestrator / human):
   - promote Orchestrator / Worker / Judge roles
   - attach missing JSON Schema I/O
   - bind LoopControls (goal, deadline, price, max_turns, no_progress)
   - harden Tool rules, SecretRef, isolation policies
5. Optionally copy/promote into a full scaffold via **ager-init** + **ager-author**.
6. Validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager-validate.py" "$PROMOTED_BUNDLE" --strict
# plus okf-graph-eng when available:
# okf validate "$PROMOTED_BUNDLE" --strict
```

7. Report frameworks detected, key prompts/tools/MCP, orchestration shape, and runtime/harness notes.

## References

- `references/framework-detectors.md`
- `../../docs/REVERSE_ENGINEERING.md`
- `../../docs/AGER_SPEC.md`
- `../../skills/ager-compile/references/framework-map.md`
