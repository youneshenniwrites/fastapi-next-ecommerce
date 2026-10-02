"""Read-only eligibility for a manually requested, reviewed frontend preview."""

import os
import re

try:
    from scripts import coderabbit_review_gate as rabbit
    from scripts import codex_review_gate as codex
    from scripts.docs_review_policy import eligible as routine_docs
except ModuleNotFoundError:
    import coderabbit_review_gate as rabbit
    import codex_review_gate as codex
    from docs_review_policy import eligible as routine_docs

WORKFLOWS = ("ci.yml", "frontend.yml", "dependency-audit.yml", "review-gate-tests.yml")


def source_allowed(pr, repo, sha):
    """Never grant deployment access to drafts, forks or an unspecified revision."""
    return (
        bool(re.fullmatch(r"[0-9a-f]{40}", sha))
        and pr.get("state") == "open"
        and not pr.get("draft", True)
        and pr.get("base", {}).get("ref") == "main"
        and (pr.get("base", {}).get("repo") or {}).get("full_name") == repo
        and (pr.get("head", {}).get("repo") or {}).get("full_name") == repo
        and pr.get("head", {}).get("sha") == sha
    )


def passed(runs, sha, number):
    """Require the latest matching PR run; a later failed run invalidates success."""
    matches = [
        r
        for r in runs
        if r.get("head_sha") == sha
        and r.get("event") == "pull_request"
        and any(p.get("number") == number for p in r.get("pull_requests", []))
    ]
    return (
        bool(matches)
        and max(matches, key=lambda r: r["id"]).get("conclusion") == "success"
    )


def verify(repo, number, sha):
    """Use trusted gate implementations and complete evidence, never PR status prose."""
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Preview orchestration must run on main")
    path = f"repos/{repo}/pulls/{number}"
    pr = codex.api(path)
    if not source_allowed(pr, repo, sha):
        raise ValueError(
            "Preview source must be an open ready same-repository exact-head PR"
        )
    files = codex.pages(path + "/files")
    reviewer = rabbit if routine_docs(pr, files, repo) else codex
    reviewed, state, _ = reviewer.inspect(repo, number)
    if reviewed != sha or state != "success":
        raise ValueError(
            "Current-head external review and resolved findings are required"
        )
    for workflow in WORKFLOWS:
        runs = codex.api(
            f"repos/{repo}/actions/workflows/{workflow}/runs?head_sha={sha}&event=pull_request&per_page=100"
        )["workflow_runs"]
        if not passed(runs, sha, number):
            raise ValueError(f"Current-head PR CI is not successful: {workflow}")
    if not source_allowed(codex.api(path), repo, sha):
        raise ValueError("PR changed during preview verification")
    return sha


if __name__ == "__main__":
    revision = verify(
        os.environ["GITHUB_REPOSITORY"],
        int(os.environ["PR_NUMBER"]),
        os.environ["PREVIEW_SHA"],
    )
    print(f"Reviewed preview revision eligible: {revision}")
