---
wiki_key: guide/cli-reference
doc_type: guide
title: CLI Reference
slug: cli-reference
truth_state: current
---

# CLI reference

AGER ships dependency-free Python entry points. Run them from the
plugin repository, or replace the script paths with the installed plugin root.

## Scaffold a bundle

```bash
python3 scripts/ager-init.py <destination> --title "<graph title>"
```

`<destination>` must not already exist. The generator copies the canonical
`scaffold/` tree to a temporary directory, replaces the title and timestamp
placeholders, runs strict AGER validation, and installs the result atomically.
Success prints JSON containing the destination, file count, and validation
result. A validation error or existing destination produces a non-zero exit.

Example:

```bash
python3 scripts/ager-init.py agent-graph --title "Support triage graph"
```

## Validate a bundle

```bash
python3 scripts/ager-validate.py <bundle> [--strict]
```

The validator prints JSON on success and failure. Without `--strict`, errors
fail the command while warnings remain advisory. With `--strict`, warnings also
produce a non-zero exit code. The checks include:

- supported `ager_version` and known AGER concept types;
- required schemas and graph-control references;
- the complete recommended loop-control set;
- append-mode worker and judge outputs;
- safeguards for irreversible tools;
- secret-like values represented by references rather than inline values; and
- absolute bundle references that resolve to files, including valid JSON
  schemas.

Run OKF graph validation separately for link and typed-edge checks:

```bash
python3 ../okf-plugin/scripts/okf-graph.py validate <bundle> --strict
```

The OKF command is supplied by the required `okf-graph-eng` plugin, not by this
repository. See [[Plugin-Guide]] for installation and [[AGER-Specification]]
for the data contract.

## Pack a neighborhood

```bash
python3 scripts/ager_pack.py agents/lead-researcher.md --repo . --tiny
python3 scripts/ager_pack.py agents/lead-researcher.md --repo . --hops 2 --max-tokens 8000
```

Default budget is 1/4 of `SECOND_BRAIN_WINDOW_TOKENS` (128000 → 32000). Over
budget is a hard fail and `--write` is skipped. Neighbor bodies stay off unless
that node is the pack root. Node clip (`--max-nodes` / `--tiny`) is not a token
budget.

## Agent commands and skills

| Task | Claude Code / Grok Build | Codex |
|---|---|---|
| Scaffold | `/ager-init` | `$ager-init-graph` |
| Author concepts | `/ager-author` | `$ager-author` |
| Validate | `/ager-validate` | `$ager-validate` |
| Pack a neighborhood | `/ager-pack` | `$ager-pack` |
| Map to a framework | `/ager-compile` | `$ager-compile` |

The commands delegate to the corresponding skills. `ager-compile` emits
framework mapping guidance or stub signatures; it is not a production runtime
generator.

## Exit behavior

| Command | Exit 0 | Non-zero exit |
|---|---|---|
| `ager-init.py` | Bundle created and strict-valid | Destination exists or generated bundle is invalid |
| `ager-validate.py` | No errors; and no warnings in strict mode | Structural error, or warning in strict mode |
| `ager_pack.py` | Pack is under the token budget | Over budget (no `--write`) |
| `okf-graph.py validate` | OKF graph satisfies selected checks | Broken links, invalid edges, or strict warnings |

Next: [[User-Guide]] · [[AGER-Specification]] · [[Code-Walkthrough]]
