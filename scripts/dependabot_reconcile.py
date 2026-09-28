"""Bounded, serial continuation using live evidence and trusted main code only."""

import json
import os
import subprocess

import codex_review_gate as gate
from dependabot_export import ExportNotSafe, repair_export
from dependabot_merge import MergeNotReady

APPROVAL = "Automated dependency continuation approval after exact-head Codex review (VIN-172)."


def trusted_pr(pr, repo):
    return (
        pr.get("state") == "open"
        and not pr.get("draft")
        and pr.get("user", {}).get("login") == "dependabot[bot]"
        and pr.get("base", {}).get("ref") == "main"
        and (pr.get("head", {}).get("repo") or {}).get("full_name") == repo
        and pr.get("head", {}).get("ref", "").startswith("dependabot/")
    )


def own_approvals(reviews):
    return [
        r
        for r in reviews
        if r.get("user", {}).get("login") == "github-actions[bot]"
        and r.get("state") == "APPROVED"
        and r.get("body") == APPROVAL
    ]


def green(states):
    return bool(states) and all(s in {"SUCCESS", "SKIPPED", "NEUTRAL"} for s in states)


def dismiss_approvals(path, reviews, api):
    for review in {r["id"]: r for r in own_approvals(reviews)}.values():
        api(
            f"{path}/reviews/{review['id']}/dismissals",
            method="PUT",
            message="Dependency continuation evidence is no longer verified; approval revoked (VIN-172).",
        )


def reconcile_approvals(repo, candidates, api, pages, checks, inspect):
    """Revoke stale approvals across the bounded queue before any pending stop."""
    retained = {}
    failed = False
    for candidate in candidates:
        number = candidate["number"]
        path = f"repos/{repo}/pulls/{number}"
        reviews = own_approvals(pages(f"{path}/reviews"))
        retained[number] = []
        if not reviews:
            continue
        try:
            pr = api(path)
            sha, state, _ = inspect(repo, number)
            states = checks(number)
            current = api(path)
            valid = (
                trusted_pr(pr, repo)
                and trusted_pr(current, repo)
                and pr["head"]["sha"] == sha == current["head"]["sha"]
                and state == "success"
                and green(states)
                and current.get("mergeable_state") == "clean"
            )
            stale = [r for r in reviews if not valid or r.get("commit_id") != sha]
        except Exception:  # noqa: BLE001 - unknown evidence cannot retain approval
            stale = reviews
            failed = True
        dismiss_approvals(path, stale, api)
        retained[number] = [r for r in reviews if r not in stale]
    if failed:
        raise RuntimeError("Approval evidence unavailable; own approvals revoked")
    return retained


