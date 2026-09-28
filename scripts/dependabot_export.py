"""Repair a uv export from validated data; never execute or check out PR code."""

import base64
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, urlsplit

import tomllib

UV_VERSION = "0.8.22"
FILES = {"backend/pyproject.toml", "backend/uv.lock", "backend/requirements.txt"}
MAX_BYTES = 2_000_000


class ExportNotSafe(RuntimeError):
    """Input or concurrent state requires maintainer attention."""


def _requirements(value):
    if not isinstance(value, list) or any(
        not isinstance(item, str)
        or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[|\s|[<>=!~;]|$)", item)
        or any(char in item for char in ("@", "://", "\\", "\n", "\r"))
        for item in value
    ):
        raise ExportNotSafe("Only registry dependency declarations can be exported")


def validate_inputs(base_manifest, manifest, lock):
    """Permit dependency edits only, with a single virtual project and PyPI sources."""
    try:
        base = tomllib.loads(base_manifest)
        head = tomllib.loads(manifest)
        locked = tomllib.loads(lock)
        for config in (base, head):
            if "build-system" in config or "uv" in config.get("tool", {}):
                raise ExportNotSafe(
                    "Custom build, uv configuration or workspace is unsupported"
                )
            project = config["project"]
            if project.get("dynamic"):
                raise ExportNotSafe("Dynamic project metadata is unsupported")
            _requirements(project.get("dependencies", []))
            for values in project.get("optional-dependencies", {}).values():
                _requirements(values)
            for values in config.get("dependency-groups", {}).values():
                _requirements(values)
        stripped = []
        for config in (base, head):
            config = copy.deepcopy(config)
            config["project"].pop("dependencies", None)
            config["project"].pop("optional-dependencies", None)
            config.pop("dependency-groups", None)
            stripped.append(config)
        if stripped[0] != stripped[1]:
            raise ExportNotSafe("Nondependency project configuration changed")
        virtual = 0
        for package in locked["package"]:
            source = package["source"]
            if (
                source == {"virtual": "."}
                and package["name"] == head["project"]["name"]
            ):
                virtual += 1
            elif source != {"registry": "https://pypi.org/simple"}:
                raise ExportNotSafe(
                    "Only public PyPI packages and the virtual root are allowed"
                )
            for artifact in (
                [package["sdist"]] if "sdist" in package else []
            ) + package.get("wheels", []):
                url = urlsplit(artifact["url"])
                if (
                    (url.scheme, url.netloc) != ("https", "files.pythonhosted.org")
                    or url.query
                    or url.fragment
                ):
                    raise ExportNotSafe("Non-PyPI package artifact is unsupported")
        if virtual != 1:
            raise ExportNotSafe("Expected exactly one virtual root project")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ExportNotSafe("Malformed dependency metadata") from exc


def _run(command, **kwargs):
    try:
        return subprocess.run(command, check=True, **kwargs)
    except (subprocess.SubprocessError, OSError) as exc:
        raise ExportNotSafe(
            "Isolated pinned uv export failed; maintainer attention required"
        ) from exc


