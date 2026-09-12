"""Fail-closed adapter for Codex's current GitHub summary/reaction protocol.

Only trusted default-branch code may run this with statuses:write. Never execute
PR code. Unknown protocol changes leave the status pending, never approved.
"""

import argparse
import json
import os
import re
import urllib.request

BOT_ID = 199175422
CONTEXT = "Codex review"


def details_url(repo, explicit=None):
    """Link status details to the actual evidence run, never back to the PR."""
    url = explicit
    if not url and os.environ.get("GITHUB_RUN_ID"):
        url = f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    if not url or not re.fullmatch(
        r"https://github\.com/" + re.escape(repo) + r"/actions/runs/\d+(?:/job/\d+)?",
        url,
    ):
        raise ValueError(
            "Publishing requires an Actions run URL (--details-url for local bootstrap)"
        )
    return url


def trusted(value):
    user = value.get("user", {})
    return user.get("id") == BOT_ID and user.get("type") == "Bot"


def review_request(comment):
    return comment.get("author_association") in {
        "OWNER",
        "MEMBER",
        "COLLABORATOR",
    } and bool(
        re.fullmatch(
            r"@codex review(?:\n<!-- codex-review-head:[0-9a-f]{40} -->)?",
            comment.get("body", "").strip(),
        )
    )


def evaluate(sha, comments, reactions, unresolved, reviews=()):
    if unresolved:
        return "pending", "Resolve review conversations and obtain a clean re-review"
    marker = f"<!-- codex-review-head:{sha} -->"
    requests = [c for c in comments if review_request(c)]
    if not requests:
        return "pending", "Awaiting a Codex review request bound to this commit"
    request = max(requests, key=lambda c: c["id"])
    if request.get("updated_at") != request.get("created_at"):
        return "pending", "Post a new unedited review request"
    summaries = [
        c
        for c in comments
        if trusted(c)
        and c.get("body", "").startswith("<!-- codex-pull-request-review-summary -->")
    ]
    if not summaries:
        return "pending", "Waiting for Codex to start reviewing"
    summary = max(summaries, key=lambda c: c["id"])
    if summary["updated_at"] < request["created_at"]:
        return "pending", "Waiting for a fresh review summary"
    rows = [
        line
        for line in summary["body"].splitlines()
        if "**Code Review**" in line and line.startswith("|")
    ]
    if len(rows) != 1:
        return "pending", "Unrecognized Codex review summary; maintainer action needed"
    columns = rows[0].split("|")
    if len(columns) < 5:
        return "pending", "Unrecognized Codex review summary; maintainer action needed"
    commit = re.fullmatch(r"\s*`([0-9a-f]{7,40})`\s*", columns[3])
    if not commit or not sha.startswith(commit[1]):
        return "pending", "Codex has not reviewed the latest commit"
    if "✅ **Completed**" not in columns[2]:
        return "pending", "Codex review is running or has not completed successfully"
    # Codex currently emits either a thumbs-up or an explicit clean-result
    # comment. The latter carries its own reviewed commit; match its exact
    # observed protocol, never an arbitrary mention of 'no issues'.
    clean = [
        c
        for c in comments
        if trusted(c)
        and c.get("created_at", "") >= request["created_at"]
        and c.get("updated_at") == c.get("created_at")
        and c.get("body", "").startswith(
            (
                "Codex Review: Didn't find any major issues. Can't wait for the next one!\n\n",
                "Codex Review: Didn't find any major issues. Swish!\n\n",
            )
        )
        and re.search(
            r"\*\*Reviewed commit:\*\* `" + re.escape(sha[:10]) + r"`(?:\n|$)",
            c["body"],
        )
    ]
    positive = marker in request["body"] and any(
        trusted(r) and r.get("content") == "+1"
        for r in reactions.get(request["id"], [])
    )
    if not positive and not clean:
        return "pending", "Review completed; awaiting Codex's clean-review confirmation"
    # A later review with findings invalidates an older clean result even if
    # somebody resolves its threads without obtaining another clean review.
    signal_time = max((c["created_at"] for c in clean), default=request["created_at"])
    if any(
        trusted(r)
        and (
            not r.get("updated_at")
            or max(r.get("submitted_at") or "", r["updated_at"]) >= signal_time
        )
        and r.get("state") in {"COMMENTED", "CHANGES_REQUESTED", "DISMISSED"}
        for r in reviews
    ):
        return "pending", "Obtain a new clean review after the latest review findings"
    return "success", "Codex clean review confirmed for latest commit; threads resolved"


