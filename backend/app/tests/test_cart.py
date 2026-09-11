from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.cart import set_quantity
from app.models.cart import CartLine
from app.models.product import Product
from app.models.user import User


@pytest.fixture
def product(db):
    """Persist a fictional product with enough stock for quantity boundary tests."""
    item = Product(name="Cart test", price=Decimal("19.99"), stock=99)
    db.add(item)
    db.commit()
    return item


def headers(token):
    """Build bearer headers without exposing the token in test output."""
    return {"Authorization": f"Bearer {token}"}


def put(client, token, product, quantity, **extra):
    """Submit an absolute quantity with optional fields for rejection tests."""
    return client.put(
        f"/api/v1/cart/items/{product.id}",
        headers=headers(token),
        json={"quantity": quantity, **extra},
    )


def test_cart_current_money_stock_and_idempotence(client, db, product, token):
    """Verify retries, live prices, visible shortages, reductions and repeat removal."""
    assert client.get("/api/v1/cart/", headers=headers(token)).json()["items"] == []
    for _ in range(2):
        result = put(client, token, product, 3)
        assert result.status_code == 200
        assert result.headers["cache-control"] == "private, no-store"
        assert result.json()["subtotal"] == "59.97"
        assert len(result.json()["items"]) == 1
    product.price = Decimal("0.10")
    product.stock = 1
    db.commit()
    result = client.get("/api/v1/cart/", headers=headers(token)).json()
    assert result["subtotal"] == "0.30"
    assert result["items"][0]["available"] is False
    assert result["items"][0]["quantity"] == 3
    assert put(client, token, product, 4).status_code == 409
    assert put(client, token, product, 3).status_code == 200
    assert put(client, token, product, 2).status_code == 200
    assert put(client, token, product, 1).json()["items"][0]["available"] is True
    for _ in range(2):
        assert (
            client.delete(
                f"/api/v1/cart/items/{product.id}", headers=headers(token)
            ).status_code
            == 204
        )
    assert (
        client.get("/api/v1/cart/", headers=headers(token)).json()["subtotal"] == "0.00"
    )


@pytest.mark.parametrize("quantity", [0, -1, 100, 1.5, "2", True, None])
def test_invalid_quantity(client, product, token, quantity):
    """Reject out-of-range values and coercions such as strings and booleans."""
    assert put(client, token, product, quantity).status_code == 422


def test_stock_missing_and_untrusted_fields(client, db, product, token):
    """Reject unavailable additions, missing products and client authority fields."""
    product.stock = 0
    db.commit()
    assert put(client, token, product, 1).status_code == 409
    for field in ("user_id", "price", "subtotal", "product_id"):
        assert put(client, token, product, 1, **{field: 1}).status_code == 422
    assert (
        client.put(
            "/api/v1/cart/items/2147483647",
            headers=headers(token),
            json={"quantity": 1},
        ).status_code
        == 404
    )
    assert (
        client.put(
            "/api/v1/cart/items/0", headers=headers(token), json={"quantity": 1}
        ).status_code
        == 422
    )


def test_auth_and_customer_isolation(client, db, product, user, token):
    """Keep carts separate and deny anonymous, expired and disabled credentials."""
    assert put(client, token, product, 2).status_code == 200
    other = User(email="other@example.com", hashed_password="unused", is_active=True)
    db.add(other)
    db.commit()
    other_token = create_access_token(other.id)
    assert (
        client.get("/api/v1/cart/", headers=headers(other_token)).json()["items"] == []
    )
    assert (
        client.delete(
            f"/api/v1/cart/items/{product.id}", headers=headers(other_token)
        ).status_code
        == 204
    )
    assert put(client, other_token, product, 4).status_code == 200
    assert (
        client.get("/api/v1/cart/", headers=headers(token)).json()["items"][0][
            "quantity"
        ]
        == 2
    )
    expired = create_access_token(user.id, expires_delta=timedelta(seconds=-1))
    for auth in ({}, headers(expired)):
        assert client.get("/api/v1/cart/", headers=auth).status_code == 401
        assert (
            client.put(
                f"/api/v1/cart/items/{product.id}", headers=auth, json={"quantity": 1}
            ).status_code
            == 401
        )
        assert (
            client.delete(f"/api/v1/cart/items/{product.id}", headers=auth).status_code
            == 401
        )
    user.is_active = False
    db.commit()
    assert put(client, token, product, 1).status_code == 401
    assert client.get("/api/v1/cart/", headers=headers(token)).status_code == 401
    assert (
        client.delete(
            f"/api/v1/cart/items/{product.id}", headers=headers(token)
        ).status_code
        == 401
    )


