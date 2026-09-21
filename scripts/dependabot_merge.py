"""Bounded CI wait and atomic SHA merge; never arm persistent auto-merge."""
import json
import os
import subprocess
import time


def merge_validated(repo, number, head, api, checks, sleep=time.sleep):
    """A changed head stops work; GitHub enforces protection at the merge call."""
    path = f"repos/{repo}/pulls/{number}"
    for _ in range(40):
        pr = api(path)
        if pr["state"] != "open" or pr["draft"] or pr["head"]["sha"] != head:
            return "Head changed or PR no longer ready; no merge"
        states = checks()
        if any(state in {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"} for state in states):
            return "Required CI failed; no merge"
        if states and all(state in {"SUCCESS", "SKIPPED", "NEUTRAL"} for state in states):
            api(f"{path}/reviews", event="APPROVE", commit_id=head,
                body="Automated dependency-policy approval (VIN-172), not a Codex review. Required CI and protection still apply.")
            # SHA is checked atomically by GitHub; a push after the above read
            # cannot inherit permission. No --auto request survives this run.
            result = api(f"{path}/merge", method="PUT", sha=head, merge_method="squash")
            if not result.get("merged"):
                raise RuntimeError("GitHub did not merge the validated commit")
            return "Merged validated head"
        sleep(30)
    return "Required CI not ready within 20 minutes; rerun after resolving blocker"


if __name__ == "__main__":
    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["PR_NUMBER"])

    def api(path, method=None, **fields):
        command = ["gh", "api", path]
        if method:
            command += ["--method", method]
        for key, value in fields.items():
            command += ["-f", f"{key}={value}"]
        return json.loads(subprocess.check_output(command, text=True))

    def checks():
        result = subprocess.run(["gh", "pr", "checks", str(number), "--repo", repo,
                                 "--required", "--json", "state"], capture_output=True, text=True)
        # gh returns nonzero for pending/failed checks; valid JSON remains evidence.
        try:
            return [item["state"] for item in json.loads(result.stdout)]
        except (ValueError, TypeError):
            return []  # API failure/missing checks cannot authorize merge.

    print(merge_validated(repo, number, os.environ["EXPECTED_HEAD"], api, checks))
