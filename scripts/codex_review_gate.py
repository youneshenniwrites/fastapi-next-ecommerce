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


def trusted(value):
    user = value.get("user", {})
    return user.get("id") == BOT_ID and user.get("type") == "Bot"


def evaluate(sha, comments, reactions, unresolved, reviews=()):
    if unresolved:
        return "pending", "Resolve review conversations and obtain a clean re-review"
    marker = f"<!-- codex-review-head:{sha} -->"
    requests = [
        c for c in comments if "@codex review" in c.get("body", "") and not trusted(c)
    ]
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
            "Codex Review: Didn't find any major issues. Can't wait for the next one!\n\n"
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
        and r.get("submitted_at", "") >= signal_time
        and r.get("state") in {"COMMENTED", "CHANGES_REQUESTED"}
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
    while True:
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


def inspect(repo, number):
    pr = api(f"repos/{repo}/pulls/{number}")
    sha = pr["head"]["sha"]
    comments = pages(f"repos/{repo}/issues/{number}/comments")
    matching = [
        c for c in comments if f"<!-- codex-review-head:{sha} -->" in c.get("body", "")
    ]
    reactions = {}
    if matching:
        latest = max(matching, key=lambda c: c["id"])
        reactions[latest["id"]] = pages(
            f"repos/{repo}/issues/comments/{latest['id']}/reactions"
        )
    reviews = pages(f"repos/{repo}/pulls/{number}/reviews")
    state, reason = evaluate(sha, comments, reactions, threads(repo, number), reviews)
    if pr["draft"] or pr["state"] != "open":
        state, reason = "pending", "PR must be open and ready for review"
    return sha, state, reason


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    numbers = (
        [args.pr]
        if args.pr
        else [p["number"] for p in pages(f"repos/{args.repo}/pulls?state=open")]
    )
    for number in numbers:
        if args.publish:
            current = api(f"repos/{args.repo}/pulls/{number}")["head"]["sha"]
            api(
                f"repos/{args.repo}/statuses/{current}",
                {
                    "state": "pending",
                    "context": CONTEXT,
                    "description": "Checking external review evidence",
                },
            )
        sha, state, reason = inspect(args.repo, number)
        print(json.dumps({"pr": number, "sha": sha, "state": state, "reason": reason}))
        if args.publish:
            # Write only to the inspected SHA. A concurrent push gets no success
            # status and must independently pass a new evaluation.
            api(
                f"repos/{args.repo}/statuses/{sha}",
                {
                    "state": state,
                    "context": CONTEXT,
                    "description": reason[:140],
                    "target_url": f"https://github.com/{args.repo}/pull/{number}",
                },
            )


if __name__ == "__main__":
    main()
