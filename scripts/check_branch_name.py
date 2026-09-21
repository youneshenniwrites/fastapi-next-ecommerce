"""Validate issue-linked PR branches; no PR text is executed as shell code."""

import json
import os
import re
import subprocess
from pathlib import Path

PATTERN = re.compile(
    r"(feat|fix|docs|test|ci|build|chore|refactor|perf|style|revert)/vin-([1-9][0-9]*)-[a-z0-9]+(?:-[a-z0-9]+)*"
)
REPOSITORY = "youneshenniwrites/fastapi-next-ecommerce"


def validate(event, lookup):
    """Return a readable result or fail without trusting a branch's bot prefix."""
    pr = event["pull_request"]
    branch = pr["head"]["ref"]
    author = pr["user"]
    if (
        author.get("id") == 49699333
        and author.get("login") == "dependabot[bot]"
        and author.get("type") == "Bot"
    ):
        return "Dependabot keeps its upstream branch name."
    if (
        pr["number"] == 177
        and branch == "feat/order-drafts"
        and pr["head"]["repo"]["full_name"] == REPOSITORY
    ):
        return "Existing PR #177 retains its reviewed branch name."
    match = PATTERN.fullmatch(branch)
    if not match:
        raise ValueError(
            "Use type/vin-N-short-description, e.g. feat/vin-118-order-drafts (N is the issue number)."
        )
    number = int(match[2])
    title = re.match(r"\[VIN-([1-9][0-9]*)\] \[[a-z]+\] ", pr["title"])
    if not title or int(title[1]) != number:
        raise ValueError(
            f"Branch VIN-{number} must match the PR title's [VIN-{number}] issue key."
        )
    issue = lookup(number)
    if "pull_request" in issue or issue.get("number") != number:
        raise ValueError(f"VIN-{number} must identify a GitHub issue, not a PR.")
    return f"Branch links to VIN-{number}; naming valid."


def main():
    """Read the GitHub event and verify the issue with the read-only job token."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())

    def lookup(number):
        result = subprocess.run(
            ["gh", "api", f"repos/{REPOSITORY}/issues/{number}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    try:
        print(validate(event, lookup))
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Branch naming check failed: {error}") from None


if __name__ == "__main__":
    main()
