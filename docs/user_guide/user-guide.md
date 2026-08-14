---
doc_type: guide
title: User Guide
slug: user-guide
wiki_key: guide/user-guide
truth_state: current
---

# AGER user guide

AGER (`okf-agent-graph`) helps you scaffold, author, validate, and map portable
multi-agent graphs expressed as OKF Markdown and YAML.

Plugin release **0.5.0** implements AGER document schema **0.3.0**. These
versions intentionally differ: upgrading the plugin does not change the
document schema unless `ager_version` changes.

## Prerequisite

AGER depends on
[`okf-graph-eng`](https://github.com/SpillwaveSolutions/okf-plugin) for full
OKF link validation, impact analysis, packing, edge queries, and visualization.
Install or load it before `okf-agent-graph`. The dependency-free AGER validator
still works without it, but does not replace full OKF graph validation.

## Install

### Claude Code

```bash
claude plugin marketplace add SpillwaveSolutions/okf-plugin
claude plugin install okf-graph-eng@okf-plugin-marketplace
claude plugin marketplace add SpillwaveSolutions/okf-agent-graph
claude plugin install okf-agent-graph@okf-agent-graph-marketplace
```

Start a new session after installation. The plugin exposes `/ager-init`,
`/ager-author`, `/ager-validate`, `/ager-compile`, `/ager-scan`, and `/ager-reverse-engineer`.

### Codex

Install the AGER plugin normally:

```bash
codex plugin marketplace add SpillwaveSolutions/okf-agent-graph
codex
```

Open `/plugins`, install `okf-agent-graph`, and start a new session. Codex uses
`$ager-init-graph`, `$ager-author`, `$ager-validate`, `$ager-compile`, `$ager-scan`, and `$ager-reverse-engineer`.
The pinned `okf-plugin` v0.3.2 dependency does not ship a Codex manifest. For
full OKF validation, use an `okf` executable, a sibling `../okf-plugin`
checkout, or an explicitly supplied path to `okf-graph.py`.

### Grok Build

Grok Build consumes the Claude-compatible plugin packaging. Load
`okf-graph-eng` first and `okf-agent-graph` second. The repository also ships
optional native metadata in `.grok-plugin/marketplace.json`; this project does
not document a separate Grok CLI installation command.

## Create your first graph

Choose a new destination such as `agent-graph/`. The initializer deliberately
refuses to overwrite an existing destination. Invoke `/ager-init` in Claude
Code or Grok Build, or `$ager-init-graph` in Codex, and ask for a title such as
“My agent graph.”

The generated bundle contains:

```text
agent-graph/
├── index.md
├── log.md
├── agents/
├── runtime/
├── ops/
├── evaluation/
├── memory/
├── tools/
├── models/
├── patterns/
├── prompts/
└── schemas/
```

The root `index.md` must retain:

```yaml
okf_version: "0.2"
ager_version: "0.3.0"
```

AGER references are root-relative to the bundle:

```yaml
entry: /agents/lead-researcher.md
loop_policy: /runtime/loop-policy.md
```

## Author the graph

Invoke `/ager-author` in Claude Code or Grok Build, or `$ager-author` in Codex.
Describe the concept to add or change and name the bundle.

1. Define the `AgentGraph` and its entry agent.
2. Add orchestrator, worker, synthesizer, and judge agents as needed.
3. Give every agent an input schema and output schema.
4. Add a `LoopPolicy` with applicable goal, deadline, price, turn, and
   no-progress controls.
5. Define `ScratchPad` keys and use append mode for parallel worker and judge
   output.
6. Add tools, rules, failure and retry policies, triggers, retrieval bindings,
   and evaluation rubrics.
7. Update the nearest `index.md` catalog and append an entry to `log.md`.

Parallel workers and judges use append semantics:

```yaml
record_output_to:
  key: worker_outputs
  mode: append
```

Never place credentials directly in an AGER document. Refer to a `SecretRef`
path instead.

## Validate

Invoke `/ager-validate` in Claude Code or Grok Build, or `$ager-validate` in
Codex. Validation has two layers:

1. AGER structural validation checks document types, required fields, versions,
   controls, schema references, output modes, tool safety, and inline secrets.
2. `okf-graph-eng` validates links and the wider OKF graph.

Both layers should pass before the bundle is committed or compiled. From a
source checkout:

```bash
python3 scripts/ager-validate.py agent-graph --strict
python3 ../okf-plugin/scripts/okf-graph.py validate agent-graph --strict
```

If the OKF CLI is installed on `PATH`, the second command can be:

```bash
okf validate agent-graph --strict
```

The AGER validator emits JSON and returns a nonzero status for errors. With
`--strict`, warnings also fail.



## Reverse engineer an existing agent project

When the system already lives in LangGraph, CrewAI, LlamaIndex, raw Claude/OpenAI
APIs, Claude Agent SDK, MCP configs, or a hyperscaler agent runtime, use AGKC:

```bash
python3 scripts/ager_scan.py --root /path/to/project --json -o scan.json
python3 scripts/ager_reverse_engineer.py --root /path/to/project --out discovered-ager --json
```

Or invoke `/ager-scan` and `/ager-reverse-engineer`. Review the draft bundle,
promote concepts with `/ager-author`, then validate. Full guide:
[[Reverse-Engineering]].

## Compile adapter guidance

Invoke `/ager-compile` in Claude Code or Grok Build, or `$ager-compile` in
Codex. Choose `langgraph`, `crewai`, `openai`, `anthropic`, or `custom`.

Compilation maps AGER concepts to framework primitives, including nodes, loop
controls, state channels, tool guardrails, and failure handling. It is adapter
guidance, not a production runtime generator. By default it produces mapping
notes or comment-and-signature stubs.

## Use the scripts directly

```bash
python3 scripts/ager-init.py agent-graph --title "My agent graph"
python3 scripts/ager-validate.py agent-graph --strict
```

`ager-init.py` stages the scaffold, performs strict AGER validation, and
installs the finished bundle atomically. It does not overwrite an existing
destination. There are no standalone `ager-author.py` or `ager-compile.py`
scripts in this release; those workflows are skill-driven.

## Explore the sample

The repository's `sample-ager/` is a complete research graph with an
orchestrator, parallel workers, synthesis, judgment, all five loop controls,
append-only outputs, ScratchPad lineage, failure and retry policies, a trigger,
tool rules, retrieval bindings, schemas, and a quality rubric.

```bash
python3 scripts/ager-validate.py sample-ager --strict
python3 ../okf-plugin/scripts/okf-graph.py validate sample-ager --strict
```

Start with `sample-ager/index.md`, `sample-ager/runtime/agent-graph.md`, and
`sample-ager/runtime/loop-policy.md`.

## Troubleshooting

### The destination already exists

Choose a new directory or deliberately move the existing directory first. The
initializer will not overwrite content.

### AGER validation passes but full graph validation did not run

Install or locate `okf-graph-eng`, then run `okf validate` or its
`okf-graph.py` script separately.

### Strict mode fails on warnings

Review the JSON `issues` array. A production-style loop should include goal,
deadline, price-budget, maximum-turn, and no-progress controls.

### A reference target does not exist

Paths beginning with `/` resolve from the bundle root, not the filesystem root.
Verify the file exists inside the bundle and JSON schemas contain valid JSON.

### An agent is missing a schema

Agent documents require `input_schema` and `output_schema`.

### A worker or judge fails output validation

Workers and judges must record parallel output with `mode: append`, preventing
one result from replacing another.

### A tool is rejected as unsafe

An irreversible tool needs `dual_control: true`, a compensation reference, or
a rule with `action: require_human`.

### A secret-like field is rejected

Do not embed passwords, tokens, API keys, or secret values. Use a `SecretRef`
path or environment substitution.

### The bundle reports an incompatible version

AGER concepts and the bundle root use `ager_version: "0.3.0"`. The plugin
package version is `0.4.0`; do not copy it into `ager_version`.

## Further reading

[[CLI-Reference]] · [[Plugin-Guide]] · [[AGER-Specification]] ·
[[Design-Doc]] · [[Code-Walkthrough]]
