"""Deploy a clean archive and verify public API/database/storefront boundaries."""

import html
import io
import json
import os
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://forme-api-production.vercel.app"
WEB = "https://forme-ecommerce.vercel.app"


def read(url, expected=200, retry=False):
    attempts = 6 if retry else 1
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == attempts:
                raise
            time.sleep(5)
            continue
        if status == expected:
            return body
        if attempt + 1 < attempts:
            time.sleep(5)
    raise RuntimeError(f"Smoke check failed: {url} expected {expected}, got {status}")


def main():
    sha = os.environ["RELEASE_SHA"]
    archive = subprocess.check_output(["git", "archive", sha])
    with tempfile.TemporaryDirectory(prefix="forme-release-") as directory:
        root = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            files.extractall(root, filter="data")
        (root / ".vercel").mkdir()
        for component, variable in [
            ("API", "VERCEL_API_PROJECT_ID"),
            ("storefront", "VERCEL_FRONTEND_PROJECT_ID"),
        ]:
            (root / ".vercel/project.json").write_text(
                json.dumps(
                    {
                        "projectId": os.environ[variable],
                        "orgId": os.environ["VERCEL_ORG_ID"],
                    }
                )
            )
            print(f"Deploying {component} from {sha}", flush=True)
            subprocess.run(
                [
                    "vercel",
                    "deploy",
                    "--prod",
                    "--yes",
                    "--cwd",
                    directory,
                    "--token",
                    os.environ["VERCEL_TOKEN"],
                ],
                check=True,
                env={**os.environ, "VERCEL_PROJECT_ID": os.environ[variable]},
            )
            if component == "API":
                read(API + "/health", retry=True)
                products = json.loads(read(API + "/api/v1/products/", retry=True))
                assert isinstance(products, list) and products, "Demo catalog is empty"
                read(API + "/")  # Dashboard domain link must resolve to docs.
                read(API + "/docs")
                read(API + "/openapi.json")
                read(API + "/api/v1/auth/me", expected=401)
        page = read(WEB, retry=True).decode()
        assert "VINDOR" in page and html.escape(products[0]["name"]) in page, (
            "Catalog did not render"
        )
        read(WEB + "/api/session/me", expected=401)
        # Only test rejection; never automatically replay an authentication write.
        request = urllib.request.Request(
            WEB + "/api/session/logout",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://untrusted.example",
            },
        )
        try:
            urllib.request.urlopen(request, timeout=30)
        except urllib.error.HTTPError as error:
            assert error.code == 403, "Wrong-origin mutation was not rejected"
        else:
            raise RuntimeError("Wrong-origin mutation was accepted")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(
            f"## Production released\n\nCommit: `{sha}`\n\n"
            f"- [Storefront]({WEB})\n- [Swagger]({API}/docs)\n"
            "- Database-backed catalog, API docs, anonymous session and origin checks passed.\n"
            "- No database downgrade or mutation replay is performed on failure.\n"
        )


if __name__ == "__main__":
    main()
