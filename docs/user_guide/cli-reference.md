---
wiki_key: guide/cli-reference
doc_type: guide
title: CLI Reference
slug: cli-reference
truth_state: current
---

# CLI reference

AGER v0.4.0 ships two dependency-free Python entry points. Run them from the
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

## Agent commands and skills

| Task | Claude Code / Grok Build | Codex |
|---|---|---|
| Scaffold | `/ager-init` | `$ager-init-graph` |
| Author concepts | `/ager-author` | `$ager-author` |
| Validate | `/ager-validate` | `$ager-validate` |
| Map to a framework | `/ager-compile` | `$ager-compile` |

The commands delegate to the corresponding skills. `ager-compile` emits
framework mapping guidance or stub signatures; it is not a production runtime
generator.

## Exit behavior

| Command | Exit 0 | Non-zero exit |
|---|---|---|
| `ager-init.py` | Bundle created and strict-valid | Destination exists or generated bundle is invalid |
| `ager-validate.py` | No errors; and no warnings in strict mode | Structural error, or warning in strict mode |
| `okf-graph.py validate` | OKF graph satisfies selected checks | Broken links, invalid edges, or strict warnings |

Next: [[User-Guide]] · [[AGER-Specification]] · [[Code-Walkthrough]]
