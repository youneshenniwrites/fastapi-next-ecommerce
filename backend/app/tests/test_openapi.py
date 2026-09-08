def test_openapi_documents_security_errors_and_money(client):
    schema = client.get("/openapi.json").json()
    assert schema["openapi"].startswith("3.1.")
    paths = schema["paths"]
    assert "401" in paths["/api/v1/auth/me"]["get"]["responses"]
    assert "404" in paths["/api/v1/products/{product_id}"]["get"]["responses"]
    write = paths["/api/v1/products/"]["post"]
    assert write["security"] == [{"OAuth2PasswordBearer": []}]
    assert {"201", "401", "403", "422"} <= write["responses"].keys()
    assert not paths["/api/v1/products/"]["get"].get("security")
    assert (
        schema["components"]["schemas"]["ProductRead"]["properties"]["price"]["type"]
        == "string"
    )
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_api_domain_opens_swagger_without_changing_contract(client):
    for path in ("/", "/?next=https://untrusted.example"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"
    response = client.get("/")
    assert response.status_code == 200
    assert "swagger-ui" in response.text
    assert "/" not in client.get("/openapi.json").json()["paths"]
    assert client.get("/health").json() == {"status": "ok"}
