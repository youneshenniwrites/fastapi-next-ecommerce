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
        json={
            "name": "New",
            "price": 12,
            "stock": 3,
            "category": "uncategorized",
        },
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
        {"category": "all"},
        {"category": "Not A Slug"},
        {"category": "missing-category"},
        {"category": None},
        {"image": {"key": "https://evil.example/lamp.webp", "alt": "Remote"}},
        {"image": {"key": "../lamp", "alt": "Path"}},
        {"image": {"key": "not-a-photo", "alt": "Missing file"}},
        {"image": {"key": "lamp", "alt": "<img alt=x>"}},
        {"image": {"key": "lamp", "alt": ""}},
        {"image": "lamp"},
        {"material": "<b>oak</b>"},
        {"width_mm": 0},
        {"width_mm": 10001},
        {"height_mm": True},
    ],
)
def test_invalid_product_create(client, admin_headers, db, invalid):
    payload = {
        "name": "Valid",
        "price": "12.34",
        "stock": 1,
        "category": "uncategorized",
        **invalid,
    }
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
        {"category": None},
        {"category": "all"},
        {"category": "missing-category"},
        {"image": {"key": "https://evil.example/lamp.webp", "alt": "Remote"}},
        {"image": {"key": "lamp", "alt": "<script>"}},
        {"material": "<i>felt</i>"},
        {"depth_mm": 0},
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
    assert product.category.slug == "uncategorized"


def test_decimal_price_roundtrip_and_partial_update(client, admin_headers):
    created = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "name": "  Tea  ",
            "price": "19.90",
            "stock": 2,
            "description": "Box",
            "category": "lighting",
        },
    )
    assert created.status_code == 201
    product = created.json()
    assert product["name"] == "Tea"
    assert product["price"] == "19.90"
    assert product["currency"] == "GBP"
    assert product["category"] == {"slug": "lighting", "name": "Lighting"}
    url = f"/api/v1/products/{product['id']}"
    response = client.put(url, json={"description": None}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["price"] == "19.90"
    assert response.json()["category"]["slug"] == "lighting"
    moved = client.put(
        url, json={"category": "writing-and-planning"}, headers=admin_headers
    )
    assert moved.status_code == 200
    assert moved.json()["category"] == {
        "slug": "writing-and-planning",
        "name": "Writing and planning",
    }
    assert moved.json()["price"] == "19.90"
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
    from sqlalchemy import insert, select
    from sqlalchemy.exc import DataError, IntegrityError

    from app.models.category import Category

    category_id = db.scalar(select(Category.id).where(Category.slug == "uncategorized"))
    with pytest.raises((IntegrityError, DataError)):
        db.execute(
            insert(Product).values(
                {
                    "name": "Valid",
                    "price": 1,
                    "stock": 1,
                    "currency": "GBP",
                    "category_id": category_id,
                    **values,
                }
            )
        )
        db.commit()
    db.rollback()


@pytest.mark.parametrize("field", ["name", "price", "stock", "currency", "category_id"])
def test_database_required_columns(db, field):
    from sqlalchemy import insert, select
    from sqlalchemy.exc import IntegrityError

    from app.models.category import Category

    category_id = db.scalar(select(Category.id).where(Category.slug == "uncategorized"))
    with pytest.raises(IntegrityError):
        db.execute(
            insert(Product).values(
                {
                    "name": "Valid",
                    "price": 1,
                    "stock": 1,
                    "currency": "GBP",
                    "category_id": category_id,
                    field: None,
                }
            )
        )
        db.commit()
    db.rollback()


def test_rename_keeps_the_photo_and_leaves_history_unchanged(
    client, db, admin_headers, user, token
):
    """A new name keeps the photograph, stock, cart line and order snapshot."""
    from decimal import Decimal

    from app.models.cart import CartLine
    from app.models.order import Order, OrderLine

    created = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "name": "Task Light",
            "price": "65.00",
            "stock": 8,
            "category": "lighting",
            "image": {
                "key": "lamp",
                "alt": "Representative photograph of a desk lamp",
            },
            "material": "Aluminium",
            "width_mm": 150,
            "depth_mm": 150,
            "height_mm": 420,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["image"] == {
        "key": "lamp",
        "alt": "Representative photograph of a desk lamp",
    }
    assert body["material"] == "Aluminium"
    assert body["height_mm"] == 420
    product_id = body["id"]
    product = db.get(Product, product_id)
    product.reserved_stock = 1
    db.add(CartLine(user_id=user.id, product_id=product_id, quantity=1))
    order = Order(
        user_id=user.id, status="draft", currency="GBP", total=Decimal("65.00")
    )
    order.lines.append(
        OrderLine(
            product_id=product_id,
            product_name="Task Light",
            unit_price=Decimal("65.00"),
            quantity=1,
        )
    )
    db.add(order)
    db.commit()

    user.is_superuser = False
    db.commit()
    forbidden = client.put(
        f"/api/v1/products/{product_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "image": {
                "key": "mat",
                "alt": "Representative photograph of a felt desk mat",
            }
        },
    )
    assert forbidden.status_code == 403
    user.is_superuser = True
    db.commit()

    renamed = client.put(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
        json={"name": "Renamed lamp"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["id"] == product_id
    assert renamed.json()["name"] == "Renamed lamp"
    assert renamed.json()["image"]["key"] == "lamp"
    assert renamed.json()["stock"] == 8
    assert renamed.json()["material"] == "Aluminium"
    db.refresh(product)
    assert product.reserved_stock == 1
    assert db.get(CartLine, (user.id, product_id)).quantity == 1
    line = db.query(OrderLine).filter_by(product_id=product_id).one()
    assert line.product_name == "Task Light"
    assert line.unit_price == Decimal("65.00")

    cleared = client.put(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
        json={"image": None, "height_mm": None},
    )
    assert cleared.status_code == 200
    assert cleared.json()["image"] is None
    assert cleared.json()["height_mm"] is None
    assert cleared.json()["material"] == "Aluminium"
    assert cleared.json()["width_mm"] == 150
    assert cleared.json()["name"] == "Renamed lamp"


def test_absent_facts_are_null(client, admin_headers):
    created = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "name": "Plain object",
            "price": "1.00",
            "stock": 1,
            "category": "uncategorized",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["image"] is None
    assert body["material"] is None
    assert body["width_mm"] is None
    assert body["depth_mm"] is None
    assert body["height_mm"] is None
