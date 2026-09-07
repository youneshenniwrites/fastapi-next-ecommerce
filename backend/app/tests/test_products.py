import pytest

from app.models.product import Product


@pytest.mark.parametrize(
    "role,expected",
    [("anonymous", 401), ("customer", 403), ("admin", 201), ("disabled-admin", 401)],
)
def test_product_write_permissions(client, db, user, token, role, expected):
    user.is_superuser = role in {"admin", "disabled-admin"}
    user.is_active = role != "disabled-admin"
    db.commit()
    headers = {} if role == "anonymous" else {"Authorization": f"Bearer {token}"}
    product = Product(name="Existing", price=10, stock=2)
    db.add(product)
    db.commit()
    response = client.post(
        "/api/v1/products/",
        json={"name": "New", "price": 12, "stock": 3},
        headers=headers,
    )
    assert response.status_code == expected
    update = client.put(
        f"/api/v1/products/{product.id}", json={"name": "Updated"}, headers=headers
    )
    assert update.status_code == (200 if role == "admin" else expected)
    delete = client.delete(f"/api/v1/products/{product.id}", headers=headers)
    assert delete.status_code == (204 if role == "admin" else expected)
    if role != "admin":
        db.refresh(product)
        assert product.name == "Existing"
        assert db.query(Product).count() == 1


def test_catalog_is_public(client, db):
    product = Product(name="Public", price=10, stock=1)
    db.add(product)
    db.commit()
    assert client.get("/api/v1/products/").status_code == 200
    assert client.get(f"/api/v1/products/{product.id}").json()["name"] == "Public"
    assert client.get("/api/v1/products/99999").status_code == 404
