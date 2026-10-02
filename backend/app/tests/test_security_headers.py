import asyncio
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app.core.security_headers import DENY_CONTENT_POLICY, SecurityHeadersMiddleware
from app.main import app, logger


def assert_security_headers(response):
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["content-security-policy"] == "frame-ancestors 'none'"
    candidate = response.headers["content-security-policy-report-only"]
    assert "default-src 'none'" in candidate
    assert "base-uri 'none'" in candidate
    assert "object-src 'none'" in candidate
    assert "frame-ancestors 'none'" in candidate
    assert "unsafe-eval" not in candidate
    assert "report-uri" not in candidate
    assert "report-to" not in candidate
    if response.request.url.scheme == "https":
        assert response.headers["strict-transport-security"] == "max-age=31536000"
    else:
        assert "strict-transport-security" not in response.headers


@pytest.mark.parametrize(
    "path,status,content_type",
    [
        ("/health", 200, "application/json"),
        ("/", 307, None),
        ("/docs", 200, "text/html"),
        ("/redoc", 200, "text/html"),
        ("/docs/oauth2-redirect", 200, "text/html"),
        ("/openapi.json", 200, "application/json"),
        ("/not-a-route", 404, "application/json"),
        ("/api/v1/auth/me", 401, "application/json"),
        ("/api/v1/products/not-an-id", 422, "application/json"),
    ],
)
def test_real_api_responses_keep_headers_and_content_types(
    client, path, status, content_type
):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == status
    assert_security_headers(response)
    if content_type:
        assert response.headers["content-type"].startswith(content_type)
    else:
        assert response.headers["location"] == "/docs"
    if status == 401:
        assert response.headers["www-authenticate"] == "Bearer"
    if content_type != "text/html":
        assert response.headers["content-security-policy-report-only"] == (
            DENY_CONTENT_POLICY
        )


