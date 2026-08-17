#!/usr/bin/env python3
"""Plugin packaging, release-version, and canonical-source invariants."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION = "0.6.2"


class PluginPackagingTests(unittest.TestCase):
    def test_manifest_versions_stay_in_lockstep(self) -> None:
        claude = json.loads((REPO / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((REPO / ".codex-plugin/plugin.json").read_text())
        claude_market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
        grok = json.loads((REPO / ".grok-plugin/marketplace.json").read_text())
        root_market = json.loads((REPO / "marketplace.json").read_text())
        found = {
            claude["version"], codex["version"],
            claude_market["plugins"][0]["version"], grok["version"],
            grok["plugins"][0]["version"], root_market["plugins"][0]["version"],
        }
        self.assertEqual(found, {VERSION})

    def test_readme_and_changelog_advertise_release(self) -> None:
        self.assertIn(f"| **Version** | {VERSION} |", (REPO / "README.md").read_text())
        changelog = (REPO / "CHANGELOG.md").read_text()
        self.assertRegex(
            changelog,
            rf"(?m)^## {re.escape(VERSION)} — (?:unreleased|\d{{4}}-\d{{2}}-\d{{2}})$",
        )

    def test_codex_manifest_paths_resolve(self) -> None:
        manifest = json.loads((REPO / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "okf-agent-graph")
        self.assertTrue((REPO / manifest["skills"]).is_dir())
        self.assertNotIn("hooks", manifest)

    def test_skill_frontmatter_has_codex_required_fields(self) -> None:
        for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
            text = skill.read_text()
            match = re.match(r"^---\n(.*?)\n---", text, re.S)
            self.assertIsNotNone(match, skill)
            block = match.group(1)
            self.assertRegex(block, r"(?m)^name: [a-z0-9-]+$")
            self.assertRegex(block, r"(?m)^description: .+$")

    def test_scaffold_is_the_only_template_source(self) -> None:
        self.assertTrue((REPO / "scaffold/agents/worker.md").is_file())
        self.assertFalse((REPO / "skills/ager-author/templates").exists())
        self.assertFalse((REPO / "skills/ager-init-graph/templates").exists())


if __name__ == "__main__":
    unittest.main()
