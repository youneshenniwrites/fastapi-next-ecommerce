"""Independent PostgreSQL acceptance for payment races and provider uncertainty."""

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier, RLock

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.crud.product import delete_product, update_product
from app.models.order import Order, PaymentEvent
from app.models.product import Product
from app.schemas.product import ProductUpdate
from app.services import payments
from app.tests.test_payments import managed as managed
from app.tests.test_payments import provider as provider


@pytest.fixture(autouse=True)
def postgres_only(db):
    """SQLite cannot establish these row-lock guarantees."""
    if db.bind.dialect.name != "postgresql":
        pytest.skip("Real PostgreSQL locks required")


def parallel(db, actions):
    """Give contenders independent connections and synchronize entry without sleeps."""
    engine = db.bind
    db.rollback()
    barrier = Barrier(len(actions))

    def run(action):
        with Session(engine) as session:
            barrier.wait(timeout=10)
            return action(session)

    with ThreadPoolExecutor(max_workers=len(actions)) as pool:
        futures = [pool.submit(run, action) for action in actions]
        results = [future.result(timeout=20) for future in futures]
    db.expire_all()
    return results


def payload(provider, sid, kind, eid, **changes):
    """Snapshot the webhook independently from subsequent provider state."""
    snapshot = provider.retrieve(sid)
    snapshot.update(changes)
    return json.dumps(
        dict(id=eid, type=kind, livemode=False, data={"object": snapshot})
    ).encode()


def inventory(db, oid, pid, state, stock, reserved):
    db.expire_all()
    order, product = db.get(Order, oid), db.get(Product, pid)
    assert order.payment_status == state
    assert (product.stock, product.reserved_stock) == (stock, reserved)
    assert bool(order.inventory_released_at) == (
        state in {"cancelled", "expired", "failed"}
    )
    assert order.total == Decimal("4.70")


def test_simultaneous_creation_shares_durable_identity(
    db, managed, provider, monkeypatch
):
    """Provider I/O sees committed intent and holds no DB lock; retries share one key."""
    oid, pid, uid = managed
    engine, arrive, guard = db.bind, Barrier(2), RLock()
    original = provider.create

    def create(params, key):
        with Session(engine) as observer:
            observer.execute(text("SET LOCAL lock_timeout = '1s'"))
            order = observer.scalar(
                select(Order).where(Order.id == oid).with_for_update()
            )
            assert order.payment_started_at is not None
            assert json.loads(order.payment_request) == params
        arrive.wait(timeout=10)
        with guard:
            return original(params, key)

    monkeypatch.setattr(provider, "create", create)
    results = parallel(
        db,
        [lambda session: payments.start_payment(session, uid, oid)["checkout_url"]] * 2,
    )
    assert results[0] == results[1]
    assert len(provider.sessions) == 1
    assert provider.requests[0] == provider.requests[1]
    inventory(db, oid, pid, "pending", 1, 2)


def test_provider_success_database_failure_preserves_retry_identity(
    db, managed, provider, monkeypatch
):
    """A failed local bind cannot duplicate the already-created external session."""
    oid, pid, uid = managed
    original = db.commit

    def commit():
        # Fail the binding transaction, not an incidental setup/account commit.
        # The provider has already created this session, while its local binding
        # is still uncommitted and must roll back after the injected failure.
        if (
            provider.sessions
            and db.get(Order, oid).payment_session_id in provider.sessions
        ):
            db.flush()
            raise RuntimeError("disposable binding failure")
        original()

    monkeypatch.setattr(db, "commit", commit)
    with pytest.raises(RuntimeError, match="binding"):
        payments.start_payment(db, uid, oid)
    monkeypatch.setattr(db, "commit", original)
    assert db.get(Order, oid).payment_session_id is None
    assert len(provider.sessions) == 1
    assert payments.start_payment(db, uid, oid)["checkout_url"]
    assert len(provider.sessions) == 1
    assert provider.requests[0] == provider.requests[1]
    inventory(db, oid, pid, "pending", 1, 2)


def test_duplicate_paid_webhooks_race_reconciliation(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    event = payload(provider, sid, "checkout.session.completed", "evt_duplicate_paid")
    parallel(
        db,
        [lambda session: payments.handle_webhook(session, event, "fixture")] * 2
        + [lambda session: payments.reconcile_payment(session, uid, oid)],
    )
    inventory(db, oid, pid, "paid", 1, 0)
    assert len(list(db.scalars(select(PaymentEvent)))) == 1


@pytest.mark.parametrize(
    "kind", ["checkout.session.expired", "checkout.session.async_payment_failed"]
)
def test_duplicate_terminal_webhooks_release_once(db, managed, provider, kind):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    failed = kind.endswith("failed")
    provider.sessions[sid]["status"] = "complete" if failed else "expired"
    event = payload(provider, sid, kind, "evt_duplicate_terminal")
    parallel(
        db, [lambda session: payments.handle_webhook(session, event, "fixture")] * 2
    )
    inventory(db, oid, pid, "failed" if failed else "expired", 3, 0)
    assert len(list(db.scalars(select(PaymentEvent)))) == 1


def test_cancel_expiry_and_reconcile_race(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid]["status"] = "expired"
    event = payload(provider, sid, "checkout.session.expired", "evt_cancel_race")
    parallel(
        db,
        [
            lambda session: payments.cancel_payment(session, uid, oid),
            lambda session: payments.reconcile_payment(session, uid, oid),
            lambda session: payments.handle_webhook(session, event, "fixture"),
        ],
    )
    state = db.get(Order, oid).payment_status
    assert state in {"cancelled", "expired"}
    inventory(db, oid, pid, state, 3, 0)
    assert len(list(db.scalars(select(PaymentEvent)))) == 1


def test_checkout_wins_cancellation_keeps_claim_until_signed_success(
    db, managed, provider, monkeypatch
):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    original = provider.expire

    def expire(session_id):
        provider.sessions[session_id].update(status="complete", payment_status="paid")
        return original(session_id)

    monkeypatch.setattr(provider, "expire", expire)
    assert payments.cancel_payment(db, uid, oid).payment_status == "pending"
    inventory(db, oid, pid, "pending", 1, 2)
    event = payload(provider, sid, "checkout.session.completed", "evt_cancel_lost")
    payments.handle_webhook(db, event, "fixture")
    inventory(db, oid, pid, "paid", 1, 0)


def test_success_stale_failure_and_cancel_race(db, managed, provider):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid].update(status="complete", payment_status="paid")
    success = payload(
        provider, sid, "checkout.session.async_payment_succeeded", "evt_success"
    )
    failure = payload(
        provider,
        sid,
        "checkout.session.async_payment_failed",
        "evt_failure",
        payment_status="unpaid",
    )
    parallel(
        db,
        [
            lambda session: payments.handle_webhook(session, success, "fixture"),
            lambda session: payments.handle_webhook(session, failure, "fixture"),
            lambda session: payments.cancel_payment(session, uid, oid),
        ],
    )
    inventory(db, oid, pid, "paid", 1, 0)
    assert len(list(db.scalars(select(PaymentEvent)))) == 2


