"""Conservative routine-prose classification; never execute PR content."""


def routine_path(path):
    return (
        path in {"README.md", "docs/demo.md", "docs/observability.md"}
        or path.startswith("docs/plans/")
    ) and path.endswith(".md")


def eligible(pr, files, repo):
    return (
        pr.get("state") == "open"
        and not pr.get("draft", True)
        and pr.get("base", {}).get("ref") == "main"
        and (pr.get("head", {}).get("repo") or {}).get("full_name") == repo
        and bool(files)
        and len(files) == pr.get("changed_files")
        and all(
            routine_path(f.get("filename", ""))
            and ("previous_filename" not in f or routine_path(f["previous_filename"]))
            for f in files
        )
    )


def inspect_routine(repo, number, api, pages):
    pr = api(f"repos/{repo}/pulls/{number}")
    files = pages(f"repos/{repo}/pulls/{number}/files")
    current = api(f"repos/{repo}/pulls/{number}")
    return (
        pr["head"]["sha"] == current["head"]["sha"]
        and pr["base"]["sha"] == current["base"]["sha"]
        and eligible(current, files, repo)
    ), current
