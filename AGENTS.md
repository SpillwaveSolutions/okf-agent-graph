# AGENTS.md — okf-agent-graph

Grok Build / multi-agent host conventions (dual-host with Claude plugins).

## Plugin

- Name: `okf-agent-graph`
- Depends on: `okf-graph-eng` (SpillwaveSolutions/okf-plugin)

## When editing

- Keep sample-ager valid as OKF
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