def generate_export(base_manifest, manifest, lock):
    validate_inputs(base_manifest, manifest, lock)
    uv = shutil.which("uv")
    if not uv:
        raise ExportNotSafe("Pinned uv executable unavailable")
    uv = str(Path(uv).resolve())
    with tempfile.TemporaryDirectory(prefix="dependabot-export-") as directory:
        root = Path(directory)
        (root / "pyproject.toml").write_text(manifest)
        (root / "uv.lock").write_text(lock)
        # Allowlist, not a denylist: GitHub/member tokens, proxy credentials and
        # all caller-controlled uv/pip configuration are absent from the child.
        env = {
            "PATH": os.pathsep.join(
                (
                    str(Path(uv).parent),
                    str(Path(sys.executable).parent),
                    "/usr/bin",
                    "/bin",
                )
            ),
            "HOME": directory,
            "UV_CACHE_DIR": str(root / "cache"),
            "UV_PYTHON": sys.executable,
            "UV_PYTHON_DOWNLOADS": "never",
            "UV_NO_CONFIG": "1",
        }
        version = _run(
            [uv, "--version"],
            env=env,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if version.stdout.split()[:2] != ["uv", UV_VERSION]:
            raise ExportNotSafe("Unexpected uv version; refusing export")
        result = _run(
            [
                uv,
                "export",
                "--locked",
                "--offline",
                "--no-config",
                "--no-dev",
                "--no-emit-project",
                "--format",
                "requirements-txt",
                "--no-header",
            ],
            env=env,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if len(result.stdout.encode()) > MAX_BYTES:
            raise ExportNotSafe("Generated export is too large")
        return (
            "# Generated from uv.lock by the trusted dependency continuation.\n"
            + result.stdout
        )


def _snapshot(api, repo, sha, names):
    tree = api(f"repos/{repo}/git/trees/{sha}?recursive=1")
    if tree.get("truncated"):
        raise ExportNotSafe("Repository tree is truncated")
    entries = {item["path"]: item for item in tree["tree"]}
    result = {}
    for name in names:
        entry = entries.get(name, {})
        if (
            entry.get("mode") != "100644"
            or entry.get("type") != "blob"
            or entry.get("size", MAX_BYTES + 1) > MAX_BYTES
        ):
            raise ExportNotSafe("Dependency input must be a bounded regular file")
        blob = api(f"repos/{repo}/git/blobs/{entry['sha']}")
        if (
            blob.get("encoding") != "base64"
            or blob.get("size", MAX_BYTES + 1) > MAX_BYTES
        ):
            raise ExportNotSafe("Unsupported Git blob")
        try:
            value = base64.b64decode("".join(blob["content"].split()), validate=True)
            if len(value) > MAX_BYTES:
                raise ExportNotSafe("Dependency input is too large")
            result[name] = value.decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise ExportNotSafe("Invalid dependency file encoding") from exc
    return result


def _trusted(pr, repo, sha):
    return (
        pr.get("state") == "open"
        and not pr.get("draft")
        and pr.get("user", {}).get("login") == "dependabot[bot]"
        and pr.get("base", {}).get("ref") == "main"
        and (pr.get("head", {}).get("repo") or {}).get("full_name") == repo
        and pr.get("head", {}).get("sha") == sha
        and pr.get("head", {}).get("ref", "").startswith("dependabot/")
    )


def _dependency_lines(content):
    return [
        line.rstrip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def repair_export(repo, number, sha, api, request_api):
    """Return true only after publishing a parent-bound repair commit.

    request_api must accept json_body and use a member/App token so CI runs for
    the new head. A non-fast-forward ref update refuses a concurrent branch push.
    """
    path = f"repos/{repo}/pulls/{number}"
    pr = api(path)
    if not _trusted(pr, repo, sha):
        raise ExportNotSafe("PR trust or head changed")
    count = pr.get("changed_files", 0)
    if not 0 < count <= 100:
        return False
    files = api(f"{path}/files?per_page=100")
    if len(files) != count or any(
        item.get("filename") not in FILES or item.get("status") != "modified"
        for item in files
    ):
        return False
    if not any(item["filename"] == "backend/uv.lock" for item in files):
        return False
    head = _snapshot(api, repo, sha, FILES)
    base_sha = pr["base"]["sha"]
    base = _snapshot(api, repo, base_sha, {"backend/pyproject.toml"})
    output = generate_export(
        base["backend/pyproject.toml"],
        head["backend/pyproject.toml"],
        head["backend/uv.lock"],
    )
    if _dependency_lines(output) == _dependency_lines(head["backend/requirements.txt"]):
        return False
    if request_api is None:
        raise ExportNotSafe("Member token is required to publish export and trigger CI")
    current = api(path)
    if (
        not _trusted(current, repo, sha)
        or current["base"]["sha"] != base_sha
        or current["head"]["ref"] != pr["head"]["ref"]
    ):
        raise ExportNotSafe("PR changed while generating export")
    commit = api(f"repos/{repo}/git/commits/{sha}")
    tree = request_api(
        f"repos/{repo}/git/trees",
        method="POST",
        json_body={
            "base_tree": commit["tree"]["sha"],
            "tree": [
                {
                    "path": "backend/requirements.txt",
                    "mode": "100644",
                    "type": "blob",
                    "content": output,
                }
            ],
        },
    )
    repaired = request_api(
        f"repos/{repo}/git/commits",
        method="POST",
        json_body={
            "message": "fix(deps): regenerate locked runtime requirements (VIN-172)",
            "tree": tree["sha"],
            "parents": [sha],
        },
    )
    request_api(
        f"repos/{repo}/git/refs/heads/{quote(pr['head']['ref'], safe='/')}",
        method="PATCH",
        json_body={"sha": repaired["sha"], "force": False},
    )
    return True
