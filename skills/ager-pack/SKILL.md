---
name: ager-pack
description: Build a progressive-disclosure ContextPack from an AGER bundle. Default 1/4 window token budget, fail-closed. Bodies off unless that node is the pack root.
---

# AGER Pack

Local packer. Do not fall back to okf-graph-eng for auto-inject.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_pack.py" agents/lead-researcher.md --repo . --hops 2
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_pack.py" agents/lead-researcher.md --repo . --tiny
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ager_pack.py" agents/lead-researcher.md --repo . --mermaid
```

- Default budget = 1/4 of `SECOND_BRAIN_WINDOW_TOKENS` (128000 → 32000)
- Override: `--max-tokens` / `SECOND_BRAIN_PACK_MAX_TOKENS`
- Over budget is a hard fail. Do not `--write`. Node clip is not a token budget.
- Neighbors keep title / type / path / description. Full body only on the seed.
