"""Compare local coverage evidence; never execute report contents or publish comments."""

import argparse
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from coverage_summary import MAX_REPORT_BYTES, parse_report


def source_path(value, prefix):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError("Invalid report source path")
    return str(PurePosixPath(prefix) / path)


def executable_lines(kind, report):
    if report.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("Report too large")
    text = report.read_text()
    result = {}
    if kind == "backend":
        root = ET.fromstring(text)
        sources = [
            str(PurePosixPath(item.text or ""))
            for item in root.findall("sources/source")
        ]
        if len(sources) != 1 or not (
            sources[0] == "app" or sources[0].endswith("/backend/app")
        ):
            raise ValueError("Backend source root does not match backend/app")
        for item in root.iter("class"):
            name = source_path(item.attrib["filename"], "backend/app")
            if name in result:
                raise ValueError("Duplicate source")
            result[name] = {}
            for line in item.iter("line"):
                number, hits = int(line.attrib["number"]), int(line.attrib["hits"])
                if number < 1 or hits < 0 or number in result[name]:
                    raise ValueError("Invalid XML line record")
                result[name][number] = hits > 0
    else:
        for record in text.split("end_of_record"):
            if not record.strip():
                continue
            names = re.findall(r"^SF:(.+)$", record, re.MULTILINE)
            if len(names) != 1:
                raise ValueError("Expected one LCOV source")
            name = source_path(names[0], "frontend")
            if name in result:
                raise ValueError("Duplicate source")
            result[name] = {}
            for line in record.splitlines():
                if not line.startswith("DA:"):
                    continue
                match = re.fullmatch(r"DA:(\d+),(\d+)(?:,.*)?", line)
                if not match:
                    raise ValueError("Malformed LCOV line record")
                number, hits = int(match[1]), int(match[2])
                if number in result[name] or number < 1:
                    raise ValueError("Invalid line record")
                result[name][number] = int(hits) > 0
    if not result:
        raise ValueError("Empty coverage sources")
    measured = [hit for source in result.values() for hit in source.values()]
    if parse_report(kind, report)["Lines"] != (sum(measured), len(measured)):
        raise ValueError("Line details do not match report totals")
    return result


def changed_lines(diff):
    """Read zero-context git diff without treating filenames as commands."""
    result = {}
    current = None
    file_header = True
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current = None
            file_header = True
        elif file_header and line.startswith("+++ "):
            current = None
            if line.startswith("+++ b/"):
                current = source_path(line[6:], "")
                result.setdefault(current, set())
            elif line != "+++ /dev/null":
                raise ValueError("Unsupported diff filename encoding")
        elif line.startswith("@@ ") and current is not None:
            file_header = False
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if not match:
                raise ValueError("Invalid diff hunk")
            start, size = int(match[1]), int(match[2] or 1)
            result[current].update(range(start, start + size))
    return result


def compare(kind, head_report, base_report, diff, head, base):
    for revision in (head, base):
        if not re.fullmatch("[0-9a-f]{40}", revision):
            raise ValueError("Expected full commit identity")
    head_totals = parse_report(kind, head_report)
    head_lines = executable_lines(kind, head_report)
    lines = [
        f"## {kind.title()} coverage comparison",
        "",
        f"Tested head: `{head}`. Base: `{base}`.",
        "",
    ]
    try:
        base_totals = parse_report(kind, base_report)
        base_lines = executable_lines(kind, base_report)
        if head_lines.keys() != base_lines.keys():
            raise ValueError("Different measured file sets")
    except (OSError, ValueError, KeyError, ET.ParseError):
        lines += [
            "**Baseline unavailable or incompatible:** no total regression is inferred.",
            "",
        ]
    else:
        lines += ["| Metric | Base | Head | Change |", "| --- | --- | --- | --- |"]
        for metric in head_totals:
            hc, ht = head_totals[metric]
            bc, bt = base_totals[metric]
            if not ht or not bt:
                lines.append(f"| {metric} | N/A | N/A | N/A |")
            else:
                lines.append(
                    f"| {metric} | {bc / bt:.1%} | {hc / ht:.1%} | {(hc / ht - bc / bt) * 100:+.2f} pp |"
                )
        lines.append("")
    measured = []
    outside = 0
    for name, additions in changed_lines(diff).items():
        if name not in head_lines:
            outside += len(additions)
        else:
            measured += [
                head_lines[name][n] for n in additions if n in head_lines[name]
            ]
    if measured:
        lines.append(
            f"Changed measured executable lines: **{sum(measured)}/{len(measured)} ({sum(measured) / len(measured):.1%})**."
        )
    else:
        lines.append("Changed measured executable lines: **N/A (none measured)**.")
    lines += [
        (
            f"Added lines in files outside the measured scope: **{outside}**. "
            "These are not counted as covered; they may include non-executable content."
        ),
        "",
        "Comparison is supporting evidence, not an additional gate. Existing test thresholds remain enforced.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["backend", "frontend"], required=True)
    parser.add_argument("--head-report", type=Path, required=True)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    if not all(re.fullmatch("[0-9a-f]{40}", x) for x in (args.head, args.base)):
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
        text=True,
        capture_output=True,
    ).stdout
    print(
        compare(
            args.kind, args.head_report, args.base_report, diff, args.head, args.base
        )
    )


if __name__ == "__main__":
    main()
