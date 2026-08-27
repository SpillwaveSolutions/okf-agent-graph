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
PLUGIN_FIXTURE = REPO / "tests/fixtures/plugin-repo"
SCAN = REPO / "scripts/ager_scan.py"
CAPTURE = REPO / "scripts/ager_capture.py"
REVERSE = REPO / "scripts/ager_reverse_engineer.py"
SCRIPTS = REPO / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ager_plugins import classify_agent_role, parse_frontmatter  # noqa: E402


def run_json(*args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"non-JSON from {args}: {proc.stdout!r} {proc.stderr!r}") from exc
    return proc, payload


def _by_name(findings: list[dict], name: str) -> dict:
    matches = [
        f
        for f in findings
        if f.get("name") == name or f.get("title") == name
    ]
    assert matches, f"no finding named {name!r} in {[f.get('name') or f.get('title') for f in findings]}"
    return matches[0]


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
                "--author",
                "claude-code/lumenfield-detector",
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
            self.assertIn("author: \"claude-code/lumenfield-detector\"", index)
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
                "--author",
                "claude-code/lumenfield-detector",
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


class FrontmatterAndRoleTests(unittest.TestCase):
    def test_parse_tools_csv_and_list(self) -> None:
        meta, body = parse_frontmatter(
            "---\nname: enhancer-judge\ntools: Read, Grep, Glob\n---\n\nHello\n"
        )
        self.assertEqual(meta["name"], "enhancer-judge")
        self.assertEqual(meta["tools"], ["Read", "Grep", "Glob"])
        self.assertIn("Hello", body)

        meta, _ = parse_frontmatter(
            "---\nname: x\ntools:\n  - Read\n  - Write\n---\n\n"
        )
        self.assertEqual(meta["tools"], ["Read", "Write"])

        meta, _ = parse_frontmatter("---\nname: y\ntools: [Read, Edit]\n---\n\n")
        self.assertEqual(meta["tools"], ["Read", "Edit"])

    def test_classify_enhancer_roles(self) -> None:
        self.assertEqual(
            classify_agent_role(
                name="enhancer-judge",
                description="Never writes anything, never grades its own draft.",
                body="You are the judge.",
                tools=["Read", "Grep", "Glob"],
                kind="agent",
            ),
            "JudgeAgent",
        )
        self.assertEqual(
            classify_agent_role(
                name="enhancer-doer",
                description=(
                    "Holds no write tool of any kind; its draft is the text of its "
                    "final reply, for the enhancer-loop orchestrator to write."
                ),
                body="You are the doer.",
                tools=["Read", "Grep", "Glob"],
                kind="agent",
            ),
            "WorkerAgent",
        )
        self.assertEqual(
            classify_agent_role(
                name="enhancer-loop",
                description="You are the orchestrator. You are the only role in this loop that writes the real ticket file.",
                body="You are the orchestrator.",
                tools=[],
                kind="skill",
            ),
            "OrchestratorAgent",
        )


