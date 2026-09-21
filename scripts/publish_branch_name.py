"""Publish head-bound naming statuses using only trusted default-branch code."""

import json
import os
import subprocess
from pathlib import Path

from check_branch_name import REPOSITORY, validate


def api(path, payload=None):
    """Pass structured data to GitHub without executing untrusted PR content."""
    command = ["gh", "api", f"repos/{REPOSITORY}/{path}"]
    if payload is not None:
        command += ["--method", "POST", "--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def publish(number):
    """Re-read live metadata and refuse success after a concurrent head/title change."""
    pr = api(f"pulls/{number}")
    if pr["state"] != "open":
        return
    sha = pr["head"]["sha"]
    target = f"{os.environ['GITHUB_SERVER_URL']}/{REPOSITORY}/actions/runs/{os.environ['GITHUB_RUN_ID']}"

    def status(state, description):
        api(
            f"statuses/{sha}",
            {
                "state": state,
                "context": "Branch naming",
                "description": description[:140],
                "target_url": target,
            },
        )

    status("pending", "Checking trusted issue-linked branch policy")
    try:
        message = validate({"pull_request": pr}, lambda n: api(f"issues/{n}"))
    except (ValueError, subprocess.CalledProcessError) as error:
        status("failure", "Invalid branch or issue metadata; see run log")
        print(f"PR #{number}: {error}")
        return
    current = api(f"pulls/{number}")
    if current["state"] != "open" or (
        current["head"]["sha"],
        current["head"]["ref"],
        current["title"],
    ) != (sha, pr["head"]["ref"], pr["title"]):
        status("pending", "PR changed during validation; latest event must recheck")
        return
    status("success", message)
    print(f"PR #{number}: {message}")


def main():
    """Check one event PR or all open PRs during manual bootstrap/reconciliation."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if "pull_request" in event:
        publish(event["pull_request"]["number"])
        return
    page = 1
    while True:
        prs = api(f"pulls?state=open&per_page=100&page={page}")
        for pr in prs:
            publish(pr["number"])
        if len(prs) < 100:
            break
        page += 1


if __name__ == "__main__":
    main()