def test_cors_preflight_keeps_baseline_headers(client):
    response = client.options(
        "/api/v1/products/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert_security_headers(response)
    assert (
        response.headers["content-security-policy-report-only"] == DENY_CONTENT_POLICY
    )


def test_unhandled_failure_keeps_default_body_and_still_propagates(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("fictional failure")

    monkeypatch.setattr(logger, "info", fail)
    with TestClient(app, raise_server_exceptions=False) as error_client:
        response = error_client.get("/health")
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert_security_headers(response)
    assert (
        response.headers["content-security-policy-report-only"] == DENY_CONTENT_POLICY
    )
    with TestClient(app) as error_client:
        with pytest.raises(RuntimeError, match="fictional failure"):
            error_client.get("/health")


class DocumentationTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.styles = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.scripts.append(dict(attrs))
        elif tag == "style":
            self.styles.append(dict(attrs))


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/docs/oauth2-redirect"])
def test_documentation_nonces_are_fresh_and_match_candidate_policy(client, path):
    nonces = []
    for _ in range(2):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-store"
        tags = DocumentationTags()
        tags.feed(response.text)
        assert tags.scripts
        nonce = tags.scripts[0]["nonce"]
        assert len(nonce) >= 32
        nonces.append(nonce)
        assert all(tag.get("nonce") == nonce for tag in tags.scripts + tags.styles)
        candidate = response.headers["content-security-policy-report-only"]
        assert f"script-src 'nonce-{nonce}'" in candidate
        assert "'unsafe-inline'" not in next(
            directive
            for directive in candidate.split("; ")
            if directive.startswith("script-src ")
        )
        assert all(
            tag.get("src", "https://cdn.jsdelivr.net").startswith(
                "https://cdn.jsdelivr.net/"
            )
            for tag in tags.scripts
            if "src" in tag
        )
        if path != "/docs/oauth2-redirect":
            assert "style-src-attr 'unsafe-inline'" in candidate
            assert f"style-src 'self' 'nonce-{nonce}'" in candidate
            style_elements = next(
                directive
                for directive in candidate.split("; ")
                if directive.startswith("style-src ")
            )
            assert "'unsafe-inline'" not in style_elements
        if path == "/redoc":
            assert '"nonce": "' + nonce + '"' in response.text
            assert "Redoc.init(" in response.text
            assert "fonts.googleapis.com" not in response.text + candidate
            assert "fonts.gstatic.com" not in response.text + candidate
            assert (
                "https://cdn.jsdelivr.net/npm/redoc@2.5.4/bundles/redoc.standalone.js"
                in response.text
            )
            assert "https://cdn.redoc.ly" in candidate
            assert (
                "'sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU='"
                in style_elements
            )
            assert (
                "'sha256-QMIg+bpjm3JdElJ388KYke01izlUW0UoNOeKjpMxdgc='"
                in style_elements
            )
        else:
            assert "https://cdn.redoc.ly" not in candidate
            assert "sha256-" not in candidate
        if path == "/docs":
            assert "SwaggerUIBundle.presets.apis" in response.text
            assert (
                "oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect'"
                in (response.text)
            )
        if path == "/docs/oauth2-redirect":
            assert "window.opener.swaggerUIRedirectOauth2" in response.text
            assert "https://cdn.jsdelivr.net" not in candidate
    assert nonces[0] != nonces[1]


def test_documentation_preserves_proxy_prefix_and_schema_contract():
    with TestClient(app, root_path="/prefix") as docs_client:
        swagger = docs_client.get("/docs")
        redoc = docs_client.get("/redoc")
    assert "url: '/prefix/openapi.json'" in swagger.text
    assert "window.location.origin + '/prefix/docs/oauth2-redirect'" in swagger.text
    assert 'Redoc.init("/prefix/openapi.json"' in redoc.text
    schema = app.openapi()
    assert {"/docs", "/redoc", "/docs/oauth2-redirect"}.isdisjoint(schema["paths"])
    assert (
        schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"][
            "password"
        ]["tokenUrl"]
        == "/api/v1/auth/login"
    )


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/docs/oauth2-redirect"])
def test_documentation_head_and_errors_keep_method_semantics(client, path):
    response = client.head(path)
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["cache-control"] == "private, no-store"
    assert (
        "script-src 'nonce-" in response.headers["content-security-policy-report-only"]
    )
    error = client.post(path)
    assert error.status_code == 405
    assert_security_headers(error)
    assert error.headers["content-security-policy-report-only"] == DENY_CONTENT_POLICY


def test_hsts_uses_https_scope_and_ignores_forwarded_proto(client):
    spoofed = client.get("/health", headers={"X-Forwarded-Proto": "https"})
    assert "strict-transport-security" not in spoofed.headers
    with TestClient(app, base_url="https://testserver") as secure_client:
        for path in ["/health", "/not-a-route", "/docs"]:
            assert_security_headers(secure_client.get(path))
        preflight = secure_client.options(
            "/api/v1/products/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert_security_headers(preflight)


def test_unhandled_https_error_keeps_transport_and_candidate_headers(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("fictional failure")

    monkeypatch.setattr(logger, "info", fail)
    with TestClient(
        app, base_url="https://testserver", raise_server_exceptions=False
    ) as secure_client:
        response = secure_client.get("/health")
    assert response.status_code == 500
    assert_security_headers(response)
    assert (
        response.headers["content-security-policy-report-only"] == DENY_CONTENT_POLICY
    )


@pytest.mark.parametrize("scope_type", ["websocket", "lifespan"])
def test_non_http_scopes_pass_through_unchanged(scope_type):
    scope = {"type": scope_type}
    message = {"type": f"{scope_type}.fictional", "data": "unchanged"}
    sent = []

    async def receive():
        return message

    async def send(received):
        sent.append(received)

    async def downstream(received_scope, received_receive, received_send):
        assert received_scope is scope
        assert received_receive is receive
        assert received_send is send
        await received_send(await received_receive())

    asyncio.run(SecurityHeadersMiddleware(downstream)(scope, receive, send))
    assert scope == {"type": scope_type}
    assert sent == [message]
