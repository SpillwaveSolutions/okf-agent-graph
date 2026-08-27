# AGENTS.md — okf-agent-graph

Grok Build / multi-agent host conventions (dual-host with Claude plugins).

## Plugin

- Name: `okf-agent-graph`
- Depends on: `okf-graph-eng` (SpillwaveSolutions/okf-plugin)
- Hosts: Claude Code, Grok Build, Codex, Agent Plugins 1.0, Grok Bot, LangChain Deep Agents
- Isolation: `docs/ISOLATION.md`. Open `/ager-session` before writing a shared second brain.

## When editing

- Keep sample-ager valid as OKF
- Reverse engineering (AGKC): skills ager-scan / ager-reverse-engineer; scripts ager_scan.py, ager_capture.py, ager_reverse_engineer.py, ager_plugins.py
- Keep fixture tests/fixtures/agent-repo and tests/fixtures/plugin-repo green via tests/test_ager_scan.py
- Update ager_version when breaking schema
- Cross-link wiki_ticket_sdd only for Trigger examples

<!-- worklog:policy:start -->
## Work tracking policy

- Capture every approved plan with `bin/worklog plan-capture` before implementation.
- Record discovered work with `bin/worklog add --unplanned --discovered-during <item>` before doing it.
- Never hand-edit `.work/*.jsonl` or `docs/roadmap.md`; use `bin/worklog` and `bin/worklog roadmap-render`.
- Commit worklog events and the regenerated roadmap together.
- Use one assistant session per working directory; create a separate worktree for concurrent sessions.
<!-- worklog:policy:end -->
