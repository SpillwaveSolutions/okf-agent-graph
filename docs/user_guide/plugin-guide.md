---
wiki_key: guide/plugin-guide
doc_type: guide
title: Plugin Guide
slug: plugin-guide
truth_state: current
---

# Plugin guide

`okf-agent-graph` is the AGER domain plugin. It supplies the AGER specification,
skills, canonical scaffold, generator, validator, and worked sample. The
required `okf-graph-eng` plugin supplies general OKF link validation, typed-edge
validation, impact analysis, packs, queries, and visualization.

## Install order

### Claude Code

```bash
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace
claude plugin marketplace add SpillwaveSolutions/okf-agent-graph
claude plugin install okf-agent-graph@okf-agent-graph-marketplace
```

Restart or open a new session after installation so the skills and commands are
discovered.

### Codex

```bash
codex plugin marketplace add SpillwaveSolutions/okf-agent-graph
codex
```

Open `/plugins`, install `okf-agent-graph`, and start a new session. The pinned
`okf-plugin` v0.3.2 dependency has no Codex manifest. For full OKF validation,
use an `okf` executable, a sibling `../okf-plugin` checkout, or an explicitly
supplied path to `okf-graph.py`.

### Grok Build

Grok Build consumes the Claude-compatible plugin layout. The repository also
ships `.grok-plugin/marketplace.json` with the dependency relationship declared.

## What is packaged

| Path | Purpose |
|---|---|
| `skills/ager-init-graph/` | Atomic scaffold workflow |
| `skills/ager-author/` | AGER concept and typed-edge authoring rules |
| `skills/ager-validate/` | AGER checks plus delegation to OKF validation |
| `skills/ager-compile/` | Framework crosswalk and adapter-stub guidance |
| `skills/ager-scan/` | Detect agent frameworks in an existing repo |
| `skills/ager-reverse-engineer/` | Capture a draft AGER bundle from code |
| `commands/` | Claude/Grok slash-command wrappers |
| `scaffold/` | The only canonical template tree |
| `sample-ager/` | Complete research graph example |
| `scripts/` | Direct generator, validator, and AGKC CLIs |

Claude, Codex, Grok, and root marketplace manifests all advertise plugin
version `0.5.0`. The document schema stays at `ager_version: "0.3.0"`; plugin
release versions and schema versions intentionally serve different purposes.

## Dependency resolution

AGER validation is self-contained. Full OKF validation looks for the graph
engine through an installed executable, a discoverable plugin root, a sibling
`../okf-plugin` checkout, or a path supplied by the user. If the dependency is
unavailable, run the local AGER validator and report that OKF link validation
was not performed.

## Updating the plugin

Keep all plugin manifest versions in lockstep. If a change breaks the AGER
document schema, update `ager_version`, the specification, scaffold, sample,
validator, and tests together. Non-breaking plugin features do not require a
schema-version bump.

Next: [[User-Guide]] · [[CLI-Reference]] · [[AGER-Specification]]
