"""Enforce bounded regression and changed-line coverage using local report data."""

import argparse
import re
import subprocess
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

from coverage_compare import changed_lines, executable_lines
from coverage_summary import parse_report

# Ratios, not rounded display percentages: 0.5 percentage points and 90%.
MAX_DROP = Fraction(1, 200)
MIN_CHANGED = Fraction(9, 10)


def evaluate(kind, head_report, base_report, diff):
    head = parse_report(kind, head_report)
    head_lines = executable_lines(kind, head_report)
    passed = True
    lines = ["## Coverage regression gates"]
    try:
        base = parse_report(kind, base_report)
        if executable_lines(kind, base_report).keys() != head_lines.keys():
            raise ValueError("Incompatible scope")
    except (OSError, ValueError, KeyError, ET.ParseError):
        lines.append(
            "Total regression: **N/A (baseline unavailable or incompatible)**. Changed-line gate still applies."
        )
    else:
        for metric, (covered, total) in head.items():
            base_covered, base_total = base[metric]
            if not total or not base_total:
                lines.append(f"{metric} regression: **N/A (no measured denominator)**.")
                continue
            drop = Fraction(base_covered, base_total) - Fraction(covered, total)
            valid = drop <= MAX_DROP
            passed &= valid
            lines.append(
                f"{metric} regression: **{'PASS' if valid else 'FAIL'}**; drop {float(drop * 100):.3f} percentage points (maximum 0.5)."
            )
    measured = [
        head_lines[name][number]
        for name, additions in changed_lines(diff).items()
        if name in head_lines
        for number in additions
        if number in head_lines[name]
    ]
    if measured:
        valid = Fraction(sum(measured), len(measured)) >= MIN_CHANGED
        passed &= valid
        lines.append(
            f"Changed measured lines: **{'PASS' if valid else 'FAIL'}**; {sum(measured)}/{len(measured)} covered (minimum 90%)."
        )
    else:
        lines.append("Changed measured lines: **N/A (none measured)**.")
    lines.append(
        "Existing absolute coverage thresholds remain required. Lines outside the measured scope are not counted as covered."
    )
    return "\n\n".join(lines) + "\n", passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["backend", "frontend"], required=True)
    parser.add_argument("--head-report", type=Path, required=True)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    if not all(re.fullmatch("[0-9a-f]{40}", value) for value in (args.head, args.base)):
        parser.error("Full commit identities required")
    diff = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
            "--unified=0",
            args.base,
            args.head,
            "--",
            "backend/app",
            "frontend/src",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    try:
        summary, passed = evaluate(args.kind, args.head_report, args.base_report, diff)
    except (OSError, ValueError, KeyError, ET.ParseError):
        print(
            "## Coverage regression gates\n\n**FAIL: head coverage evidence unavailable or invalid.**"
        )
        return 1
    print(summary, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
