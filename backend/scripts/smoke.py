"""Exercise a running, disposable API without adding third-party dependencies."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

base = os.environ.get("API_BASE_URL", "http://localhost:8000")


def request(path, payload=None, token=None, form=False, expected=200):
    headers = {}
    data = None
    if payload is not None:
        data = (
            urllib.parse.urlencode(payload) if form else json.dumps(payload)
        ).encode()
        headers["Content-Type"] = (
            "application/x-www-form-urlencoded" if form else "application/json"
        )
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(base + path, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        assert response.status == expected, (path, response.status, expected)
        return json.load(response)


request("/health")
email = f"smoke-{uuid.uuid4().hex}@example.com"
password = "Smoke-only-password-123"
registered = request(
    "/api/v1/auth/register", {"email": email, "password": password}, expected=201
)
assert registered["is_superuser"] is False
login = request(
    "/api/v1/auth/login", {"username": email, "password": password}, form=True
)
token = login["access_token"]
assert request("/api/v1/auth/me", token=token)["email"] == email
request("/api/v1/products/")
request(
    "/api/v1/products/", {"name": "Forbidden", "price": 1, "stock": 1}, expected=401
)
request(
    "/api/v1/products/",
    {"name": "Forbidden", "price": 1, "stock": 1},
    token=token,
    expected=403,
)
print(
    "PASS: health, PostgreSQL registration/login/me, public catalog, protected writes"
)
