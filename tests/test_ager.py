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
                sys.executable, GENERATOR, destination, "--title", "Generated Test Graph"
            )
            self.assertEqual(proc.returncode, 0, payload)
            self.assertTrue(payload["ager_validation"]["valid"])
            self.assertEqual(payload["ager_validation"]["bundle"], str(destination.resolve()))
            self.assertEqual(payload["file_count"], 36)
            self.assertIn("title: \"Generated Test Graph\"", (destination / "index.md").read_text())
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


if __name__ == "__main__":
    unittest.main()
