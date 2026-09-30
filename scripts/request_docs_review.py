"""Request CodeRabbit once per eligible head; this is not approval or merging."""

import os

try:
    from scripts.codex_review_gate import api, pages
    from scripts.docs_review_policy import inspect_routine
except ModuleNotFoundError:
    from codex_review_gate import api, pages
    from docs_review_policy import inspect_routine


def request(repo, number):
    routine, pr = inspect_routine(repo, number, api, pages)
    if not routine:
        return
    sha = pr["head"]["sha"]
    marker = f"<!-- docs-coderabbit-head:{sha} -->"
    actor = api("user")["login"]
    comments = pages(f"repos/{repo}/issues/{number}/comments")
    if any(
        c.get("user", {}).get("login") == actor and marker in c.get("body", "")
        for c in comments
    ):
        return
    current = api(f"repos/{repo}/pulls/{number}")
    if current["head"]["sha"] != sha or current["state"] != "open" or current["draft"]:
        return
    api(
        f"repos/{repo}/issues/{number}/comments",
        {"body": f"@coderabbitai review\n{marker}"},
    )


if __name__ == "__main__":
    request(os.environ["GITHUB_REPOSITORY"], int(os.environ["PR_NUMBER"]))
