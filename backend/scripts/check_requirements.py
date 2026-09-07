"""Verify the pip compatibility export matches the authoritative uv lockfile."""

import subprocess
from pathlib import Path

backend = Path(__file__).resolve().parents[1]
result = subprocess.run(
    [
        "uv",
        "export",
        "--locked",
        "--no-dev",
        "--no-emit-project",
        "--format",
        "requirements-txt",
        "--no-header",
    ],
    cwd=backend,
    check=True,
    capture_output=True,
    text=True,
)


def dependencies(content):
    # Ignore generated comments, including the invocation-specific header.
    return [
        line.rstrip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


if dependencies(result.stdout) != dependencies(
    (backend / "requirements.txt").read_text()
):
    raise SystemExit(
        "requirements.txt is stale. From backend/, run: uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt"
    )
print("Runtime requirements match uv.lock")
