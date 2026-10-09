"""Request CodeRabbit once per eligible head; this is not approval or merging."""

import argparse
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
    base_ref = pr["base"]["ref"]
    marker = f"<!-- docs-coderabbit-head:{sha} -->"
    actor = api("user")["login"]
    comments = pages(f"repos/{repo}/issues/{number}/comments")
    if any(
        c.get("user", {}).get("login") == actor and marker in c.get("body", "")
        for c in comments
    ):
        return
    current = api(f"repos/{repo}/pulls/{number}")
    if (
        current["head"]["sha"] != sha
        or current["base"]["ref"] != base_ref
        or current["state"] != "open"
        or current["draft"]
    ):
        return
    api(
        f"repos/{repo}/issues/{number}/comments",
        {"body": f"@coderabbitai review\n{marker}"},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--classify", action="store_true")
    args = parser.parse_args()
    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["PR_NUMBER"])
    if args.classify:
        routine, _ = inspect_routine(repo, number, api, pages)
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"eligible={str(routine).lower()}\n")
    else:
        request(repo, number)
