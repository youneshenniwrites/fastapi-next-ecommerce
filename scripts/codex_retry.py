"""Bounded recovery for observed Codex quota notices, never review approval."""

from datetime import datetime, timedelta, timezone

try:
    from scripts.codex_review_gate import review_request, trusted
except ModuleNotFoundError:
    from codex_review_gate import review_request, trusted

MAX_REQUESTS = 3  # initial request and at most two retries per head
QUOTA_NOTICE = (
    "You have reached your Codex usage limits for code reviews. "
    "You can see your limits in the [Codex usage dashboard]"
    "(https://chatgpt.com/codex/cloud/settings/usage)."
)


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (AttributeError, TypeError, ValueError):
        return None


def may_request(comments, sha, now=None, reviews=()):
    marker = f"<!-- codex-review-head:{sha} -->"
    requests = [
        c for c in comments if review_request(c) and marker in c.get("body", "")
    ]
    if not requests:
        return True
    if len(requests) >= MAX_REQUESTS:
        return False
    # Edited requests cannot establish when the current head was requested.
    times = [timestamp(c.get("created_at")) for c in requests]
    if any(t is None for t in times) or any(
        c.get("created_at") != c.get("updated_at") for c in requests
    ):
        return False
    last = max(times)
    last_id = max(
        c.get("id", 0) for c in requests if timestamp(c.get("created_at")) == last
    )
    for review in reviews:
        if trusted(review):
            time = timestamp(review.get("updated_at") or review.get("submitted_at"))
            if time is None or time >= last:
                return False
    # A newer manual request also owns the review; do not retry over it.
    if any(review_request(c) and c.get("id", 0) > last_id for c in comments):
        return False
    responses = []
    for comment in comments:
        if not trusted(comment):
            continue
        time = timestamp(comment.get("updated_at") or comment.get("created_at"))
        if time is None:
            return False
        comment_id = comment.get("id", 0)
        if time > last or (time == last and comment_id > last_id):
            responses.append((time, comment_id, comment))
    if not responses:
        return False
    # Summary updates, findings and unfamiliar service responses supersede quota.
    time, _, response = max(responses, key=lambda item: (item[0], item[1]))
    if response.get("body", "").strip() != QUOTA_NOTICE or response.get(
        "created_at"
    ) != response.get("updated_at"):
        return False
    # The observed notice has no reset timestamp. Space the final retry far enough
    # apart to allow a weekly allowance reset, without claiming to know its time.
    cooldown = timedelta(days=1 if len(requests) == 1 else 7)
    return (now or datetime.now(timezone.utc)) >= time + cooldown
