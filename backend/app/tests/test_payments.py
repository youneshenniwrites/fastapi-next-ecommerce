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

    def account_id(self):
        return "acct_fictional_fixture"

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


def test_operator_recovery_after_idempotency_window(db, managed, provider):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    order = db.get(Order, oid)
    order.payment_started_at = payments.now() - timedelta(days=2)
    db.commit()
    sid = next(iter(provider.sessions))
    provider.sessions[sid]["status"] = "expired"
    assert payments.reconcile_known_session(db, oid, sid).payment_status == "expired"
    assert db.get(Product, pid).stock == 3
    assert len(provider.requests) == 1


def test_real_sdk_transport_serialization(monkeypatch):
    """Exercise real SDK method routing, resource conversion and retry-key headers."""
    from stripe._http_client import HTTPClient

    from app.providers.stripe import StripeProvider

    class Transport(HTTPClient):
        name = "in-memory"

        def request(self, method, url, headers, post_data=None, *, _usage=None):
            calls.append((method, url, dict(headers), post_data))
            if url.endswith("/v1/account"):
                return b'{"id":"acct_sdk","object":"account"}', 200, {}
            return (
                json.dumps(
                    {
                        "id": "cs_test_sdk",
                        "object": "checkout.session",
                        "metadata": {"order_id": "1"},
                    }
                ).encode(),
                200,
                {},
            )

    calls = []
    monkeypatch.setattr(
        settings, "STRIPE_API_KEY", SecretStr("rk_test_fictional_fixture")
    )
    provider = StripeProvider()
    provider.client = stripe.StripeClient(
        "rk_test_fictional_fixture", http_client=Transport()
    )
    params = {
        "mode": "payment",
        "line_items": [
            {
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": 235,
                    "product_data": {"name": "Fictional tea"},
                },
                "quantity": 2,
            }
        ],
        "integration_identifier": "vindor_abcdefgh",
    }
    assert provider.account_id() == "acct_sdk"
    assert calls.pop()[1].endswith("/v1/account")
    assert provider.create(params, "durable-key")["metadata"] == {"order_id": "1"}
    assert calls[0][2]["Idempotency-Key"] == "durable-key"
    from urllib.parse import parse_qs

    assert parse_qs(calls[0][3])["line_items[0][price_data][unit_amount]"] == ["235"]
    assert provider.retrieve("cs_test_sdk")["id"] == "cs_test_sdk"
    assert provider.expire("cs_test_sdk")["id"] == "cs_test_sdk"
    assert calls[-1][1].endswith("/v1/checkout/sessions/cs_test_sdk/expire")


def test_reconciliation_cli_is_bounded_and_reports_cursor(
    db, managed, provider, monkeypatch, capsys
):
    from app import reconcile_payments

    oid, _, _ = managed
    monkeypatch.setattr(reconcile_payments, "SessionLocal", lambda: db)
    monkeypatch.setattr("sys.argv", ["reconcile", "--limit", "1"])
    reconcile_payments.main()
    output = capsys.readouterr().out
    assert f"Order {oid}: pending" in output
    assert f"Next cursor: --after-id {oid}" in output
    monkeypatch.setattr("sys.argv", ["reconcile", "--order-id", str(oid)])
    with pytest.raises(SystemExit) as error:
        reconcile_payments.main()
    assert error.value.code == 2


def test_legacy_placed_orders_stay_unmanaged(db, user, provider, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_ENABLED", False)
    product = Product(name="Legacy item", price=Decimal("1.00"), stock=1)
    db.add(product)
    db.commit()
    oid = prepare(db, user.id, product)
    place_order(db, user.id, oid, "legacy")
    monkeypatch.setattr(settings, "STRIPE_ENABLED", True)
    for action in (
        payments.start_payment,
        payments.cancel_payment,
        payments.reconcile_payment,
    ):
        with pytest.raises(HTTPException) as error:
            action(db, user.id, oid)
        assert error.value.status_code == 409
    assert db.get(Product, product.id).reserved_stock == 0
    assert provider.requests == []


def test_paid_after_released_inventory_is_never_marked_paid(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    payments.cancel_payment(db, uid, oid)
    provider.sessions[sid].update(status="complete", payment_status="paid")
    with pytest.raises(HTTPException) as error:
        provider.emit(db, sid)
    assert error.value.status_code == 409
    assert db.get(Order, oid).payment_status == "cancelled"
    assert db.get(Product, pid).stock == 3
    assert list(db.scalars(select(PaymentEvent))) == []


def test_inventory_effect_and_deduplication_roll_back_together(
    db, managed, provider, monkeypatch
):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    original_commit = db.commit

    def fail_commit():
        db.flush()
        raise RuntimeError("disposable database fault after effects")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError):
        provider.emit(db, sid)
    monkeypatch.setattr(db, "commit", original_commit)
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).reserved_stock == 2
    assert list(db.scalars(select(PaymentEvent))) == []
    provider.emit(db, sid)
    assert db.get(Order, oid).payment_status == "paid"


