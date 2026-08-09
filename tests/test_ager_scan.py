#!/usr/bin/env python3
"""Tests for AGER reverse-engineering scan + capture."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests/fixtures/agent-repo"
SCAN = REPO / "scripts/ager_scan.py"
CAPTURE = REPO / "scripts/ager_capture.py"
REVERSE = REPO / "scripts/ager_reverse_engineer.py"


def run_json(*args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"non-JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from exc
    return proc, payload


class AgerScanTests(unittest.TestCase):
    def test_fixture_detects_major_frameworks(self) -> None:
        proc, payload = run_json(sys.executable, SCAN, "--root", FIXTURE, "--json")
        self.assertEqual(proc.returncode, 0, payload)
        frameworks = set(payload["frameworks"])
        for required in {
            "langgraph",
            "langchain",
            "crewai",
            "anthropic-sdk",
            "claude-agent-sdk",
            "mcp",
        }:
            self.assertIn(required, frameworks, frameworks)
        kinds = {f["kind"] for f in payload["findings"]}
        for required_kind in {
            "framework",
            "system_prompt",
            "tool",
            "mcp",
            "graph",
            "loop",
            "orchestration",
            "sandbox",
            "hyperscaler",
        }:
            self.assertIn(required_kind, kinds, kinds)
        self.assertGreaterEqual(payload["summary"]["findings"], 10)

    def test_reverse_engineer_writes_draft_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ager-re-") as temp:
            out = Path(temp) / "discovered"
            proc, payload = run_json(
                sys.executable,
                REVERSE,
                "--root",
                FIXTURE,
                "--out",
                out,
                "--title",
                "Fixture Agent Graph",
                "--scan-json",
                out / "scan.json",
                "--json",
            )
            self.assertEqual(proc.returncode, 0, payload)
            self.assertTrue((out / "index.md").is_file())
            self.assertTrue((out / "discoveries/index.md").is_file())
            self.assertTrue((out / "frameworks/index.md").is_file())
            self.assertTrue((out / "capture-report.json").is_file())
            self.assertTrue((out / "scan.json").is_file())
            index = (out / "index.md").read_text(encoding="utf-8")
            self.assertIn('ager_version: "0.3.0"', index)
            self.assertIn("Fixture Agent Graph", index)
            self.assertIn("langgraph", index)
            self.assertGreaterEqual(len(payload["capture"]["files_written"]), 8)

    def test_capture_from_existing_scan_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ager-cap-") as temp:
            scan_path = Path(temp) / "scan.json"
            out = Path(temp) / "out"
            proc, scan = run_json(sys.executable, SCAN, "--root", FIXTURE, "--json", "-o", scan_path)
            self.assertEqual(proc.returncode, 0, scan)
            proc2, report = run_json(
                sys.executable,
                CAPTURE,
                "--scan-json",
                scan_path,
                "--out",
                out,
                "--title",
                "From Scan",
                "--json",
            )
            self.assertEqual(proc2.returncode, 0, report)
            self.assertTrue((out / "tools/index.md").is_file())
            self.assertTrue((out / "mcp/index.md").is_file())


class PluginSurfaceTests(unittest.TestCase):
    def test_reverse_skills_and_commands_exist(self) -> None:
        self.assertTrue((REPO / "skills/ager-scan/SKILL.md").is_file())
        self.assertTrue((REPO / "skills/ager-reverse-engineer/SKILL.md").is_file())
        self.assertTrue((REPO / "commands/ager-scan.md").is_file())
        self.assertTrue((REPO / "commands/ager-reverse-engineer.md").is_file())
        self.assertTrue((REPO / "agents/agent-graph-re-orchestrator.md").is_file())
        self.assertTrue((REPO / "docs/REVERSE_ENGINEERING.md").is_file())


if __name__ == "__main__":
    unittest.main()
