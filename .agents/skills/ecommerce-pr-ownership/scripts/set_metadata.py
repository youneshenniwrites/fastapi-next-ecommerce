"""Assign an ecommerce PR and copy the linked issue's milestone and priority."""

import argparse
import json
import re
import subprocess

REPO = "youneshenniwrites/fastapi-next-ecommerce"
OWNER = "youneshenniwrites"
LABELS = (
    "bug",
    "enhancement",
    "documentation",
    "tooling",
    "dependencies",
    "github_actions",
    "docker",
)


def api(path, payload=None, method=None):
    args = ["gh", "api", path]
    if method:
        args += ["--method", method]
    elif payload is not None:
        args += ["--method", "POST"]
    if payload is not None:
        args += ["--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(payload) if payload is not None else None,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout) if result.stdout else {}


def linked_issue_number(title, body):
    """Use the title VIN key, then a closing keyword, then Refs."""
    titled = re.search(r"\[VIN-([1-9][0-9]*)\]", title or "")
    if titled:
        return int(titled.group(1))
    text = body or ""
    closing = re.search(
        r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", text
    )
    if closing:
        return int(closing.group(1))
    refs = re.search(r"(?i)\brefs\s+#(\d+)", text)
    if refs:
        return int(refs.group(1))
    return None


def issue_sidebar(issue):
    """Return the milestone and priority labels to copy from a linked issue."""
    if not issue:
        return None, []
    raw = issue.get("milestone") or None
    milestone = None
    if raw and raw.get("number"):
        milestone = {"number": raw["number"], "title": raw.get("title")}
    priority = [
        label["name"]
        for label in issue.get("labels", [])
        if str(label.get("name", "")).startswith("priority:")
    ]
    return milestone, priority


def assign_owner(pr):
    """Add the owner, retrying with a patch when the assignee route is forbidden."""
    try:
        api(f"repos/{REPO}/issues/{pr}/assignees", {"assignees": [OWNER]})
    except subprocess.CalledProcessError:
        api(
            f"repos/{REPO}/issues/{pr}",
            {"assignees": [OWNER]},
            method="PATCH",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", type=int)
    parser.add_argument("--labels", nargs="+", required=True, choices=LABELS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.pr < 1:
        parser.error("PR number must be positive")
    pull = api(f"repos/{REPO}/pulls/{args.pr}")
    source = linked_issue_number(pull.get("title"), pull.get("body"))
    linked = api(f"repos/{REPO}/issues/{source}") if source else None
    milestone, priority = issue_sidebar(linked)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "pr": args.pr,
                    "author": pull["user"]["login"],
                    "add_assignee": OWNER,
                    "add_labels": [*args.labels, *priority],
                    "issue": source,
                    "milestone": milestone,
                }
            )
        )
        return
    # REST avoids the deprecated Projects Classic fields queried by old gh pr edit.
    # The PR stays off the project board; the linked issue card is the board item.
    # Labels and the milestone are applied even if assignment is forbidden, so a
    # partial sidebar can be repaired by running the helper again.
    api(f"repos/{REPO}/issues/{args.pr}/labels", {"labels": [*args.labels, *priority]})
    if milestone:
        api(
            f"repos/{REPO}/issues/{args.pr}",
            {"milestone": milestone["number"]},
            method="PATCH",
        )
    try:
        assign_owner(args.pr)
    except subprocess.CalledProcessError:
        pass
    issue = api(f"repos/{REPO}/issues/{args.pr}")
    assigned = [user["login"] for user in issue["assignees"]]
    labels = [label["name"] for label in issue["labels"]]
    applied = issue.get("milestone")
    if OWNER not in assigned or not set(args.labels).issubset(labels):
        raise SystemExit("GitHub did not retain the requested ownership/labels")
    if milestone and (not applied or applied["number"] != milestone["number"]):
        raise SystemExit("GitHub did not retain the linked issue milestone")
    if not set(priority).issubset(labels):
        raise SystemExit("GitHub did not retain the linked issue priority")
    print(
        json.dumps(
            {
                "pr": args.pr,
                "author": pull["user"]["login"],
                "assignees": assigned,
                "labels": labels,
                "issue": source,
                "milestone": None
                if not applied
                else {"number": applied["number"], "title": applied["title"]},
            }
        )
    )


if __name__ == "__main__":
    main()
