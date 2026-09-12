"""Render existing coverage reports for read-only Actions job summaries."""

import argparse
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_REPORT_BYTES = 5_000_000
SCOPES = {
    "backend": (
        (
            "backend/app; excludes app/tests. Migration subprocesses and browser tests "
            "are separate evidence, not included in this measurement."
        ),
        "85% combined line/branch coverage (coverage.py); no separate line/branch gate.",
    ),
    "frontend": (
        (
            "Only src/lib/catalog.ts and src/lib/session.ts. This is NOT whole-frontend "
            "coverage; components, routes and all other files are outside this scope."
        ),
        "95% statements, 90% branches, 100% functions and 95% lines (Vitest).",
    ),
}


def counts(covered, total):
    covered, total = int(covered), int(total)
    if not 0 <= covered <= total:
        raise ValueError("Invalid coverage counts")
    return covered, total


def parse_report(kind, report):
    if report.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("Coverage report exceeds size limit")
    text = report.read_text(encoding="utf-8")
    if kind == "backend":
        root = ET.fromstring(text)
        if root.tag != "coverage":
            raise ValueError("Expected coverage XML")
        return {
            "Lines": counts(root.attrib["lines-covered"], root.attrib["lines-valid"]),
            "Branches": counts(
                root.attrib["branches-covered"], root.attrib["branches-valid"]
            ),
        }
    totals = dict.fromkeys(("LH", "LF", "BRH", "BRF"), 0)
    files = []
    for record in text.split("end_of_record"):
        fields = dict(line.split(":", 1) for line in record.splitlines() if ":" in line)
        if not fields:
            continue
        files.append(fields["SF"])
        # Require explicit totals, including zero, rather than inventing coverage.
        for field in totals:
            totals[field] += int(fields[field])
        counts(fields["LH"], fields["LF"])
        counts(fields["BRH"], fields["BRF"])
    if sorted(files) != ["src/lib/catalog.ts", "src/lib/session.ts"]:
        raise ValueError("Frontend report does not match the documented measured scope")
    return {
        "Lines": counts(totals["LH"], totals["LF"]),
        "Branches": counts(totals["BRH"], totals["BRF"]),
    }


def render(kind, report, outcome, artifact_url="", revision="local"):
    if not re.fullmatch(r"local|[0-9a-f]{7,40}", revision):
        raise ValueError("Invalid tested revision")
    if artifact_url and not re.fullmatch(
        r"https://github\.com/[\w.-]+/[\w.-]+/actions/runs/\d+/artifacts/\d+",
        artifact_url,
    ):
        raise ValueError("Invalid artifact URL")
    scope, gate = SCOPES[kind]
    lines = [
        f"## {kind.title()} coverage",
        "",
        f"Tested revision: `{revision}`.",
        "",
        f"**Measured scope:** {scope}",
        "",
        f"**Existing gates:** {gate}",
        f"**Test/coverage step outcome:** {outcome}. This reporter does not replace the test gates.",
        "",
    ]
    valid = True
    try:
        metrics = parse_report(kind, report)
        lines.extend(
            ["| Metric | Covered / measured | Coverage |", "| --- | --- | --- |"]
        )
        for name, (covered, total) in metrics.items():
            percentage = (
                f"{covered / total:.1%}"
                if total
                else "N/A (no measured branches/lines)"
            )
            lines.append(f"| {name} | {covered} / {total} | {percentage} |")
    except (OSError, ValueError, KeyError, ET.ParseError):
        valid = False
        lines.append(
            "**Coverage unavailable:** report missing, malformed or outside the expected scope. No percentage or pass is inferred."
        )
    lines.extend(
        [
            "",
            f"[Download HTML and raw reports]({artifact_url}) (14-day retention)."
            if artifact_url
            else "Artifact unavailable; inspect the report-upload step.",
            "",
            "Coverage supports review; it does not establish test quality or whole-product correctness.",
        ]
    )
    return "\n".join(lines) + "\n", valid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=SCOPES, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--outcome",
        choices=["success", "failure", "cancelled", "skipped"],
        required=True,
    )
    parser.add_argument("--artifact-url", default="")
    parser.add_argument("--revision", default=os.environ.get("GITHUB_SHA", "local"))
    args = parser.parse_args()
    summary, valid = render(
        args.kind, args.report, args.outcome, args.artifact_url, args.revision
    )
    print(summary, end="")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
