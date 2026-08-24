# Changelog

## Unreleased

- Noun-ownership migration guide:
  [`docs/user_guide/noun-ownership-migration.md`](docs/user_guide/noun-ownership-migration.md)
  (`WriteEvent` owner, unverified high-impact, okf-plugin v0.8.0 pin).

## 0.7.0 — 2026-08-24

### Added

- **Noun ownership.** AGER now ships JSON schemas for the full agent/harness
  set (51 types), including `AgentNode`, `Workflow`, `Harness`, `SharedState`,
  `ToolCapability`, loop/runtime/ops/eval types, with `x-impact` for the graph
  engine. `WriteEvent` stays in second-brain-core / the graph engine write
  journal; AGER does not own it.
- README lists every AGER noun.

### Changed

- Catalog / ContextPack stay in okf-plugin. Authoring AgentNode is no longer
  an okf-graph-eng concern.

## 0.6.4

- WikiTicket SDD (worklog) is the tracking system for this plugin.


## 0.6.3 — 2026-08-17

- **Cursor host.** `.cursor-plugin/plugin.json` (Cursor Plugins) plus `.cursor/rules/second-brain.mdc`. Docs: `docs/CURSOR.md`. `docs/GROK_BOT.md` now covers Grok Bot spawning Cursor cloud agents.

## 0.6.2 — 2026-08-16

- Local ContextPack: `scripts/ager_pack.py`, `/ager-pack`, `$ager-pack`.
- Default budget = 1/4 of `SECOND_BRAIN_WINDOW_TOKENS` (128000 → 32000).
- Override: `--max-tokens` / `SECOND_BRAIN_PACK_MAX_TOKENS`.
- **Fail-closed**: over-budget pack does not `--write`.
- Bodies off unless that node is the pack root. Neighbors keep title / type / path / description.
- Inbound typed edges are visible from the seed (same shape as PKC inbound index).
- Catalog `index.md` files and `write-events/` are not concepts.
- Node clip (`--max-nodes` / `--tiny`) is not a token budget.
- Implements part of [okf-plugin#55](https://github.com/SpillwaveSolutions/okf-plugin/issues/55).

## 0.6.1 — 2026-08-16

- Required identity on every knowledge write: `--author` or `SECOND_BRAIN_IDENTITY`.
- `ager_common.resolve_author()` fail-closes without a claim. Capture, reverse-engineer, and init stamp `author` and emit a `WriteEvent`.
- Scan / validate / print-only paths do not require identity.

## 0.6.0 — 2026-08-15

- **Multi-host bindings + write isolation.** Root Agent Plugins 1.0 `plugin.json`, Grok Bot / Deep Agents / isolation / onboarding docs, host wrappers, vendored `scripts/brain_session.py`, and `ager-session`.
- Concurrent writers read `main` and write `brain/<actor>/<session-id>`. Isolation tests use fictional **lumenfield-detector** / **northstar-console** only.
- LoopPolicy / KnowledgeBind: retrieve from `main`; persist loop/graph writes only in the session worktree.

## 0.5.1 — 2026-08-13

- Register AGER types in `schemas/okf-concepts/registry.json` so a mixed
  second-brain `okf-graph.py validate` recognizes them (fallback: shared
  BaseConcept, required `type` + `title` only). Field-depth validation stays
  in `ager-validate.py`.
- Land the v0.4.0 post-release wiki ledger (`.work/published.json`), freeze the
  dated design/code-walkthrough snapshots, ignore `.work/wiki-checkout/`, and
  correct Codex dependency guidance (okf-plugin v0.3.2 has no Codex manifest).
- Refresh `docs/.index/publish-manifest.json` so worklog `ia-render --check`
  matches the current spec and user-guide bodies.

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