class PluginDiscoveryTests(unittest.TestCase):
    def test_discovers_claude_grok_codex_and_universal_plugins(self) -> None:
        proc, payload = run_json(sys.executable, SCAN, "--root", PLUGIN_FIXTURE, "--json")
        self.assertEqual(proc.returncode, 0, payload)
        frameworks = set(payload["frameworks"])
        for required in {
            "claude-code-plugin",
            "grok-plugin",
            "codex-plugin",
            "agent-plugins",
        }:
            self.assertIn(required, frameworks, frameworks)

        findings = payload["findings"]
        judge = _by_name(findings, "enhancer-judge")
        self.assertEqual(judge["kind"], "agent")
        self.assertEqual(judge["role"], "JudgeAgent")
        self.assertEqual(judge["maps_to"], "JudgeAgent")
        self.assertEqual(judge["host"], "claude-code")
        self.assertEqual(set(judge["tools"]), {"Read", "Grep", "Glob"})

        doer = _by_name(findings, "enhancer-doer")
        self.assertEqual(doer["role"], "WorkerAgent")
        self.assertEqual(doer["maps_to"], "WorkerAgent")

        loop = _by_name(findings, "enhancer-loop")
        self.assertEqual(loop["kind"], "skill")
        self.assertEqual(loop["role"], "OrchestratorAgent")
        self.assertEqual(loop["maps_to"], "OrchestratorAgent")

        extra = _by_name(findings, "extra-worker")
        self.assertEqual(extra["host"], "claude-code")
        self.assertEqual(extra["role"], "WorkerAgent")
        self.assertIn("Write", extra["tools"])

        planner = _by_name(findings, "planner")
        self.assertEqual(planner["host"], "grok-build")
        self.assertEqual(planner["role"], "OrchestratorAgent")

        grok_reviewer = _by_name(findings, "grok-reviewer")
        self.assertEqual(grok_reviewer["host"], "grok-build")
        self.assertEqual(grok_reviewer["role"], "JudgeAgent")

        reviewer = _by_name(findings, "reviewer")
        self.assertEqual(reviewer["host"], "codex")
        self.assertEqual(reviewer["role"], "JudgeAgent")

        review_loop = _by_name(findings, "review-loop")
        self.assertEqual(review_loop["host"], "codex")
        self.assertEqual(review_loop["role"], "OrchestratorAgent")

        lead = _by_name(findings, "lead")
        self.assertEqual(lead["framework"], "agent-plugins")
        self.assertEqual(lead["role"], "OrchestratorAgent")

        ticket_loop = _by_name(findings, "ticket-loop")
        self.assertEqual(ticket_loop["role"], "OrchestratorAgent")

        tool_titles = {f["title"] for f in findings if f["kind"] == "tool"}
        for required_tool in {"Read", "Grep", "Glob", "Write", "Edit"}:
            self.assertIn(required_tool, tool_titles, tool_titles)
        self.assertFalse(any(t.startswith("Tool:") for t in tool_titles if t in {"Read", "Grep", "Glob"}))

        orch_noise = [
            f
            for f in findings
            if f["kind"] == "orchestration" and f["title"] == "Supervisor / orchestrator role"
            and f.get("path", "").startswith("solutions/sol1_enhancer/")
        ]
        self.assertEqual(orch_noise, [])

        plugin_names = {f["title"] for f in findings if f["kind"] == "plugin"}
        self.assertIn("sol1-enhancer", plugin_names)
        self.assertIn("universal-ticket-loop", plugin_names)
        self.assertIn("codex-review-loop", plugin_names)

        graphs = [f for f in findings if f["kind"] == "graph" and f.get("maps_to") == "AgentGraph"]
        self.assertGreaterEqual(len(graphs), 1, graphs)

    def test_reverse_engineer_emits_typed_agents_and_graphs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ager-plugin-re-") as temp:
            out = Path(temp) / "discovered"
            proc, payload = run_json(
                sys.executable,
                REVERSE,
                "--root",
                PLUGIN_FIXTURE,
                "--out",
                out,
                "--title",
                "Plugin Agent Graph",
                "--author",
                "claude-code/lumenfield-detector",
                "--scan-json",
                out / "scan.json",
                "--json",
            )
            self.assertEqual(proc.returncode, 0, payload)

            judge = (out / "agents/enhancer-judge.md").read_text(encoding="utf-8")
            self.assertRegex(judge, r'type: "?JudgeAgent"?')
            self.assertIn("title: \"enhancer-judge\"", judge)
            self.assertIn("Read", judge)

            doer = (out / "agents/enhancer-doer.md").read_text(encoding="utf-8")
            self.assertRegex(doer, r'type: "?WorkerAgent"?')

            loop = (out / "agents/enhancer-loop.md").read_text(encoding="utf-8")
            self.assertRegex(loop, r'type: "?OrchestratorAgent"?')

            self.assertTrue((out / "tools/read.md").is_file())
            read_tool = (out / "tools/read.md").read_text(encoding="utf-8")
            self.assertRegex(read_tool, r'type: "?Tool"?')
            self.assertIn('title: "Read"', read_tool)

            graph_files = list((out / "graphs").glob("*.md"))
            graph_files = [p for p in graph_files if p.name != "index.md"]
            self.assertTrue(graph_files, "expected at least one AgentGraph file")
            graph_bodies = "\n".join(p.read_text(encoding="utf-8") for p in graph_files)
            self.assertIn("type: \"AgentGraph\"", graph_bodies)
            self.assertIn("/agents/enhancer-judge.md", graph_bodies)
            self.assertIn("/agents/enhancer-doer.md", graph_bodies)
            self.assertIn("/agents/enhancer-loop.md", graph_bodies)

            pattern_files = list((out / "patterns").glob("*.md"))
            pattern_files = [p for p in pattern_files if p.name != "index.md"]
            self.assertLess(
                len(pattern_files),
                5,
                f"plugin markdown leaked into patterns/: {pattern_files}",
            )


if __name__ == "__main__":
    unittest.main()