def test_customer_explicit_status_and_cancel_endpoints(client, db, managed, token):
    oid, pid, _ = managed
    headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.post(f"/api/v1/orders/{oid}/reconcile", headers=headers).json()[
            "payment_status"
        ]
        == "pending"
    )
    response = client.post(f"/api/v1/orders/{oid}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json()["payment_status"] == "cancelled"
    assert db.get(Product, pid).stock == 3


@pytest.mark.parametrize(
    "delay", [timedelta(minutes=31), timedelta(hours=22, minutes=59)]
)
def test_never_received_create_remains_valid_through_replay_window(
    db, managed, provider, monkeypatch, delay
):
    """A transport failure before Stripe sees the request must not strand stock."""
    oid, _, uid = managed
    clock = [payments.now()]
    monkeypatch.setattr(payments, "now", lambda: clock[0])
    create = provider.create
    calls = []

    def validation_aware_create(params, key):
        calls.append(copy.deepcopy(params))
        if len(calls) == 1:
            raise stripe.APIConnectionError("Request never reached Stripe")
        if params["expires_at"] < int(clock[0].timestamp()) + 1800:
            raise stripe.InvalidRequestError(
                "expires_at must be at least 30 minutes ahead",
                "expires_at",
                http_status=400,
            )
        return create(params, key)

    monkeypatch.setattr(provider, "create", validation_aware_create)
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    clock[0] += delay
    result = payments.start_payment(db, uid, oid)
    assert result["checkout_url"]
    assert len(provider.sessions) == 1
    assert calls[0] == calls[1]


def test_generic_create_rejection_never_proves_absence(
    db, managed, provider, monkeypatch
):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)

    def reject(*_):
        raise stripe.InvalidRequestError(
            "Pre-idempotency validation failure", "expires_at", http_status=400
        )

    monkeypatch.setattr(provider, "create", reject)
    with pytest.raises(HTTPException) as error:
        payments.cancel_payment(db, uid, oid)
    assert error.value.status_code == 503
    assert len(provider.sessions) == 1
    assert db.get(Product, pid).reserved_stock == 2


def prepare_unknown_scan(db, managed, provider, monkeypatch):
    oid, _, uid = managed

    def reject(*_):
        raise stripe.InvalidRequestError(
            "Deterministic rejection without a session", "line_items", http_status=400
        )

    monkeypatch.setattr(provider, "create", reject)
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    deadline = payments.aware(db.get(Order, oid).payment_expires_at)
    monkeypatch.setattr(payments, "now", lambda: deadline + timedelta(minutes=6))
    return oid


def test_complete_absence_scan_releases_rejected_creation_once(
    db, managed, provider, monkeypatch
):
    oid = prepare_unknown_scan(db, managed, provider, monkeypatch)
    calls = []

    def find(reference, expiry):
        calls.append((reference, expiry))
        assert not db.in_transaction()
        return [], True

    monkeypatch.setattr(provider, "find_sessions", find, raising=False)
    assert payments.reconcile_unknown_session(db, oid).payment_status == "expired"
    assert payments.reconcile_unknown_session(db, oid).payment_status == "expired"
    assert db.get(Product, managed[1]).stock == 3
    assert len(calls) == 1


@pytest.mark.parametrize("outcome", ["incomplete", "ambiguous", "unavailable"])
def test_unproven_absence_keeps_reservation(
    db, managed, provider, monkeypatch, outcome
):
    oid = prepare_unknown_scan(db, managed, provider, monkeypatch)

    def find(*_):
        if outcome == "unavailable":
            raise stripe.APIConnectionError("Cannot scan provider")
        return (
            [{"id": "one"}, {"id": "two"}] if outcome == "ambiguous" else []
        ), outcome == "ambiguous"

    monkeypatch.setattr(provider, "find_sessions", find, raising=False)
    with pytest.raises(HTTPException):
        payments.reconcile_unknown_session(db, oid)
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, managed[1]).reserved_stock == 2


def test_scan_refuses_open_creation_window(db, managed, provider, monkeypatch):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    with pytest.raises(HTTPException) as error:
        payments.reconcile_unknown_session(db, oid)
    assert error.value.status_code == 409
    assert db.get(Product, pid).reserved_stock == 2


@pytest.mark.parametrize("paid", [False, True])
def test_scan_recovers_matching_session_without_recreating(
    db, managed, provider, monkeypatch, paid
):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    deadline = payments.aware(db.get(Order, oid).payment_expires_at)
    monkeypatch.setattr(payments, "now", lambda: deadline + timedelta(minutes=6))
    sid = next(iter(provider.sessions))
    provider.sessions[sid].update(
        status="complete" if paid else "expired",
        payment_status="paid" if paid else "unpaid",
    )
    monkeypatch.setattr(
        provider,
        "find_sessions",
        lambda *_: ([provider.retrieve(sid)], True),
        raising=False,
    )
    result = payments.reconcile_unknown_session(db, oid)
    assert result.payment_status == ("pending" if paid else "expired")
    assert db.get(Product, pid).stock == (1 if paid else 3)
    assert len(provider.requests) == 1


