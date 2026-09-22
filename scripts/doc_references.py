"""List documentation references for human status review; never certify accuracy."""

import argparse
import re
import subprocess
from pathlib import Path


def pattern(issue: int, terms: list[str]) -> re.Pattern:
    """Match complete issue identifiers and literal, case-insensitive feature terms."""
    parts = [rf"\bVIN-{issue}\b", rf"(?<!\w)#{issue}\b", rf"/issues/{issue}(?!\d)"]
    parts.extend(re.escape(term) for term in terms)
    return re.compile("|".join(parts), re.IGNORECASE)


def main():
    """Read tracked documentation from the current checkout without changing it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", type=int, help="GitHub issue number")
    parser.add_argument(
        "terms", nargs="+", help="Literal feature terms, e.g. 'order placement'"
    )
    args = parser.parse_args()
    if args.issue < 1 or any(not term.strip() for term in args.terms):
        parser.error("Use a positive issue number and non-empty feature terms")
    root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
        .decode()
        .split("\0")
    )
    matcher = pattern(args.issue, args.terms)
    hits = 0
    for name in paths:
        if not name.endswith((".md", ".mdx", ".rst", ".txt")):
            continue
        path = root / name
        if not path.is_file() or path.is_symlink():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if matcher.search(line):
                print(f"{name}:{number}:{line}")
                hits += 1
    print(
        f"\n{hits} references. Inspect surrounding context; this is discovery, not validation."
    )
    if not hits:
        print(
            "No matches: broaden the feature terms and inspect entry-point docs manually."
        )


if __name__ == "__main__":
    main()