def reconcile(repo, pulls, api, pages, checks, inspect, request_api=None, repair=None):
    """Inspect at most 30 PRs; perform at most one branch update or merge per run.

    The optional member token requests reviews, updates branches and merges.
    Approval uses the workflow token. The member token merges only a clean,
    reviewed head so normal main CI is triggered.
    """
    outcomes = []
    candidates = sorted(
        (p for p in pulls if p.get("user", {}).get("login") == "dependabot[bot]"),
        key=lambda p: p["number"],
    )[:30]
    approvals = reconcile_approvals(repo, candidates, api, pages, checks, inspect)
    for candidate in candidates:
        number = candidate["number"]
        path = f"repos/{repo}/pulls/{number}"
        merged = False
        known_approvals = approvals[number]
        approval_attempted = bool(known_approvals)
        try:
            pr = api(path)
            if not trusted_pr(pr, repo):
                continue
            sha = pr["head"]["sha"]
            if repair is not None:
                try:
                    repaired = repair(repo, number, sha, api, request_api)
                except ExportNotSafe as error:
                    outcomes.append((number, f"Export repair blocked: {error}"))
                    continue
                if repaired:
                    outcomes.append(
                        (number, "Repaired Python export; wait for new-head CI")
                    )
                    break
            states = checks(number)
            if any(
                s in {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}
                for s in states
            ):
                outcomes.append((number, "Required CI failed; repair required"))
                continue
            if pr.get("mergeable_state") == "behind":
                if request_api is None:
                    outcomes.append(
                        (
                            number,
                            "Branch behind; DEPENDABOT_REVIEW_TOKEN required to update and trigger CI",
                        )
                    )
                    continue
                # expected_head_sha makes a concurrent PR push fail atomically.
                request_api(
                    f"{path}/update-branch", method="PUT", expected_head_sha=sha
                )
                outcomes.append(
                    (number, "Branch update requested; wait for new-head CI")
                )
                break
            if pr.get("mergeable_state") == "dirty":
                outcomes.append((number, "Merge conflicts require repair"))
                continue
            if pr.get("mergeable_state") in {None, "unknown"}:
                outcomes.append(
                    (number, "Mergeability pending; keep this queue candidate")
                )
                break
            if not states or any(
                s not in {"SUCCESS", "SKIPPED", "NEUTRAL"} for s in states
            ):
                outcomes.append(
                    (
                        number,
                        "Required CI missing or pending; keep this queue candidate",
                    )
                )
                break
            comments = pages(f"repos/{repo}/issues/{number}/comments")
            marker = f"<!-- codex-review-head:{sha} -->"
            if not any(
                gate.review_request(c) and marker in c.get("body", "") for c in comments
            ):
                current = api(path)
                if (
                    trusted_pr(current, repo)
                    and current["head"]["sha"] == sha
                    and request_api
                ):
                    request_api(
                        f"repos/{repo}/issues/{number}/comments",
                        body=f"@codex review\n{marker}",
                    )
                    outcomes.append((number, "Requested Codex review for current head"))
                else:
                    outcomes.append(
                        (number, "Review request token unavailable or head changed")
                    )
                break
            reviewed, state, reason = inspect(repo, number)
            if reviewed != sha or state != "success":
                outcomes.append((number, reason))
                if reason in {
                    "Resolve review conversations and obtain a clean re-review",
                    "Obtain a new clean review after the latest review findings",
                }:
                    continue
                break
            states = checks(number)
            if not states or any(
                s not in {"SUCCESS", "SKIPPED", "NEUTRAL"} for s in states
            ):
                outcomes.append((number, "Required CI missing, pending or failed"))
                continue
            current = api(path)
            if (
                not trusted_pr(current, repo)
                or current["head"]["sha"] != sha
                or current.get("mergeable_state")
                in {None, "unknown", "dirty", "behind"}
            ):
                outcomes.append((number, "PR trust, head or mergeability changed"))
                continue
            if request_api is None:
                outcomes.append((number, "Merge token unavailable"))
                break
            reviews = pages(f"{path}/reviews")
            if not any(
                r.get("user", {}).get("login") == "github-actions[bot]"
                and r.get("commit_id") == sha
                and r.get("state") == "APPROVED"
                and r.get("body") == APPROVAL
                for r in reviews
            ):
                approval_attempted = True
                approval = api(
                    f"{path}/reviews", event="APPROVE", commit_id=sha, body=APPROVAL
                )
                if approval.get("id"):
                    known_approvals.append(approval)
            # Review evidence can change without a push (new findings/dismissal).
            reviewed, state, reason = inspect(repo, number)
            current = api(path)
            if (
                reviewed != sha
                or state != "success"
                or not trusted_pr(current, repo)
                or current["head"]["sha"] != sha
                or current.get("mergeable_state") != "clean"
            ):
                outcomes.append((number, "Evidence or PR changed before merge"))
                continue
            # Optional checks are not atomically enforced by branch protection.
            # Re-read them after the final evidence inspection, immediately before merge.
            if not green(checks(number)):
                outcomes.append((number, "CI changed before merge; approval revoked"))
                continue
            try:
                result = request_api(
                    f"{path}/merge",
                    method="PUT",
                    sha=sha,
                    merge_method="squash",
                    commit_title=f"chore(deps): update dependencies (VIN-172) (#{number})",
                )
            except MergeNotReady:
                outcomes.append(
                    (number, "Protection not ready; later completion event retries")
                )
                continue
            if not result.get("merged"):
                raise RuntimeError("GitHub did not merge the validated head")
            merged = True
            outcomes.append((number, "Merged reviewed head"))
            break
        finally:
            if approval_attempted and not merged:
                # Cover failed/ambiguous creation, exceptions and all pending exits.
                try:
                    current_reviews = pages(f"{path}/reviews")
                except Exception:
                    dismiss_approvals(path, known_approvals, api)
                    raise
                dismiss_approvals(path, known_approvals + current_reviews, api)
    return outcomes


def api(path, method=None, token=None, json_body=None, **fields):
    command = ["gh", "api", path]
    if method:
        command += ["--method", method]
    for key, value in fields.items():
        command += ["-f", f"{key}={value}"]
    if json_body is not None:
        command += ["--input", "-"]
    env = os.environ.copy()
    if token:
        env["GH_TOKEN"] = token
    result = subprocess.run(
        command,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        input=json.dumps(json_body) if json_body is not None else None,
    )
    if result.returncode:
        try:
            status = str(json.loads(result.stdout).get("status", ""))
        except (ValueError, AttributeError):
            status = ""
        if path.endswith("/merge") and status == "405":
            raise MergeNotReady("Protection not ready")
        raise RuntimeError(f"GitHub API failed for {path}; no further action")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def check_states(repo, number, run=subprocess.run):
    """Require all applicable checks, independently of protection's smaller set.

    The informational Codex status is replaced by live inspect() evidence. The
    two continuation workflows are queue orchestration, not PR CI, and must not
    wait for themselves. Required contexts are never excluded.
    """
    states = []
    for required in (True, False):
        command = [
            "gh",
            "pr",
            "checks",
            str(number),
            "--repo",
            repo,
            "--json",
            "name,state,workflow",
        ]
        if required:
            command.append("--required")
        result = run(command, check=False, capture_output=True, text=True, timeout=60)
        try:
            checks = json.loads(result.stdout)
            if not isinstance(checks, list) or (required and not checks):
                return []
            for check in checks:
                if not required and (
                    (check["name"] == gate.CONTEXT and not check["workflow"])
                    or check["workflow"]
                    in {"Dependabot continuation", "Dependabot approval and auto-merge"}
                ):
                    continue
                states.append(check["state"])
        except (ValueError, TypeError, KeyError):
            return []
    return states


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ.get("DEPENDABOT_REVIEW_TOKEN")

    result = reconcile(
        repo,
        gate.pages(f"repos/{repo}/pulls?state=open"),
        api,
        gate.pages,
        lambda number: check_states(repo, number),
        gate.inspect,
        (lambda path, **fields: api(path, token=token, **fields)) if token else None,
        repair=repair_export,
    )
    for number, reason in result:
        print(f"PR #{number}: {reason}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.writelines(
                f"- PR #{number}: {reason}\n" for number, reason in result
            )


if __name__ == "__main__":
    main()
