# CLAUDE.md — okf-agent-graph

Claude Code conventions for this plugin repo.

## Dependency

Always assume **okf-graph-eng** from https://github.com/SpillwaveSolutions/okf-plugin is installed for validate/impact/pack.

## AGER

- Spec version **0.3.0** — see docs/AGER_SPEC.md
- Sample bundle: sample-ager/
- Skills: ager-init-graph, ager-author, ager-validate, ager-compile, ager-scan, ager-reverse-engineer
- Reverse engineering docs: docs/REVERSE_ENGINEERING.md

## Rules

- Absolute links in OKF bundles
- No inline secrets
- Prefer append list KV for multi-agent outputs

<!-- worklog:policy:start -->
## Work tracking policy

- Every plan MUST end by running `worklog plan-capture` — it writes
  `docs/plans/<date>-<slug>.md` and appends the plan's steps as work items.
- Work discovered mid-flight that wasn't in the plan: run
  `worklog add --unplanned --discovered-during <item>` BEFORE doing the work.
- Never hand-edit `.work/*.jsonl` (use `worklog`) or `docs/roadmap.md`
  (it is generated; change the work items instead).
- After changing work items, run `worklog roadmap-render` and commit the log
  and roadmap together.
- One session per working directory. Two assistant sessions sharing a checkout
  switch branches under each other and solve the same problem twice; give each
  its own `git worktree`. `worklog` warns when it sees more than one, but the
  warning is advisory and arrives after the fact.
<!-- worklog:policy:end -->
