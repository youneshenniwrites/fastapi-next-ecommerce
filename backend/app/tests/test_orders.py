from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token
from app.models.cart import CartLine
from app.models.order import Order, OrderLine
from app.models.product import Product
from app.models.user import User


@pytest.fixture
def product(db):
    """Persist a fictional product; drafting is allowed even without stock."""
    product = Product(name="Draft test", price=Decimal("0.10"), stock=0)
    db.add(product)
    db.commit()
    return product


def headers(token):
    """Provide authenticated headers for the test customer."""
    return {"Authorization": f"Bearer {token}"}


def draft(client, token, product, **extra):
    """Create a draft using only product identity and quantity."""
    return client.post(
        "/api/v1/orders/drafts",
        headers=headers(token),
        json={"lines": [{"product_id": product.id, "quantity": 3}], **extra},
    )


def test_snapshots_survive_catalog_changes_without_claiming_stock(
    client, db, user, token, product
):
    """Drafts preserve exact money and history while leaving stock/cart untouched."""
    db.add(CartLine(user_id=user.id, product_id=product.id, quantity=2))
    db.commit()
    response = draft(client, token, product)
    assert response.status_code == 201
    assert response.headers["cache-control"] == "private, no-store"
    saved = response.json()
    assert saved["status"] == "draft"
    assert saved["currency"] == "GBP"
    assert saved["total"] == "0.30"
    assert saved["lines"][0]["unit_price"] == "0.10"
    assert saved["lines"][0]["line_total"] == "0.30"
    assert product.stock == 0
    assert db.get(CartLine, (user.id, product.id)).quantity == 2
    product.price = Decimal("9.99")
    product.name = "Changed"
    db.commit()
    db.delete(product)
    db.commit()
    result = client.get(f"/api/v1/orders/{saved['id']}", headers=headers(token))
    assert result.status_code == 200
    assert result.json() == saved


def test_ownership_pagination_and_disabled_users(client, db, token, product, user):
    """List/detail/create always use the active authenticated owner, even for admins."""
    first = draft(client, token, product).json()
    second = draft(client, token, product).json()
    assert first["id"] != second["id"]
    assert client.get("/api/v1/orders/?limit=1", headers=headers(token)).json() == [
        first
    ]
    assert client.get(
        f"/api/v1/orders/?after_id={first['id']}", headers=headers(token)
    ).json() == [second]
    other = User(
        email="other@example.com",
        hashed_password="unused",
        is_active=True,
        is_superuser=True,
    )
    db.add(other)
    db.commit()
    other_token = create_access_token(other.id)
    assert client.get("/api/v1/orders/", headers=headers(other_token)).json() == []
    assert (
        client.get(
            f"/api/v1/orders/{first['id']}", headers=headers(other_token)
        ).status_code
        == 404
    )
    assert draft(client, other_token, product, user_id=user.id).status_code == 422
    user.is_active = False
    db.commit()
    for path in ["/api/v1/orders/", f"/api/v1/orders/{first['id']}"]:
        assert client.get(path, headers=headers(token)).status_code == 401
        assert client.get(path).status_code == 401
    assert draft(client, token, product).status_code == 401
    assert client.post("/api/v1/orders/drafts", json={"lines": []}).status_code == 401


@pytest.mark.parametrize(
    "extra",
    [
        {"total": "0.01"},
        {"currency": "USD"},
        {"status": "paid"},
        {"lines": []},
        {"lines": [{"product_id": 1, "quantity": 0}]},
        {"lines": [{"product_id": 1, "quantity": True}]},
        {"lines": [{"product_id": 1, "quantity": 100}]},
        {"lines": [{"product_id": 1, "quantity": 1, "unit_price": "0.01"}]},
        {"lines": [{"product_id": 1, "quantity": 1}] * 2},
        {"lines": [{"product_id": i + 1, "quantity": 1} for i in range(101)]},
    ],
)
def test_rejects_untrusted_or_invalid_drafts(client, db, token, product, extra):
    """No invalid draft creates even a partial record."""
    assert draft(client, token, product, **extra).status_code == 422
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_missing_product_rolls_back_whole_draft(client, db, token, product):
    """A missing line cannot leave an incomplete order behind."""
    result = draft(
        client,
        token,
        product,
        lines=[
            {"product_id": product.id, "quantity": 1},
            {"product_id": 2147483647, "quantity": 1},
        ],
    )
    assert result.status_code == 404
    assert db.scalar(select(func.count()).select_from(Order)) == 0
    assert db.scalar(select(func.count()).select_from(OrderLine)) == 0
    assert draft(client, token, product).status_code == 201


def test_maximum_exact_total(client, db, token):
    """The complete supported basket fits the database money precision."""
    products = [
        Product(name=f"Maximum {i}", price=Decimal("9999999999.99"), stock=0)
        for i in range(100)
    ]
    db.add_all(products)
    db.commit()
    response = client.post(
        "/api/v1/orders/drafts",
        headers=headers(token),
        json={"lines": [{"product_id": p.id, "quantity": 99} for p in products]},
    )
    assert response.status_code == 201
    assert response.json()["total"] == "98999999999901.00"


@pytest.mark.parametrize(
    "field,value", [("total", Decimal("-1")), ("currency", "USD"), ("status", "paid")]
)
def test_database_rejects_invalid_order(db, user, field, value):
    """Database constraints protect against bypassing request validation."""
    order = Order(user_id=user.id, total=Decimal("0"))
    setattr(order, field, value)
    db.add(order)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_failed_flush_rolls_back_header_and_lines(db, user, product, monkeypatch):
    """A database failure after inserts rolls back the entire service transaction."""
    from app.schemas.order import DraftCreate
    from app.services.orders import create_draft

    original = db.flush

    def fail_after_insert(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("disposable injected failure")

    monkeypatch.setattr(db, "flush", fail_after_insert)
    with pytest.raises(RuntimeError, match="disposable"):
        create_draft(
            db, user.id, DraftCreate(lines=[{"product_id": product.id, "quantity": 1}])
        )
    monkeypatch.setattr(db, "flush", original)
    assert db.scalar(select(func.count()).select_from(Order)) == 0
    assert db.scalar(select(func.count()).select_from(OrderLine)) == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", 0),
        ("quantity", 100),
        ("unit_price", Decimal("-0.01")),
        ("product_name", " "),
    ],
)
def test_database_rejects_invalid_lines(db, user, product, field, value):
    """Invalid lines cannot bypass database money and quantity bounds."""
    order = Order(user_id=user.id, total=Decimal("0"))
    line = OrderLine(
        product_id=product.id, product_name="Valid", unit_price=Decimal("0"), quantity=1
    )
    setattr(line, field, value)
    order.lines = [line]
    db.add(order)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_draft_write_limit_does_not_create_another_order(
    client, db, token, product, monkeypatch
):
    """A throttled draft is rejected before any database write."""
    from app.core.rate_limit import write_limiter

    monkeypatch.setattr(write_limiter, "limit", 1)
    assert draft(client, token, product).status_code == 201
    result = draft(client, token, product)
    assert result.status_code == 429
    assert int(result.headers["retry-after"]) > 0
    assert db.scalar(select(func.count()).select_from(Order)) == 1