def api(path, data=None):
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pages(path):
    result = []
    for page in range(1, 101):
        batch = api(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError("Pagination limit exceeded; refusing incomplete evidence")


def threads(repo, number):
    owner, name = repo.split("/")
    cursor = None
    unresolved = False
    seen = set()
    for _ in range(100):
        result = api(
            "graphql",
            {
                "query": """query($owner:String!,$name:String!,$number:Int!,$cursor:String){
          repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100,after:$cursor){
          nodes{isResolved} pageInfo{hasNextPage endCursor}}}}}""",
                "variables": {
                    "owner": owner,
                    "name": name,
                    "number": number,
                    "cursor": cursor,
                },
            },
        )
        if result.get("errors"):
            raise RuntimeError("Cannot retrieve complete review threads")
        connection = result["data"]["repository"]["pullRequest"]["reviewThreads"]
        unresolved |= any(not node["isResolved"] for node in connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            return unresolved
        cursor = connection["pageInfo"]["endCursor"]
        if not cursor or cursor in seen:
            raise RuntimeError("Review-thread pagination did not advance")
        seen.add(cursor)
    raise RuntimeError("Review-thread pagination limit exceeded")


def review_history(repo, number):
    owner, name = repo.split("/")
    cursor = None
    seen = set()
    reviews = []
    for _ in range(100):
        response = api(
            "graphql",
            {
                "query": """query($owner:String!,$name:String!,$number:Int!,$cursor:String){
          repository(owner:$owner,name:$name){pullRequest(number:$number){reviews(first:100,after:$cursor){
          nodes{submittedAt updatedAt state author{__typename ... on Bot{databaseId} ... on User{databaseId}}}
          pageInfo{hasNextPage endCursor}}}}}""",
                "variables": {
                    "owner": owner,
                    "name": name,
                    "number": number,
                    "cursor": cursor,
                },
            },
        )
        if response.get("errors"):
            raise RuntimeError("Cannot retrieve complete review history")
        connection = response["data"]["repository"]["pullRequest"]["reviews"]
        for review in connection["nodes"]:
            author = review.get("author") or {}
            reviews.append(
                {
                    "user": {
                        "id": author.get("databaseId"),
                        "type": author.get("__typename"),
                    },
                    "state": review["state"],
                    "submitted_at": review["submittedAt"],
                    "updated_at": review["updatedAt"],
                }
            )
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]
        if not cursor or cursor in seen:
            raise RuntimeError("Review-history pagination did not advance")
        seen.add(cursor)
    else:
        raise RuntimeError("Review-history pagination limit exceeded")
    # Inline edits may not change their parent review's timestamp. Treat them
    # as findings too, even if the conversation was previously resolved.
    for comment in pages(f"repos/{repo}/pulls/{number}/comments"):
        reviews.append(
            {**comment, "state": "COMMENTED", "submitted_at": comment["created_at"]}
        )
    return reviews


def inspect(repo, number):
    pr = api(f"repos/{repo}/pulls/{number}")
    sha = pr["head"]["sha"]
    comments = pages(f"repos/{repo}/issues/{number}/comments")
    matching = [
        c
        for c in comments
        if review_request(c)
        and f"<!-- codex-review-head:{sha} -->" in c.get("body", "")
    ]
    reactions = {}
    if matching:
        latest = max(matching, key=lambda c: c["id"])
        reactions[latest["id"]] = pages(
            f"repos/{repo}/issues/comments/{latest['id']}/reactions"
        )
    reviews = review_history(repo, number)
    state, reason = evaluate(sha, comments, reactions, threads(repo, number), reviews)
    current = api(f"repos/{repo}/pulls/{number}")
    if current["head"]["sha"] != sha:
        state, reason = "pending", "PR head changed during inspection; retry required"
    elif current["draft"] or current["state"] != "open":
        state, reason = "pending", "PR must be open and ready for review"
    return sha, state, reason


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument(
        "--details-url", help="Actual evidence Actions run URL for local bootstrap"
    )
    args = parser.parse_args()
    target = details_url(args.repo, args.details_url) if args.publish else None
    if args.publish:
        publish_reviews(args.repo, target, args.pr)
    else:
        numbers = (
            [args.pr]
            if args.pr
            else [p["number"] for p in pages(f"repos/{args.repo}/pulls?state=open")]
        )
        for number in numbers:
            report(number, *inspect(args.repo, number))


def report(number, sha, state, reason):
    print(json.dumps({"pr": number, "sha": sha, "state": state, "reason": reason}))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(
                f"### Codex review · PR #{number}\n\n"
                f"- Inspected head: `{sha}`\n- Gate: **{state}**\n- Reason: {reason}\n\n"
                "This job inspects evidence. A successful job alone is not review approval; "
                "the required **Codex review** status must be successful.\n\n"
            )


def latest_status(repo, sha):
    for page in range(1, 101):
        batch = api(f"repos/{repo}/commits/{sha}/statuses?per_page=100&page={page}")
        for status in batch:
            if status.get("context", "").casefold() == CONTEXT.casefold():
                return status
        if len(batch) < 100:
            return None
    raise RuntimeError("Status pagination limit exceeded")


def publish_reviews(repo, target, only_pr=None):
    # Commit statuses are shared by every PR with the same SHA. Always discover
    # all open PRs, even for a scoped refresh, and aggregate their evidence.
    pulls = pages(f"repos/{repo}/pulls?state=open")
    groups = {}
    for pr in pulls:
        groups.setdefault(pr["head"]["sha"], []).append(pr["number"])
    if only_pr is not None:
        groups = {sha: numbers for sha, numbers in groups.items() if only_pr in numbers}
        if not groups:
            raise RuntimeError("Requested PR is not open; no status published")

    def publish(sha, state, reason):
        description = reason[:140]
        try:
            previous = latest_status(repo, sha)
        except Exception:  # noqa: BLE001 - never preserve approval on incomplete status evidence
            api(
                f"repos/{repo}/statuses/{sha}",
                {
                    "state": "pending",
                    "context": CONTEXT,
                    "description": "Status history unavailable; retry required",
                    "target_url": target,
                },
            )
            raise RuntimeError("Status history could not be verified") from None
        # GitHub allows only 1,000 statuses per SHA/context. A scheduled refresh
        # with the same result must not consume another entry just to change its URL.
        if (
            previous
            and previous["state"] == state
            and previous.get("description") == description
        ):
            return
        api(
            f"repos/{repo}/statuses/{sha}",
            {
                "state": state,
                "context": CONTEXT,
                "description": description,
                "target_url": target,
            },
        )

    failures = False
    for sha, numbers in groups.items():
        outcomes = []
        for number in numbers:
            try:
                inspected, state, reason = inspect(repo, number)
                if inspected != sha:
                    state, reason = (
                        "pending",
                        "Head changed since discovery; retry required",
                    )
            except Exception:  # noqa: BLE001 - isolate malformed/API evidence per PR; fail run below
                # Keep this head pending, but inspect the remaining groups.
                failures = True
                state, reason = (
                    "pending",
                    "Evidence API inspection failed; retry required",
                )
            report(number, sha, state, reason)
            outcomes.append((state, reason))
        blocked = next((result for result in outcomes if result[0] != "success"), None)
        state, reason = blocked or (
            "success",
            "All open PRs for this commit have verified clean Codex review",
        )
        try:
            publish(sha, state, reason)
        except Exception:  # noqa: BLE001 - a publication failure must not abandon other heads
            failures = True
            for number in numbers:
                report(
                    number,
                    sha,
                    "pending",
                    "Status publication failed; do not merge until a successful refresh",
                )
    if failures:
        raise RuntimeError(
            "Review refresh incomplete; do not merge until a successful retry"
        )


if __name__ == "__main__":
    main()
