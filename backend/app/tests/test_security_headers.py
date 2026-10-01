import pytest
from fastapi.testclient import TestClient

from app.main import app, logger


def assert_security_headers(response):
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


@pytest.mark.parametrize(
    "path,status,content_type",
    [
        ("/health", 200, "application/json"),
        ("/", 307, None),
        ("/docs", 200, "text/html"),
        ("/redoc", 200, "text/html"),
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
    with TestClient(app) as error_client:
        with pytest.raises(RuntimeError, match="fictional failure"):
            error_client.get("/health")
