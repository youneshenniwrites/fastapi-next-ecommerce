"""Publish head-bound naming statuses using only trusted default-branch code."""

import json
import os
import subprocess

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


def open_prs():
    """Read every page so another PR cannot hide a failing shared-head policy."""
    result = []
    page = 1
    while True:
        prs = api(f"pulls?state=open&per_page=100&page={page}")
        result.extend(prs)
        if len(prs) < 100:
            return result
        page += 1


def snapshot(prs, sha):
    """Capture all policy inputs and membership of a commit's open PR group."""
    return sorted(
        (
            pr["number"],
            pr["head"]["ref"],
            pr["title"],
            json.dumps(pr["user"], sort_keys=True),
            json.dumps(pr["head"].get("repo"), sort_keys=True),
        )
        for pr in prs
        if pr["head"]["sha"] == sha
    )


def publish(sha, prs):
    """Publish success only when every open PR sharing the commit passes."""
    group = [pr for pr in prs if pr["head"]["sha"] == sha]
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

    status("pending", "Checking every open PR sharing this commit")
    try:
        for pr in group:
            message = validate({"pull_request": pr}, lambda n: api(f"issues/{n}"))
            print(f"PR #{pr['number']}: {message}")
        current = open_prs()
    except (ValueError, subprocess.CalledProcessError) as error:
        status("failure", "Branch or metadata check failed; see run log")
        print(f"Commit {sha}: {error}")
        return
    if snapshot(current, sha) != snapshot(prs, sha):
        status("pending", "PR group changed during validation; rerun required")
        return
    status("success", "All open PRs sharing this commit pass branch naming")


def main():
    """Reconcile every open commit group, even for a single PR event."""
    prs = open_prs()
    for sha in sorted({pr["head"]["sha"] for pr in prs}):
        publish(sha, prs)


if __name__ == "__main__":
    main()
