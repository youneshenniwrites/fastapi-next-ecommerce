"""Placement behavior; PostgreSQL verifies real row-lock concurrency."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart import CartLine
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.order import DraftCreate
from app.services.orders import create_draft, place_order


def prepare(db, user_id, product, quantity=1):
    db.add(CartLine(user_id=user_id, product_id=product.id, quantity=quantity))
    db.commit()
    return create_draft(
        db,
        user_id,
        DraftCreate(lines=[{"product_id": product.id, "quantity": quantity}]),
    ).id


@pytest.fixture
def stocked(db):
    product = Product(name="Fictional item", price=Decimal("0.10"), stock=3)
    db.add(product)
    db.commit()
    return product


def test_placement_retry_and_cart_isolation(client, db, user, token, stocked):
    oid = prepare(db, user.id, stocked, 3)
    other = Product(name="Keep me", price=Decimal("2.00"), stock=1)
    db.add(other)
    db.flush()
    db.add(CartLine(user_id=user.id, product_id=other.id, quantity=1))
    db.commit()
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "purchase-1"}
    first = client.post(f"/api/v1/orders/{oid}/place", headers=headers)
    assert first.status_code == 200
    assert first.json()["status"] == "placed"
    assert first.json()["total"] == "0.30"
    # Simulate losing the response: replay without knowing whether it committed.
    assert (
        client.post(f"/api/v1/orders/{oid}/place", headers=headers).json()
        == first.json()
    )
    assert db.get(Product, stocked.id).stock == 0
    assert db.get(CartLine, (user.id, stocked.id)) is None
    assert db.get(CartLine, (user.id, other.id)).quantity == 1
    headers["Idempotency-Key"] = "different"
    assert (
        client.post(f"/api/v1/orders/{oid}/place", headers=headers).status_code == 409
    )


@pytest.mark.parametrize("change", ["price", "stock", "cart", "missing"])
def test_conflicts_roll_back(db, user, stocked, change):
    oid = prepare(db, user.id, stocked)
    if change == "price":
        stocked.price = Decimal("2.00")
    elif change == "stock":
        stocked.stock = 0
    elif change == "cart":
        db.get(CartLine, (user.id, stocked.id)).quantity = 2
    else:
        db.delete(stocked)
    db.commit()
    with pytest.raises(HTTPException) as error:
        place_order(db, user.id, oid, "retry-key")
    assert error.value.status_code == 409
    saved = db.get(Order, oid)
    assert saved.status == "draft"
    assert saved.idempotency_key is None


def test_key_reuse_and_ownership(db, user, stocked):
    oid = prepare(db, user.id, stocked)
    place_order(db, user.id, oid, "key")
    other = create_draft(
        db, user.id, DraftCreate(lines=[{"product_id": stocked.id, "quantity": 1}])
    )
    with pytest.raises(HTTPException) as error:
        place_order(db, user.id, other.id, "key")
    assert error.value.status_code == 409
    stranger = User(
        email="stranger@example.com", hashed_password="unused", is_active=True
    )
    db.add(stranger)
    db.commit()
    with pytest.raises(HTTPException) as error:
        place_order(db, stranger.id, oid, "key")
    assert error.value.status_code == 404


@pytest.mark.parametrize("same_customer", [False, True])
def test_concurrent_placement(db, user, stocked, same_customer):
    if db.bind.dialect.name != "postgresql":
        pytest.skip("Real PostgreSQL row locks required")
    stocked.stock = 1
    db.commit()
    uid = user.id
    oid = prepare(db, uid, stocked)
    if same_customer:
        targets = [(uid, oid), (uid, oid)]
    else:
        second = User(
            email="concurrent@example.com", hashed_password="unused", is_active=True
        )
        db.add(second)
        db.commit()
        targets = [(uid, oid), (second.id, prepare(db, second.id, stocked))]
    engine = db.bind
    db.rollback()
    barrier = Barrier(2)

    def run(target):
        with Session(engine) as session:
            barrier.wait(timeout=10)
            try:
                result = place_order(session, *target, "shared-key")
                return (200, result.id)
            except HTTPException as error:
                return (error.status_code, None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, targets))
    assert sorted(status for status, _ in results) == (
        [200, 200] if same_customer else [200, 409]
    )
    placed = list(db.scalars(select(Order).where(Order.status == "placed")))
    assert len(placed) == 1
    if same_customer:
        assert results[0] == results[1]
    db.expire_all()
    assert db.get(Product, stocked.id).stock == 0


def test_flush_failure_rolls_back_all_writes(db, user, stocked, monkeypatch):
    oid = prepare(db, user.id, stocked)
    product_id = stocked.id
    uid = user.id
    original = db.commit

    def fail(*args, **kwargs):
        db.flush()
        raise RuntimeError("Disposable post-write failure")

    monkeypatch.setattr(db, "commit", fail)
    with pytest.raises(RuntimeError):
        place_order(db, uid, oid, "failed")
    monkeypatch.setattr(db, "commit", original)
    db.expire_all()
    assert db.get(Product, product_id).stock == 3
    assert db.get(CartLine, (uid, product_id)).quantity == 1
    assert db.get(Order, oid).status == "draft"
    assert db.get(Order, oid).idempotency_key is None


def test_placement_requires_session_and_key(client, db, user, token, stocked):
    oid = prepare(db, user.id, stocked)
    url = f"/api/v1/orders/{oid}/place"
    assert client.post(url, headers={"Idempotency-Key": "key"}).status_code == 401
    auth = {"Authorization": f"Bearer {token}"}
    assert client.post(url, headers=auth).status_code == 422
    assert (
        client.post(url, headers={**auth, "Idempotency-Key": "bad key"}).status_code
        == 422
    )
    user.is_active = False
    db.commit()
    assert (
        client.post(url, headers={**auth, "Idempotency-Key": "key"}).status_code == 401
    )
