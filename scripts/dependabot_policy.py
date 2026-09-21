"""Fail-closed eligibility for the owner's dependency-only review exception."""

ALLOWED_FILES = {
    "npm": {"frontend/package.json", "frontend/package-lock.json"},
    "npm_and_yarn": {"frontend/package.json", "frontend/package-lock.json"},
    "uv": {"backend/pyproject.toml", "backend/uv.lock", "backend/requirements.txt"},
}


def eligible(pr, files, commits, ecosystem, update_type, repository):
    """Metadata verification remains required separately by fetch-metadata."""
    return bool(
        pr["state"] == "open"
        and not pr["draft"]
        and pr["user"]["login"] == "dependabot[bot]"
        and pr["base"]["ref"] == "main"
        and pr["head"]["repo"]["full_name"] == repository
        and pr["head"]["ref"].startswith("dependabot/")
        and update_type in {"version-update:semver-patch", "version-update:semver-minor"}
        and files
        and all(f["status"] == "modified" and f["filename"] in ALLOWED_FILES.get(ecosystem, set()) for f in files)
        and commits
        and all((c.get("author") or {}).get("login") == "dependabot[bot]" and c["commit"]["verification"]["verified"] for c in commits)
    )


if __name__ == "__main__":
    import json
    import os
    import subprocess

    def api(path):
        return json.loads(subprocess.check_output(["gh", "api", path], text=True))

    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["PR_NUMBER"])
    prefix = f"repos/{repo}/pulls/{number}"
    pr = api(prefix)
    # Refuse truncation rather than approving incomplete evidence.
    files = api(f"{prefix}/files?per_page=100")
    commits = api(f"{prefix}/commits?per_page=100")
    allowed = (
        pr["head"]["sha"] == os.environ["EXPECTED_HEAD"]
        and pr["changed_files"] == len(files) < 100
        and pr["commits"] == len(commits) < 100
        and eligible(pr, files, commits, os.environ["ECOSYSTEM"], os.environ["UPDATE_TYPE"], repo)
    )
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"eligible={str(allowed).lower()}\n")
    print("Eligible for policy approval" if allowed else "Normal review required; no automated approval")
