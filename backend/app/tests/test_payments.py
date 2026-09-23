"""Sandbox lifecycle regressions with an in-memory Stripe transport boundary."""

import copy
import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal

import pytest
import stripe
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError
from sqlalchemy import select

from app.core.settings import Settings, settings
from app.crud.product import delete_product, update_product
from app.models.order import Order, PaymentEvent
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductUpdate
from app.services import payments
from app.services.orders import place_order
from app.tests.test_placement import prepare


class FakeProvider:
    def __init__(self):
        self.sessions = {}
        self.keys = {}
        self.requests = []
        self.lose_response = False
        self.expire_error = False

    def create(self, params, key):
        self.requests.append((copy.deepcopy(params), key))
        if key not in self.keys:
            sid = f"cs_test_{len(self.sessions) + 1}"
            self.keys[key] = sid
            self.sessions[sid] = dict(
                id=sid,
                livemode=False,
                mode="payment",
                currency="gbp",
                amount_total=sum(
                    line["price_data"]["unit_amount"] * line["quantity"]
                    for line in params["line_items"]
                ),
                metadata=params["metadata"],
                client_reference_id=params["client_reference_id"],
                status="open",
                payment_status="unpaid",
                url=f"https://checkout.stripe.com/c/pay/{sid}",
            )
        if self.lose_response:
            self.lose_response = False
            raise stripe.APIConnectionError("lost response")
        return self.retrieve(self.keys[key])

    def retrieve(self, sid):
        return copy.deepcopy(self.sessions[sid])

    def expire(self, sid):
        if self.expire_error:
            raise stripe.APIConnectionError("uncertain expiry")
        if self.sessions[sid]["status"] != "open":
            raise stripe.InvalidRequestError("Not open", "id")
        self.sessions[sid]["status"] = "expired"
        return self.retrieve(sid)

    def event(self, payload, signature):
        return json.loads(payload)

    def emit(
        self, db, sid, kind="checkout.session.completed", eid="evt_1", **overrides
    ):
        event = dict(
            id=eid, type=kind, livemode=False, data={"object": self.retrieve(sid)}
        )
        event["data"]["object"].update(overrides)
        payments.handle_webhook(db, json.dumps(event).encode(), "fixture")


@pytest.fixture
def provider(monkeypatch):
    fake = FakeProvider()
    monkeypatch.setattr(settings, "STRIPE_ENABLED", True)
    monkeypatch.setattr(settings, "STRIPE_CHECKOUT_ORIGIN", "https://shop.example.test")
    monkeypatch.setattr(payments, "get_provider", lambda: fake)
    return fake


@pytest.fixture
def managed(db, user, provider):
    product = Product(name="Fictional tea", price=Decimal("2.35"), stock=3)
    db.add(product)
    db.commit()
    oid = prepare(db, user.id, product, 2)
    place_order(db, user.id, oid, "managed-key")
    return oid, product.id, user.id


def test_stable_session_and_snapshot(db, managed, provider):
    oid, pid, uid = managed
    first = payments.start_payment(db, uid, oid)
    assert first["order"].payment_status == "pending"
    assert first["checkout_url"].startswith("https://checkout.stripe.com/")
    product = db.get(Product, pid)
    assert (product.stock, product.reserved_stock) == (1, 2)
    product.price = Decimal("9.99")
    db.commit()
    assert payments.start_payment(db, uid, oid)["checkout_url"] == first["checkout_url"]
    assert len(provider.sessions) == len(provider.requests) == 1
    params, key = provider.requests[0]
    assert params["line_items"][0]["price_data"]["unit_amount"] == 235
    assert (
        params["success_url"]
        == f"https://shop.example.test/orders/{oid}?payment=return"
    )
    assert "payment_method_types" not in params
    assert key.startswith("vindor-")


def test_creation_response_loss_reuses_exact_intent(db, managed, provider):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException) as error:
        payments.start_payment(db, uid, oid)
    assert error.value.status_code == 503
    assert db.get(Order, oid).payment_started_at is not None
    assert db.get(Product, pid).reserved_stock == 2
    payments.start_payment(db, uid, oid)
    assert provider.requests[0] == provider.requests[1]
    assert len(provider.sessions) == 1


