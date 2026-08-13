# Changelog

## 0.5.1 — 2026-08-13

- Register AGER types in `schemas/okf-concepts/registry.json` so a mixed
  second-brain `okf-graph.py validate` recognizes them (fallback: shared
  BaseConcept, required `type` + `title` only). Field-depth validation stays
  in `ager-validate.py`.

## 0.5.0 — 2026-08-09


- Add **AGKC reverse engineering** path: scan existing agent codebases and capture draft AGER knowledge.
- New scripts: `ager_scan.py`, `ager_capture.py`, `ager_reverse_engineer.py` (stdlib only).
- New skills/commands: `ager-scan`, `ager-reverse-engineer` (Claude `/…`, Codex `$…`).
- New agent: `agent-graph-re-orchestrator`.
- Detect LangGraph, LangChain, CrewAI, LlamaIndex, OpenAI/Claude APIs, Claude Agent SDK, Deep Agents, AutoGen, Semantic Kernel, MCP/JSON-RPC, Bedrock AgentCore, Azure AI Agents, Vertex Agent Engine, Firecracker/gVisor/Kata/E2B sandboxes.
- Extract prompts/system prompts, tools, schemas, graphs, loops, orchestration, hyperscaler + hardened runtime signals with provenance.
- Fixture agent repo + `tests/test_ager_scan.py` regression coverage.
- Docs: `docs/REVERSE_ENGINEERING.md`.

## 0.4.0 — 2026-08-06

- Add a complete canonical scaffold and atomic `ager-init.py` generator.
- Add dependency-free AGER structural validation with strict CI checks.
- Make the sample bundle pass strict AGER and OKF validation without warnings.
- Add native Codex plugin packaging while preserving Claude Code and Grok Build support.
- Initialize WikiTicket SDD for plans, tickets, roadmap, PR, and wiki synchronization.

## 0.3.0 — 2026-08-04

- Initial AGER plugin with skills, commands, specification, and worked sample graph.
