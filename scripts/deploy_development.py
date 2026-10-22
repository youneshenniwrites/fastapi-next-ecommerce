"""Deploy a clean archive to development and verify public API/database/storefront boundaries."""

import html
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://forme-api-development.vercel.app"
WEB = "https://forme-ecommerce-development.vercel.app"
RETRY_ATTEMPTS = 6
RETRY_BUDGET_SECONDS = 60
SINGLE_BUDGET_SECONDS = 30
RETRY_PAUSE_SECONDS = 5
MAX_BODY_BYTES = 1_000_000
_REDIRECTS = {301, 302, 303, 307, 308}
_BASELINE_HEADERS = (
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
)


class _StopRedirects(urllib.request.HTTPRedirectHandler):
    """Refuse urllib's automatic redirect so a bypass header cannot be forwarded."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _Mismatch(Exception):
    """A retryable safe-GET contract failure. The message never carries a body."""

    def __init__(self, status, content_type):
        self.status = status
        self.content_type = content_type
        super().__init__(status)


def protection_headers():
    """Return the optional Vercel protection bypass header for automation."""
    bypass = os.environ.get("VERCEL_PROTECTION_BYPASS")
    return {"x-vercel-protection-bypass": bypass} if bypass else {}


def open_smoke(request, timeout):
    """Open one request. Redirects stay visible and are not followed."""
    opener = urllib.request.build_opener(_StopRedirects)
    return opener.open(request, timeout=timeout)


def _public_target(url):
    parts = urllib.parse.urlsplit(url)
    path = parts.path or "/"
    return f"{parts.scheme}://{parts.hostname}{path}"


def _diagnostic(url, status, content_type):
    shown = content_type or "missing"
    return f"Smoke check failed: HTTP {status} {_public_target(url)} type={shown}"


def _media_type(headers):
    if headers is None:
        return None
    raw = headers.get("Content-Type")
    if not raw:
        return None
    media = raw.split(";", 1)[0].strip().lower()
    return media or None


def _headers_ok(headers):
    return headers is not None and all(
        headers.get(name) == value for name, value in _BASELINE_HEADERS
    )


def _read_body(response, deadline, status, content_type):
    chunks = []
    total = 0
    while True:
        if time.monotonic() >= deadline:
            raise _Mismatch(status, content_type)
        try:
            chunk = response.read(65536)
        except (TimeoutError, urllib.error.URLError):
            raise _Mismatch(status, content_type) from None
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > MAX_BODY_BYTES:
            raise _Mismatch(status, content_type)
        chunks.append(chunk)


def _location_target(url, headers):
    location = headers.get("Location") if headers is not None else None
    if not location or location.startswith("//"):
        return None
    return urllib.parse.urljoin(url, location)


def _same_origin_docs(url, target):
    source = urllib.parse.urlsplit(url)
    dest = urllib.parse.urlsplit(target)
    if source.path not in ("", "/"):
        return False
    if dest.username or dest.path != "/docs" or dest.query or dest.fragment:
        return False
    return (source.scheme, source.hostname, source.port) == (
        dest.scheme,
        dest.hostname,
        dest.port,
    )


def _expect_content(body, contains, status, content_type):
    if not contains:
        return
    required = contains if isinstance(contains, tuple) else (contains,)
    if any(part not in body for part in required):
        raise _Mismatch(status, content_type)


def _expect_json(body, status, content_type, json_status, json_list):
    if not json_status and not json_list:
        return
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise _Mismatch(status, content_type) from None
    if json_status and (not isinstance(payload, dict) or payload.get("status") != "ok"):
        raise _Mismatch(status, content_type)
    if json_list and (not isinstance(payload, list) or not payload):
        raise _Mismatch(status, content_type)


def _open(url, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _Mismatch(0, None)
    request = urllib.request.Request(url, headers=protection_headers())
    try:
        response = open_smoke(request, min(SINGLE_BUDGET_SECONDS, remaining))
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error
    return response.status, response.headers, response


def _fetch(
    url, expected, deadline, content_type, contains, json_status, json_list, hops
):
    status, headers, source = _open(url, deadline)
    try:
        media = _media_type(headers)
        if status in _REDIRECTS:
            if not _headers_ok(headers):
                raise _Mismatch(status, media)
            target = _location_target(url, headers)
            if hops < 1 or target is None or not _same_origin_docs(url, target):
                raise _Mismatch(status, media)
            return _fetch(
                target,
                expected,
                deadline,
                content_type,
                contains,
                json_status,
                json_list,
                hops - 1,
            )
        if status != expected or not _headers_ok(headers):
            raise _Mismatch(status, media)
        if content_type and media != content_type:
            raise _Mismatch(status, media)
        body = _read_body(source, deadline, status, media)
        _expect_content(body, contains, status, media)
        _expect_json(body, status, media, json_status, json_list)
    finally:
        close = getattr(source, "close", None)
        if close is not None:
            close()
    print(
        f"Verified HTTP {status} and baseline headers: {_public_target(url)}",
        flush=True,
    )
    return body


def read(
    url,
    expected=200,
    retry=False,
    content_type=None,
    contains=None,
    json_status=False,
    json_list=False,
    allow_docs_redirect=False,
):
    """Read one safe GET when its status, headers, type and content all match."""
    budget = RETRY_BUDGET_SECONDS if retry else SINGLE_BUDGET_SECONDS
    deadline = time.monotonic() + budget
    attempts = RETRY_ATTEMPTS if retry else 1
    status, content = 0, None
    for attempt in range(attempts):
        if time.monotonic() >= deadline:
            break
        try:
            return _fetch(
                url,
                expected,
                deadline,
                content_type,
                contains,
                json_status,
                json_list,
                1 if allow_docs_redirect else 0,
            )
        except _Mismatch as mismatch:
            status, content = mismatch.status, mismatch.content_type
        except (urllib.error.URLError, TimeoutError):
            status, content = 0, None
        if attempt + 1 == attempts:
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(RETRY_PAUSE_SECONDS, remaining))
    raise RuntimeError(_diagnostic(url, status, content))


def send_once(request):
    """Send one mutation. Transport and response failures are never replayed."""
    try:
        with open_smoke(request, SINGLE_BUDGET_SECONDS) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def main():
    """Deploy the release archive and smoke-test the development environment."""
    sha = os.environ["RELEASE_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("RELEASE_SHA must be a full lowercase commit SHA")
    archive = subprocess.check_output(["git", "archive", sha])
    with tempfile.TemporaryDirectory(prefix="dev-release-") as directory:
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
                    "--env",
                    f"SENTRY_RELEASE={sha}",
                    "--build-env",
                    f"SENTRY_RELEASE={sha}",
                    "--cwd",
                    directory,
                    "--token",
                    os.environ["VERCEL_TOKEN"],
                ],
                check=True,
                env={**os.environ, "VERCEL_PROJECT_ID": os.environ[variable]},
            )
            if component == "API":
                read(
                    API + "/health",
                    retry=True,
                    content_type="application/json",
                    json_status=True,
                )
                products = json.loads(
                    read(
                        API + "/api/v1/products/",
                        retry=True,
                        content_type="application/json",
                        json_list=True,
                    )
                )
                read(
                    API + "/",
                    retry=True,
                    content_type="text/html",
                    allow_docs_redirect=True,
                )
                read(API + "/docs", retry=True, content_type="text/html")
                read(
                    API + "/openapi.json",
                    retry=True,
                    content_type="application/json",
                )
                read(
                    API + "/api/v1/auth/me",
                    expected=401,
                    retry=True,
                    content_type="application/json",
                )
        page = read(
            WEB,
            retry=True,
            content_type="text/html",
            contains=(b"VINDOR", html.escape(products[0]["name"]).encode()),
        ).decode()
        assert "VINDOR" in page and html.escape(products[0]["name"]) in page, (
            "Catalog did not render"
        )
        read(
            WEB + "/api/session/me",
            expected=401,
            retry=True,
            content_type="application/json",
        )
        # Only test rejection; never automatically replay an authentication write.
        request = urllib.request.Request(
            WEB + "/api/session/logout",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://untrusted.example",
                **protection_headers(),
            },
        )
        logout = send_once(request)
        if logout != 403:
            raise RuntimeError(
                f"Smoke check failed: HTTP {logout} /api/session/logout type=missing"
            )
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(
            f"## Development released\n\nCommit: `{sha}`\n\n"
            f"- [Storefront]({WEB})\n- [Swagger]({API}/docs)\n"
            "- Database-backed catalog, API docs, anonymous session and origin checks passed.\n"
            "- Baseline MIME/referrer headers verified on API and storefront smoke responses.\n"
            "- Safe GET checks retry inside one time budget. Only the API root's same-origin "
            "/docs redirect is followed.\n"
            "- No database downgrade or mutation replay is performed on failure.\n"
        )


if __name__ == "__main__":
    main()
