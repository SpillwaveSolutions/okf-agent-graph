#!/usr/bin/env python3
"""End-to-end reverse engineer: scan agent code → draft AGER knowledge bundle.

Primary entrypoint for AGKC (Agent Graph Knowledge Capture), the reverse of
ager-init/ager-author. Pattern sibling of sac_orchestrate / dekc walk+capture.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ager_capture import capture_from_scan  # noqa: E402
from ager_scan import result_to_dict, scan_root  # noqa: E402


def reverse_engineer(
    root: Path,
    *,
    out: Path,
    title: str,
    scan_json: Path | None = None,
) -> dict:
    root = root.resolve()
    scan = result_to_dict(scan_root(root))
    if scan_json:
        scan_json.parent.mkdir(parents=True, exist_ok=True)
        scan_json.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")

    capture = capture_from_scan(
        scan,
        out_dir=out,
        title=title,
        source_root=str(root),
    )
    return {
        "root": str(root),
        "out": str(out.resolve()),
        "frameworks": scan.get("frameworks", []),
        "summary": scan.get("summary", {}),
        "scan_json": str(scan_json) if scan_json else None,
        "capture": capture,
        "next_steps": [
            "Review draft concepts under the output directory",
            "Promote high-confidence drafts into a real AGER bundle via ager-author",
            "python3 scripts/ager-validate.py <bundle> --strict",
            "okf validate <bundle> --strict  # requires okf-graph-eng",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Source repository root")
    parser.add_argument(
        "--out",
        default="discovered-ager",
        help="Directory for draft AGER knowledge bundle",
    )
    parser.add_argument("--title", default="Reverse-engineered agent graph")
    parser.add_argument(
        "--scan-json",
        type=Path,
        default=None,
        help="Optional path to write intermediate scan JSON",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        return 2

    report = reverse_engineer(
        root,
        out=Path(args.out),
        title=args.title,
        scan_json=args.scan_json,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Reverse-engineered: {report['root']}")
        print(f"Draft AGER bundle:  {report['out']}")
        print(f"Frameworks:         {', '.join(report['frameworks']) or '(none)'}")
        for key, value in sorted(report["summary"].items()):
            print(f"  {key}: {value}")
        print("Next:")
        for step in report["next_steps"]:
            print(f"  - {step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
