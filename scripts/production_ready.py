"""Select a verified main revision; never authorize pull-request source."""

import json
import os
import re
import subprocess

WORKFLOWS = ("ci.yml", "frontend.yml", "dependency-audit.yml", "review-gate-tests.yml")


def passed(runs, sha):
    candidates = [
        r
        for r in runs
        if r["head_sha"] == sha and r["head_branch"] == "main" and r["event"] == "push"
    ]
    return (
        bool(candidates)
        and max(candidates, key=lambda r: r["id"])["conclusion"] == "success"
    )


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["CANDIDATE_SHA"]
    assert re.fullmatch(r"[0-9a-f]{40}", sha), "Invalid revision"
    ready = api(f"repos/{repo}/commits/main")["sha"] == sha
    for name in WORKFLOWS:
        runs = api(
            f"repos/{repo}/actions/workflows/{name}/runs?head_sha={sha}&event=push&per_page=100"
        )["workflow_runs"]
        ready = ready and passed(runs, sha)
    # Avoid deploying a revision again when several CI-completed events arrive.
    for deployment in api(
        f"repos/{repo}/deployments?sha={sha}&environment=production&per_page=100"
    ):
        statuses = api(
            f"repos/{repo}/deployments/{deployment['id']}/statuses?per_page=1"
        )
        if statuses and statuses[0]["state"] == "success":
            ready = False
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"ready={str(ready).lower()}\nsha={sha}\n")
    print(
        f"Revision {sha}: {'ready for production' if ready else 'not eligible or already deployed'}"
    )


if __name__ == "__main__":
    main()