def test_persistence_and_product_deletion(client, db, product, user, token):
    """Restore saved lines across sessions and remove them when products are deleted."""
    assert put(client, token, product, 99).status_code == 200
    # New DB session (as after process restart), and a fresh login/token.
    with Session(db.get_bind()) as fresh:
        assert fresh.get(CartLine, (user.id, product.id)).quantity == 99
    login = client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "password123"}
    )
    assert (
        client.get(
            "/api/v1/cart/", headers=headers(login.json()["access_token"])
        ).json()["items"][0]["quantity"]
        == 99
    )
    user.is_superuser = True
    db.commit()
    assert (
        client.delete(
            f"/api/v1/products/{product.id}", headers=headers(token)
        ).status_code
        == 204
    )
    assert client.get("/api/v1/cart/", headers=headers(token)).json()["items"] == []
    assert db.scalar(select(func.count()).select_from(CartLine)) == 0


def test_database_constraints(db, product, user):
    """Reject invalid quantities and orphaned ownership references at the database."""
    for user_id, product_id, quantity in [
        (user.id, product.id, 0),
        (user.id, product.id, 100),
        (2147483647, product.id, 1),
        (user.id, 2147483647, 1),
    ]:
        db.add(CartLine(user_id=user_id, product_id=product_id, quantity=quantity))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_postgres_concurrent_duplicate_and_updates(db, product, user):
    """Verify separate PostgreSQL transactions cannot create duplicate customer lines."""
    if db.get_bind().dialect.name != "postgresql":
        pytest.skip("PostgreSQL row-lock semantics are verified in integration CI")
    uid, pid = user.id, product.id
    db.commit()
    for quantities in ((2, 2), (3, 4)):
        barrier = Barrier(2)

        def worker(quantity):
            """Race an independent transaction against the other absolute quantity write."""
            with Session(db.get_bind()) as session:
                barrier.wait(timeout=10)
                return set_quantity(session, uid, pid, quantity)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, quantities))
        assert all(len(result.items) == 1 for result in results)
        db.expire_all()
        assert db.get(CartLine, (uid, pid)).quantity in quantities
        assert db.scalar(select(func.count()).select_from(CartLine)) == 1
        db.commit()


def test_multiple_products_and_maximum_money(client, db, product, token):
    """Sum multiple lines exactly even when totals exceed the product price range."""
    product.price = Decimal("9999999999.99")
    second = Product(name="Second", price=Decimal("0.01"), stock=2)
    db.add(second)
    db.commit()
    assert put(client, token, product, 99).status_code == 200
    result = put(client, token, second, 2).json()
    assert result["subtotal"] == "989999999999.03"
    assert [item["product"]["id"] for item in result["items"]] == [
        product.id,
        second.id,
    ]


def test_unique_line_and_customer_cascade(db, product, user):
    """Reject duplicate lines and cascade customer deletion to saved cart data."""
    uid, pid = user.id, product.id
    db.add(CartLine(user_id=uid, product_id=pid, quantity=1))
    db.commit()
    from sqlalchemy import insert

    with pytest.raises(IntegrityError):
        db.execute(insert(CartLine).values(user_id=uid, product_id=pid, quantity=2))
        db.commit()
    db.rollback()
    db.delete(user)
    db.commit()
    assert db.scalar(select(func.count()).select_from(CartLine)) == 0
