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
