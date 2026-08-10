---
name: ager-scan
description: Scan a codebase for agent frameworks, prompts, tools, MCP, loops, and harness signals.
---

Follow the **ager-scan** skill completely.

1. Load `${CLAUDE_PLUGIN_ROOT}/skills/ager-scan/SKILL.md`.
2. Resolve the source root from the user (default: current project root).
3. Run `scripts/ager_scan.py` and report frameworks + findings summary.