def test_paid_only_signed_event_and_no_second_decrement(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    assert payments.reconcile_payment(db, uid, oid).payment_status == "pending"
    assert db.get(Order, oid).payment_checkout_url is None
    provider.emit(db, sid)
    provider.emit(db, sid)
    assert db.get(Order, oid).payment_status == "paid"
    assert (db.get(Product, pid).stock, db.get(Product, pid).reserved_stock) == (1, 0)
    assert len(list(db.scalars(select(PaymentEvent)))) == 1
    assert payments.cancel_payment(db, uid, oid).payment_status == "paid"
    assert db.get(Product, pid).stock == 1


@pytest.mark.parametrize("started", [False, True])
def test_cancel_releases_once(db, managed, provider, started):
    oid, pid, uid = managed
    if started:
        payments.start_payment(db, uid, oid)
    assert payments.cancel_payment(db, uid, oid).payment_status == "cancelled"
    assert payments.cancel_payment(db, uid, oid).payment_status == "cancelled"
    assert (db.get(Product, pid).stock, db.get(Product, pid).reserved_stock) == (3, 0)
    if started:
        sid = db.get(Order, oid).payment_session_id
        assert provider.sessions[sid]["status"] == "expired"
        provider.emit(db, sid, kind="checkout.session.expired")
        assert db.get(Order, oid).payment_status == "cancelled"
        assert db.get(Product, pid).stock == 3


def test_cancel_after_lost_creation_response(db, managed, provider):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    assert payments.cancel_payment(db, uid, oid).payment_status == "cancelled"
    assert len(provider.sessions) == 1
    assert db.get(Product, pid).stock == 3


def test_uncertain_expiry_retains_inventory(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    provider.expire_error = True
    with pytest.raises(HTTPException) as error:
        payments.cancel_payment(db, uid, oid)
    assert error.value.status_code == 503
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).stock == 1


def test_completed_delayed_payment_cannot_be_cancelled(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid]["status"] = "complete"
    provider.emit(db, sid)
    assert payments.cancel_payment(db, uid, oid).payment_status == "pending"
    assert db.get(Product, pid).reserved_stock == 2
    provider.emit(
        db, sid, kind="checkout.session.async_payment_failed", eid="evt_failed"
    )
    assert db.get(Order, oid).payment_status == "failed"
    assert db.get(Product, pid).stock == 3


def test_stale_failed_event_does_not_release_paid_session(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    provider.emit(
        db, sid, kind="checkout.session.async_payment_failed", payment_status="unpaid"
    )
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).stock == 1
    provider.emit(
        db, sid, kind="checkout.session.async_payment_succeeded", eid="evt_success"
    )
    assert db.get(Order, oid).payment_status == "paid"


@pytest.mark.parametrize("started", [False, True])
def test_expiry_reconcile(db, managed, provider, started):
    oid, pid, uid = managed
    if started:
        payments.start_payment(db, uid, oid)
        sid = db.get(Order, oid).payment_session_id
        provider.sessions[sid]["status"] = "expired"
    else:
        order = db.get(Order, oid)
        order.payment_expires_at = payments.now() - timedelta(seconds=1)
        db.commit()
    assert payments.reconcile_payment(db, uid, oid).payment_status == "expired"
    assert payments.reconcile_payment(db, uid, oid).payment_status == "expired"
    assert db.get(Product, pid).stock == 3


def test_old_unknown_attempt_is_not_recreated(db, managed, provider):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    order = db.get(Order, oid)
    order.payment_started_at = payments.now() - timedelta(hours=23)
    db.commit()
    with pytest.raises(HTTPException) as error:
        payments.cancel_payment(db, uid, oid)
    assert error.value.status_code == 409
    assert len(provider.requests) == 1
    assert db.get(Product, pid).reserved_stock == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"livemode": True},
        {"amount_total": 1},
        {"currency": "usd"},
        {"id": "cs_test_wrong"},
        {"client_reference_id": "wrong"},
        {"metadata": {"order_id": "1", "payment_reference": "wrong"}},
    ],
)
def test_mismatched_webhook_no_effect(db, managed, provider, changes):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    with pytest.raises(HTTPException):
        provider.emit(db, sid, **changes)
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).reserved_stock == 2
    assert list(db.scalars(select(PaymentEvent))) == []


def test_webhook_before_creation_response(db, managed, provider):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    sid = next(iter(provider.sessions))
    provider.sessions[sid].update(status="complete", payment_status="paid")
    provider.emit(db, sid)
    assert db.get(Order, oid).payment_session_id == sid
    assert payments.start_payment(db, uid, oid)["order"].payment_status == "paid"
    assert len(provider.requests) == 1


