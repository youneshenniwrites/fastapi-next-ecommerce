"""Require a real, current-head CodeRabbit approval; never infer it from prose.

All unresolved review threads block delivery, including those from other reviewers.
This deliberately conservative rule reuses the repository's existing thread gate.
"""

try:
    from scripts import codex_review_gate as evidence
except ModuleNotFoundError:
    import codex_review_gate as evidence

# Verified against GitHub's public users/coderabbitai[bot] endpoint.
BOT_ID = 136622811


def trusted(value):
    user = value.get("user") or {}
    return user.get("id") == BOT_ID and user.get("type") == "Bot"


def assess(sha, reviews, unresolved, history=()):
    """Return GitHub status state/reason from complete review evidence."""
    if unresolved:
        return "pending", "Resolve review conversations before automatic merging"
    approvals = [
        review
        for review in reviews
        if trusted(review)
        and review.get("state") == "APPROVED"
        and review.get("commit_id") == sha
        and review.get("submitted_at")
    ]
    if not approvals:
        return "pending", "Awaiting CodeRabbit approval of the latest commit"
    approved_at = max(review["submitted_at"] for review in approvals)
    # GraphQL supplies update times; inline edits can invalidate a prior approval
    # even when their parent review is unchanged or its thread was resolved.
    for review in [*reviews, *history]:
        if not trusted(review):
            continue
        if review.get("state") in {"COMMENTED", "CHANGES_REQUESTED", "DISMISSED"}:
            timestamp = max(
                review.get("submitted_at") or "", review.get("updated_at") or ""
            )
            if not timestamp or timestamp >= approved_at:
                return "pending", "Obtain CodeRabbit approval after its latest findings"
        elif review.get("state") == "PENDING":
            return "pending", "CodeRabbit has an unfinished review"
    return "success", "CodeRabbit approved the latest commit; review threads resolved"


def inspect(repo, number):
    """Fetch full evidence and reject head changes while inspection is running."""
    path = f"repos/{repo}/pulls/{number}"
    pr = evidence.api(path)
    sha = pr["head"]["sha"]
    reviews = evidence.pages(path + "/reviews")
    history = evidence.review_history(repo, number)
    state, reason = assess(sha, reviews, evidence.threads(repo, number), history)
    current = evidence.api(path)
    if current["head"]["sha"] != sha:
        state, reason = "pending", "PR head changed during inspection; retry required"
    elif current["draft"] or current["state"] != "open":
        state, reason = "pending", "PR must be open and ready for review"
    return sha, state, reason
