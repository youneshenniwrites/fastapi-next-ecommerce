"""Trusted-main orchestration; upload reviewed source, never run its build locally."""

import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

try:
    from scripts.preview_ready import verify
except ModuleNotFoundError:
    from preview_ready import verify

TEAM = "team_MSFSDUW2j7TTkmYMixq2uYyM"
PROJECT = "prj_zFV4bUxqaNyhWOtsB6ZUFJbPnvur"
API = "https://forme-api-development.vercel.app"


def vercel_api(path, method="GET"):
    request = urllib.request.Request(
        f"https://api.vercel.com/{path}{'&' if '?' in path else '?'}teamId={TEAM}",
        method=method,
        headers={"Authorization": "Bearer " + os.environ["VERCEL_TOKEN"]},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def audit_project(project, variables):
    """Refuse an unexpected target or inherited preview credentials/configuration."""
    if project.get("id") != PROJECT or project.get("accountId") != TEAM:
        raise ValueError("Unexpected preview project/team")
    if project.get("rootDirectory") != "frontend" or not project.get(
        "autoExposeSystemEnvs"
    ):
        raise ValueError("Preview requires frontend root and provider system variables")
    protection = project.get("ssoProtection") or {}
    if protection.get("deploymentType") not in {
        "all",
        "preview",
        "prod_deployment_urls_and_all_previews",
        "all_except_custom_domains",
    }:
        raise ValueError("Preview deployment protection must remain enabled")
    if not isinstance(variables.get("envs"), list):
        raise TypeError("Missing environment audit evidence")
    for variable in variables["envs"]:
        targets = variable.get("target")
        if (
            not isinstance(targets, list)
            or not targets
            or not set(targets) <= {"development", "preview", "production"}
        ):
            raise ValueError("Unknown environment scope")
    if variables.get("pagination", {}).get("next"):
        raise ValueError("Incomplete environment audit")
    if any("preview" in v.get("target", []) for v in variables.get("envs", [])):
        raise ValueError(
            "Preview scope must be empty; deploy only explicit development configuration"
        )


def require_development_api():
    """Prove the fixed fictional API is reachable without adding preview credentials."""
    checks = [
        ("/health", None, 200, {"status": "ok"}),
        (
            "/api/v1/auth/login",
            urllib.parse.urlencode(
                {
                    "username": f"vin45-probe-{uuid.uuid4().hex}@example.test",
                    "password": "InvalidPreviewProbe123!",
                }
            ).encode(),
            401,
            {"detail": "Incorrect email or password"},
        ),
    ]
    for path, data, status, expected in checks:
        request = urllib.request.Request(
            API + path,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
            if data
            else {},
        )
        try:
            response = urllib.request.urlopen(request, timeout=20)
        except urllib.error.HTTPError as error:
            if error.code != status:
                raise
            response = error
        with response:
            if (
                response.status != status
                or json.loads(response.read(131073)) != expected
            ):
                raise ValueError(
                    "Development API is unavailable or protected; no preview credential is supplied"
                )


def cli_env():
    """No GitHub, database, signing or deployment credential in the child environment."""
    return {
        **{
            key: os.environ[key]
            for key in ("PATH", "HOME", "TMPDIR")
            if key in os.environ
        },
        "NO_UPDATE_NOTIFIER": "1",
        "VERCEL_TELEMETRY_DISABLED": "1",
    }


def extract_source(archive, root):
    """Reject executable CLI config and pre-existing local credentials before upload."""
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        for member in files.getmembers():
            parts = Path(member.name).parts
            name = parts[-1] if parts else ""
            if (
                member.issym()
                or member.islnk()
                or any(p in {".vercel", ".git"} for p in parts)
            ):
                raise ValueError("Archive contains links or local provider credentials")
            if name in {
                "vercel.ts",
                "vercel.js",
                "vercel.mjs",
                "vercel.cjs",
                "vercel.mts",
            } or (name.startswith(".env") and name != ".env.example"):
                raise ValueError(
                    "Archive contains executable CLI config or environment data"
                )
        files.extractall(root, filter="data")


def preview_identity(deployment):
    """Only this exact development preview may be retired; never a stable alias."""
    if (
        deployment.get("projectId") != PROJECT
        or deployment.get("target") not in {None, "preview"}
        or deployment.get("meta", {}).get("vin45") != "reviewed-preview"
        or not re.fullmatch(
            r"[a-f0-9]{40}", deployment.get("meta", {}).get("vin45head", "")
        )
    ):
        raise ValueError("Not a managed development frontend preview")
    identifier = deployment.get("id", "")
    if not re.fullmatch(r"dpl_[A-Za-z0-9]+", identifier):
        raise ValueError("Invalid deployment ID")
    hostname = deployment.get("url", "")
    if not re.fullmatch(r"[a-z0-9-]+\.vercel\.app", hostname):
        raise ValueError("Invalid preview URL")
    return identifier, "https://" + hostname


def created_identity(deployment, sha, number):
    identifier, url = preview_identity(deployment)
    if (
        deployment.get("readyState") != "READY"
        or deployment.get("meta", {}).get("vin45head") != sha
        or deployment.get("meta", {}).get("vin45pr") != str(number)
    ):
        raise ValueError("Preview is not Ready at the requested reviewed revision")
    return identifier, url


def retirement_allowed(deployment, project, aliases):
    identifier, url = preview_identity(deployment)
    production = (project.get("targets") or {}).get("production") or {}
    production_id = production.get("id")
    if (
        project.get("id") != PROJECT
        or not isinstance(production_id, str)
        or not production_id.startswith("dpl_")
    ):
        raise ValueError("Incomplete stable deployment identity")
    if production_id == identifier:
        raise ValueError("Managed preview now serves the stable deployment")
    if not isinstance(aliases.get("aliases"), list) or aliases.get(
        "pagination", {}
    ).get("next"):
        raise ValueError("Incomplete alias evidence")
    if any(
        alias.get("alias") != url.removeprefix("https://")
        for alias in aliases["aliases"]
    ):
        raise ValueError("Preview has an assigned alias; inspect it before retirement")
    return identifier


def main():
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Preview orchestration must run on main")
    if (
        os.environ["VERCEL_ORG_ID"] != TEAM
        or os.environ["VERCEL_FRONTEND_PROJECT_ID"] != PROJECT
    ):
        raise ValueError("Only the approved development frontend is permitted")
    operation = os.environ["PREVIEW_OPERATION"]
    if operation == "retire":
        identifier = os.environ["PREVIEW_DEPLOYMENT_ID"]
        if not re.fullmatch(r"dpl_[A-Za-z0-9]+", identifier):
            raise ValueError("An exact deployment ID is required")
        retirement_allowed(
            vercel_api(f"v13/deployments/{identifier}"),
            vercel_api(f"v9/projects/{PROJECT}"),
            vercel_api(f"v2/deployments/{identifier}/aliases"),
        )
        vercel_api(f"v13/deployments/{identifier}", "DELETE")
        try:
            vercel_api(f"v13/deployments/{identifier}")
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
        else:
            raise RuntimeError(
                "Retirement has not been confirmed; inspect before retrying"
            )
        message = (
            f"Retired managed preview `{identifier}`; stable aliases were not targeted."
        )
    elif operation == "create":
        repo, number, sha = (
            os.environ["GITHUB_REPOSITORY"],
            int(os.environ["PR_NUMBER"]),
            os.environ["PREVIEW_SHA"],
        )
        verify(repo, number, sha)
        audit_project(
            vercel_api(f"v9/projects/{PROJECT}"),
            vercel_api(f"v10/projects/{PROJECT}/env?decrypt=false"),
        )
        subprocess.run(
            ["git", "fetch", "--no-tags", "origin", sha],
            check=True,
            capture_output=True,
        )
        archive = subprocess.check_output(["git", "archive", sha])
        with tempfile.TemporaryDirectory(prefix="reviewed-preview-") as directory:
            root = Path(directory)
            extract_source(archive, root)
            (root / ".vercel").mkdir()
            (root / ".vercel/project.json").write_text(
                json.dumps({"orgId": TEAM, "projectId": PROJECT})
            )
            # A reviewed PR may supply app code, never executable CLI configuration.
            config = Path("frontend/vercel.json").resolve()
            verify(
                repo, number, sha
            )  # Re-read review/CI/head immediately before upload.
            require_development_api()
            command = [
                "vercel",
                "deploy",
                "--yes",
                "--target",
                "preview",
                "--cwd",
                directory,
                "--local-config",
                str(config),
                "--token",
                os.environ["VERCEL_TOKEN"],
                "--meta",
                "vin45=reviewed-preview",
                "--meta",
                f"vin45head={sha}",
                "--meta",
                f"vin45pr={number}",
            ]
            for key, value in {
                "API_BASE_URL": API,
                "APP_ORIGIN_MODE": "vercel-preview",
                "APP_ORIGIN_ALIASES": "[]",
                "ALLOW_LOCAL_HTTP_SESSIONS": "false",
                "SENTRY_RELEASE": sha,
                "SENTRY_ENVIRONMENT": "development",
                "NEXT_PUBLIC_SENTRY_ENVIRONMENT": "development",
                "RATE_LIMIT_DIAGNOSTICS_ENABLED": "false",
                "SENTRY_DIAGNOSTICS_ENABLED": "false",
                "STRIPE_WEBHOOK_RELAY_ENABLED": "false",
            }.items():
                command.extend(
                    ["--env", f"{key}={value}", "--build-env", f"{key}={value}"]
                )
            result = subprocess.run(
                command, env=cli_env(), capture_output=True, text=True, check=False
            )
            if result.returncode:
                # Vendor output may contain build-controlled strings; do not dump it to public logs.
                raise RuntimeError(
                    "Preview build failed; inspect the protected Vercel deployment log"
                )
            urls = re.findall(r"https://[a-z0-9-]+\.vercel\.app", result.stdout)
            if len(urls) != 1:
                raise RuntimeError(
                    "Preview URL not returned; inspect Vercel before retrying"
                )
            identifier, url = created_identity(
                vercel_api(f"v13/deployments/{urls[0].removeprefix('https://')}"),
                sha,
                number,
            )
            message = f"Created reviewed frontend preview of `{sha}`: [preview]({url})\n\nDeployment ID: `{identifier}`.\n\nHosted login/cart acceptance and retirement remain unverified."
    else:
        raise ValueError("Unknown preview operation")
    print(message)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write("## VIN-45 preview\n\n" + message + "\n")


if __name__ == "__main__":
    main()
