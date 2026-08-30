#!/usr/bin/env python3
"""Regression tests for AGER generation and structural validation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VALIDATOR = REPO / "scripts" / "ager-validate.py"
GENERATOR = REPO / "scripts" / "ager-init.py"
SAMPLE = REPO / "sample-ager"
OKF_GRAPH = Path(os.environ.get("OKF_GRAPH", REPO.parent / "okf-plugin/scripts/okf-graph.py"))


def run_json(*args: object) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    proc = subprocess.run([str(arg) for arg in args], capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"non-JSON output from {args}: {proc.stdout!r} {proc.stderr!r}") from exc
    return proc, payload


class AgerValidationTests(unittest.TestCase):
    def copy_sample(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory(prefix="ager-validation-")
        bundle = Path(temp.name) / "bundle"
        shutil.copytree(SAMPLE, bundle)
        return temp, bundle

    def assert_invalid(self, bundle: Path, message: str) -> None:
        proc, payload = run_json(sys.executable, VALIDATOR, bundle, "--strict")
        self.assertNotEqual(proc.returncode, 0, payload)
        messages = [issue["message"] for issue in payload["issues"]]
        self.assertTrue(any(message in value for value in messages), messages)

    def test_sample_passes_strict_ager_validation(self) -> None:
        proc, payload = run_json(sys.executable, VALIDATOR, SAMPLE, "--strict")
        self.assertEqual(proc.returncode, 0, payload)
        self.assertEqual(payload["issues"], [])

    @unittest.skipUnless(OKF_GRAPH.is_file(), "okf-graph.py dependency is unavailable")
    def test_sample_passes_strict_okf_validation(self) -> None:
        proc, payload = run_json(sys.executable, OKF_GRAPH, "validate", SAMPLE, "--strict")
        self.assertEqual(proc.returncode, 0, payload)
        self.assertEqual(payload["warn_count"], 0, payload["issues"])

    def test_missing_schema_reference_fails(self) -> None:
        temp, bundle = self.copy_sample()
        self.addCleanup(temp.cleanup)
        path = bundle / "agents/worker.md"
        path.write_text(path.read_text().replace("/schemas/task.schema.json", "/schemas/missing.json"))
        self.assert_invalid(bundle, "target does not exist")

    def test_missing_loop_control_fails_strict(self) -> None:
        temp, bundle = self.copy_sample()
        self.addCleanup(temp.cleanup)
        path = bundle / "runtime/loop-policy.md"
        text = path.read_text()
        start = text.index("  - type: deadline")
        end = text.index("  - type: price_budget")
        path.write_text(text[:start] + text[end:])
        self.assert_invalid(bundle, "missing recommended deadline control")

    def test_unsafe_irreversible_tool_fails(self) -> None:
        temp, bundle = self.copy_sample()
        self.addCleanup(temp.cleanup)
        path = bundle / "tools/web-search.md"
        path.write_text(path.read_text().replace("side_effects: external", "side_effects: irreversible"))
        self.assert_invalid(bundle, "irreversible Tool requires")

    def test_inline_secret_fails(self) -> None:
        temp, bundle = self.copy_sample()
        self.addCleanup(temp.cleanup)
        path = bundle / "tools/web-search.md"
        path.write_text(path.read_text().replace("side_effects: external", "side_effects: external\napi_key: hunter2"))
        self.assert_invalid(bundle, "inline secret-like value")

    def test_incompatible_ager_version_fails(self) -> None:
        temp, bundle = self.copy_sample()
        self.addCleanup(temp.cleanup)
        path = bundle / "agents/worker.md"
        path.write_text(path.read_text().replace('ager_version: "0.3.0"', 'ager_version: "9.0.0"'))
        self.assert_invalid(bundle, "requires ager_version")


class AgerInitTests(unittest.TestCase):
    def test_generator_creates_complete_valid_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ager-init-") as temp:
            destination = Path(temp) / "generated"
            proc, payload = run_json(
                sys.executable, GENERATOR, destination, "--title", "Generated Test Graph",
                "--author", "claude-code/lumenfield-detector",
            )
            self.assertEqual(proc.returncode, 0, payload)
            self.assertTrue(payload["ager_validation"]["valid"])
            self.assertEqual(payload["ager_validation"]["bundle"], str(destination.resolve()))
            self.assertGreaterEqual(payload["file_count"], 36)
            self.assertIn("title: \"Generated Test Graph\"", (destination / "index.md").read_text())
            self.assertIn("author: claude-code/lumenfield-detector", (destination / "index.md").read_text())
            self.assertTrue(any((destination / "write-events").glob("*.md")))
            self.assertFalse(any("{{" in path.read_text() for path in destination.rglob("*.md")))
            for required in (
                "agents/synthesizer.md", "ops/retry-policy.md", "prompts/lead.txt",
                "evaluation/quality-rubric.md", "schemas/final-report.schema.json",
            ):
                self.assertTrue((destination / required).is_file(), required)
            if OKF_GRAPH.is_file():
                okf_proc, okf_payload = run_json(
                    sys.executable, OKF_GRAPH, "validate", destination, "--strict"
                )
                self.assertEqual(okf_proc.returncode, 0, okf_payload)
                self.assertEqual(okf_payload["warn_count"], 0, okf_payload["issues"])

    def test_generator_refuses_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ager-init-existing-") as temp:
            destination = Path(temp) / "existing"
            destination.mkdir()
            sentinel = destination / "keep.txt"
            sentinel.write_text("keep")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(destination)], capture_output=True, text=True
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(sentinel.read_text(), "keep")


class TestRequiredIdentity(unittest.TestCase):
    def test_resolve_author_fail_closed(self) -> None:
        sys.path.insert(0, str(REPO / "scripts"))
        from ager_common import resolve_author

        prev = os.environ.pop("SECOND_BRAIN_IDENTITY", None)
        try:
            with self.assertRaises(SystemExit):
                resolve_author(None)
            self.assertEqual(
                resolve_author("grok-bot/northstar-console"),
                "grok-bot/northstar-console",
            )
        finally:
            if prev is not None:
                os.environ["SECOND_BRAIN_IDENTITY"] = prev

    def test_init_without_identity_fails(self) -> None:
        env = os.environ.copy()
        env.pop("SECOND_BRAIN_IDENTITY", None)
        with tempfile.TemporaryDirectory(prefix="ager-noid-") as temp:
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(Path(temp) / "new")],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("identity", (proc.stdout + proc.stderr).lower())

    def test_flag_beats_env(self) -> None:
        sys.path.insert(0, str(REPO / "scripts"))
        from ager_common import resolve_author

        prev = os.environ.get("SECOND_BRAIN_IDENTITY")
        os.environ["SECOND_BRAIN_IDENTITY"] = "grok-bot/northstar-console"
        try:
            self.assertEqual(resolve_author(None), "grok-bot/northstar-console")
            self.assertEqual(
                resolve_author("claude-code/lumenfield-detector"),
                "claude-code/lumenfield-detector",
            )
        finally:
            if prev is None:
                os.environ.pop("SECOND_BRAIN_IDENTITY", None)
            else:
                os.environ["SECOND_BRAIN_IDENTITY"] = prev


class TestPackTokenBudget(unittest.TestCase):
    def setUp(self) -> None:
        sys.path.insert(0, str(REPO / "scripts"))
        import ager_pack

        self.ager_pack = ager_pack

    def test_sample_tiny_pack_under_default_budget(self) -> None:
        result = self.ager_pack.pack(SAMPLE, "agents/lead-researcher.md", tiny=True)
        md, meta = self.ager_pack.finalize_markdown(result)
        self.assertLessEqual(meta["tokens"], meta["budget"])
        self.assertEqual(meta["budget"], 32_000)
        self.assertIn("Lead researcher", md)
        self.assertNotIn("/agents/index.md", [c["path"] for c in result["concepts"]])

    def test_bodies_off_unless_root(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            agents = tmp / "agents"
            agents.mkdir()
            (tmp / "index.md").write_text(
                '---\nokf_version: "0.2"\ntype: Reference\ntitle: t\n---\n',
                encoding="utf-8",
            )
            (agents / "root.md").write_text(
                "---\ntype: OrchestratorAgent\ntitle: Lumenfield Root\n"
                "links:\n  - target: /agents/neighbor.md\n    rel: spawns\n"
                "---\n# Lumenfield Root\n\nROOT_BODY_MARKER secret-of-root\n",
                encoding="utf-8",
            )
            (agents / "neighbor.md").write_text(
                "---\ntype: DoerAgent\ntitle: Neighbor\n"
                "description: neighbor-frontmatter-only\n---\n"
                "# Neighbor\n\nNEIGHBOR_BODY_MARKER must-not-pack\n",
                encoding="utf-8",
            )
            result = self.ager_pack.pack(tmp, "agents/root.md", hops=1, max_nodes=8)
            md, _meta = self.ager_pack.finalize_markdown(result)
            self.assertIn("ROOT_BODY_MARKER", md)
            self.assertNotIn("NEIGHBOR_BODY_MARKER", md)
            self.assertIn("neighbor-frontmatter-only", md)
        finally:
            shutil.rmtree(tmp)

    def test_inbound_edge_is_visible(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            agents = tmp / "agents"
            agents.mkdir()
            (tmp / "index.md").write_text(
                '---\nokf_version: "0.2"\ntype: Reference\ntitle: t\n---\n',
                encoding="utf-8",
            )
            (agents / "seed.md").write_text(
                "---\ntype: DoerAgent\ntitle: Seed\n---\n# Seed\n",
                encoding="utf-8",
            )
            (agents / "inbound.md").write_text(
                "---\ntype: OrchestratorAgent\ntitle: Inbound\n"
                "links:\n  - target: /agents/seed.md\n    rel: spawns\n"
                "---\n# Inbound\n",
                encoding="utf-8",
            )
            result = self.ager_pack.pack(tmp, "agents/seed.md", hops=1, max_nodes=8)
            paths = [c["path"] for c in result["concepts"]]
            self.assertIn("/agents/inbound.md", paths)
        finally:
            shutil.rmtree(tmp)

    def test_pack_rg_matches_scan(self) -> None:
        fake = REPO / "tests/fixtures/fake_rg.py"
        fake.chmod(0o755)
        prev = os.environ.get("AGER_RG_PATH")
        os.environ["AGER_RG_PATH"] = str(fake)
        try:
            scan = self.ager_pack.pack(
                SAMPLE, "agents/lead-researcher.md", hops=2, max_nodes=40, use_rg=False
            )
            accel = self.ager_pack.pack(
                SAMPLE, "agents/lead-researcher.md", hops=2, max_nodes=40, use_rg=True
            )
            self.assertEqual(scan["node_count"], accel["node_count"])
            self.assertEqual(
                sorted(c["path"] for c in scan["concepts"]),
                sorted(c["path"] for c in accel["concepts"]),
            )
            self.assertEqual(accel["reverse_index"], "rg")
            self.assertEqual(scan["reverse_index"], "scan")
        finally:
            if prev is None:
                os.environ.pop("AGER_RG_PATH", None)
            else:
                os.environ["AGER_RG_PATH"] = prev

    def test_over_budget_fails_closed(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            agents = tmp / "agents"
            agents.mkdir()
            (tmp / "index.md").write_text(
                '---\nokf_version: "0.2"\ntype: Reference\ntitle: t\n---\n',
                encoding="utf-8",
            )
            fat = "# Fat Root\n\n" + ("word " * 400)
            (agents / "fat.md").write_text(
                "---\ntype: OrchestratorAgent\ntitle: Fat Root\n---\n" + fat,
                encoding="utf-8",
            )
            result = self.ager_pack.pack(tmp, "agents/fat.md", hops=0, max_nodes=1)
            with self.assertRaises(self.ager_pack.PackBudgetError) as ctx:
                self.ager_pack.finalize_markdown(result, max_tokens=20)
            self.assertGreater(ctx.exception.tokens, ctx.exception.budget)
            self.assertEqual(ctx.exception.budget, 20)
            out = tmp / "should-not-exist.md"
            rc = self.ager_pack.main(
                [
                    "agents/fat.md",
                    "--repo",
                    str(tmp),
                    "--bundle",
                    str(tmp),
                    "--max-nodes",
                    "1",
                    "--hops",
                    "0",
                    "--max-tokens",
                    "20",
                    "--write",
                    str(out),
                    "--json",
                ]
            )
            self.assertNotEqual(rc, 0)
            self.assertFalse(out.exists())
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()

