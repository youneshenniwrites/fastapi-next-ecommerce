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


@pytest.fixture
def admin_headers(user, token, db):
    user.is_superuser = True
    db.commit()
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "invalid",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "a" * 256},
        {"price": "-0.01"},
        {"price": "1.001"},
        {"price": "NaN"},
        {"price": "Infinity"},
        {"price": "10000000000.00"},
        {"stock": -1},
        {"stock": 2147483648},
        {"stock": 1.5},
        {"stock": True},
        {"currency": "USD"},
        {"currency": "gbp"},
        {"name": None},
        {"price": None},
        {"stock": None},
        {"currency": None},
        {"description": "x" * 10001},
        {"unknown": "value"},
    ],
)
def test_invalid_product_create(client, admin_headers, db, invalid):
    payload = {"name": "Valid", "price": "12.34", "stock": 1, **invalid}
    response = client.post("/api/v1/products/", json=payload, headers=admin_headers)
    assert response.status_code == 422
    assert db.query(Product).count() == 0


@pytest.mark.parametrize(
    "invalid",
    [
        {"name": None},
        {"price": None},
        {"stock": None},
        {"currency": None},
        {"name": " "},
        {"stock": -1},
        {"price": "12.345"},
        {"currency": "EUR"},
    ],
)
def test_invalid_product_update_preserves_record(client, admin_headers, db, invalid):
    product = Product(name="Original", price=12.34, stock=2)
    db.add(product)
    db.commit()
    response = client.put(
        f"/api/v1/products/{product.id}", json=invalid, headers=admin_headers
    )
    assert response.status_code == 422
    db.refresh(product)
    assert product.name == "Original"
    assert product.stock == 2
    assert str(product.price) == "12.34"


def test_decimal_price_roundtrip_and_partial_update(client, admin_headers):
    created = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={"name": "  Tea  ", "price": "19.90", "stock": 2, "description": "Box"},
    )
    assert created.status_code == 201
    product = created.json()
    assert product["name"] == "Tea"
    assert product["price"] == "19.90"
    assert product["currency"] == "GBP"
    url = f"/api/v1/products/{product['id']}"
    response = client.put(url, json={"description": None}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["price"] == "19.90"
    assert client.get(url).json()["currency"] == "GBP"
    assert client.delete(url, headers=admin_headers).status_code == 204
    assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    "query", ["skip=-1", "skip=100001", "limit=0", "limit=-1", "limit=101"]
)
def test_pagination_bounds(client, query):
    assert client.get(f"/api/v1/products/?{query}").status_code == 422


def test_pagination_is_ordered(client, db):
    for index in range(3):
        db.add(Product(name=f"Product {index}", price=0, stock=0))
    db.commit()
    page = client.get("/api/v1/products/?skip=1&limit=1").json()
    assert len(page) == 1
    assert page[0]["name"] == "Product 1"
    assert page[0]["price"] == "0.00"


@pytest.mark.parametrize(
    "values",
    [
        {"name": "   "},
        {"name": "x" * 256},
        {"price": -1},
        {"stock": -1},
        {"stock": 2147483648},
        {"currency": "USD"},
        {"description": "x" * 10001},
    ],
)
def test_database_constraints_reject_invalid_writes(db, values):
    from sqlalchemy import insert
    from sqlalchemy.exc import DataError, IntegrityError

    with pytest.raises((IntegrityError, DataError)):
        db.execute(
            insert(Product).values(
                {"name": "Valid", "price": 1, "stock": 1, "currency": "GBP", **values}
            )
        )
        db.commit()
    db.rollback()


@pytest.mark.parametrize("field", ["name", "price", "stock", "currency"])
def test_database_required_columns(db, field):
    from sqlalchemy import insert
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        db.execute(
            insert(Product).values(
                {
                    "name": "Valid",
                    "price": 1,
                    "stock": 1,
                    "currency": "GBP",
                    field: None,
                }
            )
        )
        db.commit()
    db.rollback()