def test_paid_never_transitions_or_releases_on_stale_expiry(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    provider.emit(db, sid)
    provider.emit(
        db,
        sid,
        kind="checkout.session.expired",
        eid="evt_expired",
        status="expired",
        payment_status="unpaid",
    )
    assert db.get(Order, oid).payment_status == "paid"
    assert db.get(Product, pid).stock == 1


def test_admin_preserves_reserved_inventory(db, managed):
    oid, pid, uid = managed
    product = db.get(Product, pid)
    with pytest.raises(HTTPException) as error:
        delete_product(db, product)
    assert error.value.status_code == 409
    db.rollback()
    with pytest.raises(HTTPException) as error:
        update_product(db, product, ProductUpdate(stock=2147483647))
    assert error.value.status_code == 409
    db.rollback()
    update_product(db, product, ProductUpdate(stock=2147483645))
    payments.cancel_payment(db, uid, oid)
    assert db.get(Product, pid).stock == 2147483647
    delete_product(db, product)
    assert db.get(Product, pid) is None


@pytest.mark.parametrize("total", ["0.29", "1000000.00"])
def test_unpayable_placement_rolls_back(db, user, provider, total):
    product = Product(name="Amount bound", price=Decimal(total), stock=1)
    db.add(product)
    db.commit()
    oid = prepare(db, user.id, product)
    with pytest.raises(HTTPException) as error:
        place_order(db, user.id, oid, "bound")
    assert error.value.status_code == 409
    assert db.get(Order, oid).status == "draft"
    assert db.get(Product, product.id).stock == 1


def test_api_ownership_private_and_disabled_owner_events(
    client, db, managed, provider, token
):
    oid, pid, uid = managed
    headers = {"Authorization": f"Bearer {token}"}
    for action in ("payment", "cancel", "reconcile"):
        assert client.post(f"/api/v1/orders/{oid}/{action}").status_code == 401
    other = User(
        email="other-payment@example.test", hashed_password="unused", is_active=True
    )
    db.add(other)
    db.commit()
    with pytest.raises(HTTPException) as error:
        payments.start_payment(db, other.id, oid)
    assert error.value.status_code == 404
    response = client.post(f"/api/v1/orders/{oid}/payment", headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert "payment_reference" not in response.text
    assert "payment_request" not in response.text
    db.get(User, uid).is_active = False
    db.commit()
    assert (
        client.post(f"/api/v1/orders/{oid}/cancel", headers=headers).status_code == 401
    )
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    event = dict(
        id="evt_api",
        type="checkout.session.completed",
        livemode=False,
        data={"object": provider.retrieve(sid)},
    )
    assert (
        client.post("/api/v1/payments/webhook", content=json.dumps(event)).status_code
        == 200
    )
    assert db.get(Order, oid).payment_status == "paid"


def test_real_signature_verification(monkeypatch, client):
    secret = "whsec_fictional_test_fixture"
    monkeypatch.setattr(settings, "STRIPE_ENABLED", True)
    monkeypatch.setattr(
        settings, "STRIPE_API_KEY", SecretStr("rk_test_fictional_fixture")
    )
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", SecretStr(secret))
    payload = b'{"id":"evt_signed","type":"unknown.event","livemode":false}'
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256
    ).hexdigest()
    headers = {"Stripe-Signature": f"t={timestamp},v1={signature}"}
    assert (
        client.post(
            "/api/v1/payments/webhook", content=payload, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/payments/webhook", content=payload + b" ", headers=headers
        ).status_code
        == 400
    )
    assert client.post("/api/v1/payments/webhook", content=payload).status_code == 400
    assert (
        client.post("/api/v1/payments/webhook", content=b"x" * 262145).status_code
        == 413
    )


def test_disabled_and_live_configuration():
    base = dict(
        DATABASE_URL="sqlite://",
        SECRET_KEY="fictional-key-with-at-least-32-characters",
        _env_file=None,
    )
    assert not Settings(**base).STRIPE_ENABLED
    with pytest.raises(ValidationError):
        Settings(**base, STRIPE_API_KEY="rk_live_fictional_fixture")
    with pytest.raises(ValidationError):
        Settings(**base, STRIPE_ENABLED=True)
    with pytest.raises(HTTPException) as error:
        payments.get_provider()
    assert error.value.status_code == 503