def test_scan_rechecks_concurrent_webhook_binding(db, managed, provider, monkeypatch):
    oid, pid, uid = managed
    provider.lose_response = True
    with pytest.raises(HTTPException):
        payments.start_payment(db, uid, oid)
    deadline = payments.aware(db.get(Order, oid).payment_expires_at)
    monkeypatch.setattr(payments, "now", lambda: deadline + timedelta(minutes=6))
    sid = next(iter(provider.sessions))
    provider.sessions[sid].update(status="complete", payment_status="paid")

    def find(*_):
        provider.emit(db, sid)
        return [], True

    monkeypatch.setattr(provider, "find_sessions", find, raising=False)
    assert payments.reconcile_unknown_session(db, oid).payment_status == "paid"
    assert db.get(Product, pid).stock == 1


@pytest.mark.parametrize("foreign_id", ["999999", "malformed", "existing"])
def test_foreign_integer_order_id_without_reference_is_acknowledged(
    db, managed, provider, foreign_id
):
    oid, pid, _ = managed
    event = {
        "id": "evt_foreign",
        "type": "checkout.session.completed",
        "livemode": False,
        "data": {
            "object": {
                "metadata": {
                    "order_id": str(oid) if foreign_id == "existing" else foreign_id
                }
            }
        },
    }
    payments.handle_webhook(db, json.dumps(event).encode(), "fixture")
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).reserved_stock == 2
    assert list(db.scalars(select(PaymentEvent))) == []


def test_provider_scan_paginates_and_caps_without_false_absence(monkeypatch):
    from types import SimpleNamespace

    from app.providers.stripe import StripeProvider

    monkeypatch.setattr(
        settings, "STRIPE_API_KEY", SecretStr("rk_test_fictional_fixture")
    )
    adapter = StripeProvider()
    calls = []
    pages = [
        {"data": [{"id": "cs_test_foreign", "metadata": {}}], "has_more": True},
        {
            "data": [
                {"id": "cs_test_match", "metadata": {"payment_reference": "wanted"}}
            ],
            "has_more": False,
        },
    ]

    def list_sessions(params):
        calls.append(copy.deepcopy(params))
        page = pages.pop(0)
        return SimpleNamespace(to_dict=lambda: page)

    adapter.client = SimpleNamespace(
        v1=SimpleNamespace(
            checkout=SimpleNamespace(sessions=SimpleNamespace(list=list_sessions))
        )
    )
    result, complete = adapter.find_sessions("wanted", 100000)
    assert complete and result[0]["id"] == "cs_test_match"
    assert calls[0]["created"] == {"gte": 13540, "lte": 100000}
    assert calls[1]["starting_after"] == "cs_test_foreign"
    pages.extend(
        {"data": [{"id": f"cs_test_page_{i}", "metadata": {}}], "has_more": True}
        for i in range(10)
    )
    assert adapter.find_sessions("wanted", 100000) == ([], False)
    assert len(calls) == 12


@pytest.mark.parametrize("operation", ["replay", "absence"])
def test_changed_stripe_account_keeps_inventory_claim(
    db, managed, provider, monkeypatch, operation
):
    oid, pid, uid = managed
    if operation == "absence":
        prepare_unknown_scan(db, managed, provider, monkeypatch)
    else:
        provider.lose_response = True
        with pytest.raises(HTTPException):
            payments.start_payment(db, uid, oid)
    monkeypatch.setattr(provider, "account_id", lambda: "acct_wrong_account")
    with pytest.raises(HTTPException) as error:
        if operation == "absence":
            payments.reconcile_unknown_session(db, oid)
        else:
            payments.start_payment(db, uid, oid)
    assert error.value.status_code == 409
    assert db.get(Order, oid).payment_status == "pending"
    assert db.get(Product, pid).reserved_stock == 2


def test_missing_original_account_cannot_prove_absence(
    db, managed, provider, monkeypatch
):
    oid = prepare_unknown_scan(db, managed, provider, monkeypatch)
    order = db.get(Order, oid)
    params = json.loads(order.payment_request)
    params["metadata"].pop("stripe_account_id")
    order.payment_request = json.dumps(params)
    db.commit()
    with pytest.raises(HTTPException) as error:
        payments.reconcile_unknown_session(db, oid)
    assert error.value.status_code == 409
    assert db.get(Product, managed[1]).reserved_stock == 2


def test_known_session_skips_account_lookup(db, managed, provider, monkeypatch):
    oid, _, uid = managed
    payments.start_payment(db, uid, oid)

    def unexpected():
        pytest.fail("Known session must not require another account lookup")

    monkeypatch.setattr(provider, "account_id", unexpected)
    assert payments.reconcile_payment(db, uid, oid).payment_status == "pending"