def test_admin_overflow_racing_release_preserves_inventory(db, managed, provider):
    oid, pid, uid = managed

    def edit(session):
        try:
            update_product(
                session, session.get(Product, pid), ProductUpdate(stock=2147483647)
            )
            return "updated"
        except HTTPException as error:
            session.rollback()
            assert error.status_code == 409
            return "protected"

    results = parallel(
        db, [edit, lambda session: payments.cancel_payment(session, uid, oid)]
    )
    product = db.get(Product, pid)
    assert product.reserved_stock == 0
    assert product.stock == (2147483647 if results[0] == "updated" else 3)
    delete_product(db, product)
    assert db.get(Order, oid).total == Decimal("4.70")


def test_cancellation_wins_while_first_creation_response_is_delayed(
    db, managed, provider, monkeypatch
):
    """An in-flight start cannot resurrect the Checkout URL after cancellation."""
    from threading import Event

    oid, pid, uid = managed
    created, cancelled, guard = Event(), Event(), RLock()
    original = provider.create
    calls = 0

    def create(params, key):
        nonlocal calls
        with guard:
            calls += 1
            first = calls == 1
            result = original(params, key)
        if first:
            created.set()
            assert cancelled.wait(timeout=10)
        return result

    def cancel(session):
        assert created.wait(timeout=10)
        result = payments.cancel_payment(session, uid, oid).payment_status
        cancelled.set()
        return result

    monkeypatch.setattr(provider, "create", create)
    results = parallel(
        db,
        [
            lambda session: payments.start_payment(session, uid, oid)["checkout_url"],
            cancel,
        ],
    )
    assert results == [None, "cancelled"]
    assert len(provider.sessions) == 1
    assert next(iter(provider.sessions.values()))["status"] == "expired"
    inventory(db, oid, pid, "cancelled", 3, 0)


def test_lost_expiry_response_retains_claim_until_authoritative_retry(
    db, managed, provider, monkeypatch
):
    import stripe

    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    original = provider.expire

    def expire(sid):
        original(sid)
        raise stripe.APIConnectionError("disposable expiry response loss")

    monkeypatch.setattr(provider, "expire", expire)
    with pytest.raises(HTTPException) as error:
        payments.cancel_payment(db, uid, oid)
    assert error.value.status_code == 503
    inventory(db, oid, pid, "pending", 1, 2)
    assert payments.cancel_payment(db, uid, oid).payment_status == "cancelled"
    inventory(db, oid, pid, "cancelled", 3, 0)


def test_webhook_commit_failure_rolls_back_event_and_inventory_together(
    db, managed, provider, monkeypatch
):
    oid, pid, uid = managed
    payments.start_payment(db, uid, oid)
    sid = db.get(Order, oid).payment_session_id
    provider.sessions[sid]["status"] = "expired"
    event = payload(provider, sid, "checkout.session.expired", "evt_db_retry")
    original = db.commit

    def fail():
        db.flush()
        raise RuntimeError("disposable webhook commit failure")

    monkeypatch.setattr(db, "commit", fail)
    with pytest.raises(RuntimeError, match="webhook"):
        payments.handle_webhook(db, event, "fixture")
    monkeypatch.setattr(db, "commit", original)
    inventory(db, oid, pid, "pending", 1, 2)
    assert db.get(PaymentEvent, "evt_db_retry") is None
    payments.handle_webhook(db, event, "fixture")
    inventory(db, oid, pid, "expired", 3, 0)
    assert db.get(PaymentEvent, "evt_db_retry") is not None


@pytest.mark.parametrize("action", ["payment", "cancel", "reconcile"])
def test_payment_mutations_reject_other_and_disabled_customers(
    client, db, managed, token, action
):
    from app.core.security import create_access_token
    from app.models.user import User

    oid, pid, uid = managed
    stranger = User(
        email="payment-stranger@example.test",
        hashed_password="unused",
        is_active=True,
        is_superuser=True,
    )
    db.add(stranger)
    db.commit()
    response = client.post(
        f"/api/v1/orders/{oid}/{action}",
        headers={"Authorization": f"Bearer {create_access_token(stranger.id)}"},
    )
    assert response.status_code == 404
    db.get(User, uid).is_active = False
    db.commit()
    response = client.post(
        f"/api/v1/orders/{oid}/{action}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    inventory(db, oid, pid, "pending", 1, 2)
