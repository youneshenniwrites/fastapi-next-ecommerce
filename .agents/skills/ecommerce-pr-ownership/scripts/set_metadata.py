"""Assign an ecommerce PR to its owner and add reviewed labels through GitHub REST."""

import argparse
import json
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


def api(path, payload=None):
    args = ["gh", "api", path]
    if payload is not None:
        args += ["--method", "POST", "--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps(payload) if payload is not None else None,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pr", type=int)
    parser.add_argument("--labels", nargs="+", required=True, choices=LABELS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.pr < 1:
        parser.error("PR number must be positive")
    pull = api(f"repos/{REPO}/pulls/{args.pr}")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "pr": args.pr,
                    "author": pull["user"]["login"],
                    "add_assignee": OWNER,
                    "add_labels": args.labels,
                }
            )
        )
        return
    # REST avoids the deprecated Projects Classic fields queried by old gh pr edit.
    api(f"repos/{REPO}/issues/{args.pr}/assignees", {"assignees": [OWNER]})
    api(f"repos/{REPO}/issues/{args.pr}/labels", {"labels": args.labels})
    issue = api(f"repos/{REPO}/issues/{args.pr}")
    assigned = [user["login"] for user in issue["assignees"]]
    labels = [label["name"] for label in issue["labels"]]
    if OWNER not in assigned or not set(args.labels).issubset(labels):
        raise SystemExit("GitHub did not retain the requested ownership/labels")
    print(
        json.dumps(
            {
                "pr": args.pr,
                "author": pull["user"]["login"],
                "assignees": assigned,
                "labels": labels,
            }
        )
    )


if __name__ == "__main__":
    main()
