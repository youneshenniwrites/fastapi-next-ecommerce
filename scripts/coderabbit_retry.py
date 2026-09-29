"""Bounded recovery for trusted CodeRabbit rate-limit responses, never approval."""

import re
from datetime import datetime, timedelta, timezone

from coderabbit_review_gate import trusted

MAX_REQUESTS = 3  # initial request plus two retries per head


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (AttributeError, TypeError, ValueError):
        return None


def may_request(comments, sha, is_request, now=None):
    marker = f"<!-- coderabbit-review-head:{sha} -->"
    requests = [c for c in comments if is_request(c) and marker in c.get("body", "")]
    if not requests:
        return True
    if len(requests) >= MAX_REQUESTS:
        return False
    times = [timestamp(c.get("created_at")) for c in requests]
    if any(t is None for t in times):
        return False
    last = max(times)
    last_id = max(
        c.get("id", 0) for c in requests if timestamp(c.get("created_at")) == last
    )
    responses = []
    for comment in comments:
        if not trusted(comment):
            continue
        time = timestamp(comment.get("updated_at") or comment.get("created_at"))
        if time is None:
            return False
        comment_id = comment.get("id", 0)
        if time > last or (time == last and comment_id > last_id):
            responses.append((time, comment_id, comment.get("body", "")))
    if not responses:
        return False
    # A later response supersedes an earlier rate-limit notice.
    time, _, body = max(responses, key=lambda item: (item[0], item[1]))
    if "Review rate limited." not in body and "## Review limit reached" not in body:
        return False
    delay = re.search(r"Next included review available in (\d+) minutes", body)
    if delay:
        minutes = int(delay.group(1))
        if minutes > 10080:
            return False
        cooldown = timedelta(minutes=max(60, minutes + 5))
    else:
        # Unknown reset windows are not permission to retry aggressively.
        cooldown = timedelta(days=1)
    now = now or datetime.now(timezone.utc)
    return now >= time + cooldown
