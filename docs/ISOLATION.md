# Write isolation for OKF Agent Graph (AGER)

One shared institutional second brain. Many agents. Many machines. Many project worktrees.

AGER captures *how agents loop*: orchestrators, doers, judges, synthesizers, LoopPolicy, KnowledgeBind. Type ownership says *what* you may write. Isolation says *where concurrent sessions do not collide*.

## Protocol

```
read  → origin/main (shared truth) + optional session overlay
write → brain/<actor>/<session-id> worktree only
close → commit, push to the checkout's existing remote, open PR
merge → human or green auto-merge on non-overlapping paths
```

```bash
python3 scripts/brain_session.py open \
  --repo "$BRAIN_REPO" \
  --bundle knowledge \
  --actor grok-bot/okf-agent-graph \
  --plugin okf-agent-graph \
  --host grok-bot

# JSON includes SECOND_BRAIN_ROOT and BRAIN_SESSION_ID.

python3 scripts/brain_session.py close \
  --repo "$BRAIN_REPO" \
  --session <id>
```

Branch name: `brain/<sanitized-actor>/<session-id>`

Prefer this vendored helper. If `second-brain-core` is also installed, that copy is equivalent.

## Why not only flock-on-main

Flock serializes writers on one machine. It fails across machines, long thinking sessions, and cloud Grok Bots. Worktree + PR is the multi-agent protocol. Flock remains optional *inside* one worktree.

## Fictional multi-project example

Two agents share one institutional second brain while working on different product trees.

- Agent A (Claude Code) works **lumenfield-detector**.
- Agent B (Grok Bot) works **northstar-console**.

Both pack from `main`. When either writes an owned node, it opens `brain/<actor>/<session-id>`, writes only there, then closes with a PR.

Public docs, samples, and tests use only these fictional names. Real client project names are forbidden.

## Read freshness

- Shared truth: pack against `main` after a fast-forward pull.
- Session overlay: also see your own unmerged writes.
- Do not pack other agents' open branches by default.

## Conflicts

OKF concepts are one file per path. Two agents editing the same node will conflict. That is useful. Prefer creating new nodes. Catalog indexes are regenerated-friendly; treat them as derived when possible.

## Grok Bot (cloud)

No local worktree required. Same branch naming via GitHub. Or mount a box and give each bot session its own worktree. Do not solve isolation by making the knowledge repo public.

## Public pack surface

This document never names a private remote. The knowledge root is a path the human already has, or `SECOND_BRAIN_ROOT` / the active session bundle.


## LoopPolicy / KnowledgeBind

A lumenfield-detector loop and a northstar-console loop may both retrieve from the same institutional tree.

- **KnowledgeBind / RetrievalBinding** read from `main` (plus this session overlay).
- **LoopPolicy** writes (new loops, run records, captured reverse-engineered graphs) go only to the session worktree.
- Do not bind a loop's write root to another agent's open `brain/<actor>/...` branch.


## Related

- [second-brain-core docs/ISOLATION.md](https://github.com/SpillwaveSolutions/second-brain-core/blob/main/docs/ISOLATION.md)
- [GROK_BOT.md](GROK_BOT.md)
- [LANG_CHAIN_DEEP_AGENTS.md](LANG_CHAIN_DEEP_AGENTS.md)
