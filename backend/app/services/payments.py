"""Durable payment intent, provider I/O outside locks, and atomic inventory effects."""

import json
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.order import Order, PaymentEvent
from app.models.product import Product
from app.providers.stripe import StripeProvider


class PaymentProvider(Protocol):
    def create(self, params: dict[str, Any], key: str) -> dict[str, Any]: ...
    def retrieve(self, session_id: str) -> dict[str, Any]: ...
    def expire(self, session_id: str) -> dict[str, Any]: ...
    def event(self, payload: bytes, signature: str) -> dict[str, Any]: ...


def get_provider() -> PaymentProvider:
    """Tests replace only this adapter; secrets never enter responses or log messages."""
    if not settings.STRIPE_ENABLED:
        raise HTTPException(503, "Sandbox payments are not configured")
    return StripeProvider()


def now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def lock_order(db: Session, order_id: int, user_id: int | None = None) -> Order:
    query = select(Order).where(Order.id == order_id)
    if user_id is not None:
        query = query.where(Order.user_id == user_id)
    order = db.scalar(query.with_for_update().execution_options(populate_existing=True))
    if order is None:
        raise HTTPException(404, "Order not found")
    if order.payment_status is None:
        raise HTTPException(409, "This order was not placed for sandbox payment")
    return order


def finish(db: Session, order: Order, state: str) -> None:
    """Order lock, then sorted product locks: claim disposal occurs exactly once."""
    if order.payment_status != "pending":
        return
    products = {
        p.id: p
        for p in db.scalars(
            select(Product)
            .where(Product.id.in_([line.product_id for line in order.lines]))
            .order_by(Product.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    }
    for line in order.lines:
        product = products.get(line.product_id)
        if product is None or product.reserved_stock < line.quantity:
            raise HTTPException(
                409, "Inventory reservation requires operator reconciliation"
            )
        product.reserved_stock -= line.quantity
        if state != "paid":
            product.stock += line.quantity
    if state != "paid":
        order.inventory_released_at = now()
    order.payment_status = state
    order.payment_checkout_url = None


def validate_session(order: Order, session: dict[str, Any]) -> None:
    metadata = session.get("metadata") or {}
    if (
        session.get("livemode") is not False
        or session.get("mode") != "payment"
        or session.get("currency") != "gbp"
        or session.get("amount_total") != int(order.total * 100)
        or session.get("client_reference_id") != str(order.id)
        or metadata.get("order_id") != str(order.id)
        or metadata.get("payment_reference") != order.payment_reference
        or not isinstance(session.get("id"), str)
        or not session["id"].startswith("cs_test_")
        or (order.payment_session_id and order.payment_session_id != session["id"])
        or order.payment_started_at is None
    ):
        raise HTTPException(409, "Payment session does not match the order")


def apply_session(
    db: Session,
    order: Order,
    session: dict[str, Any],
    *,
    terminal: str = "expired",
    failed: bool = False,
    verified_paid: bool = False,
) -> None:
    validate_session(order, session)
    order.payment_session_id = session["id"]
    if session.get("payment_status") == "paid":
        if order.payment_status not in ("pending", "paid"):
            raise HTTPException(
                409,
                "Payment conflicts with released inventory; operator reconciliation required",
            )
        if verified_paid:
            finish(db, order, "paid")
        else:
            order.payment_checkout_url = None
    elif session.get("status") == "expired":
        finish(db, order, terminal)
    elif failed and session.get("status") == "complete":
        finish(db, order, "failed")
    elif order.payment_status == "pending":
        # Completed delayed payments retain inventory until a definitive event.
        url = session.get("url")
        order.payment_checkout_url = (
            url
            if session.get("status") == "open"
            and isinstance(url, str)
            and url.startswith("https://checkout.stripe.com/")
            else None
        )


def provider_call(call, *args):
    """Uncertain provider outcomes retain inventory and the durable retry identity."""
    try:
        return call(*args)
    except stripe.StripeError:
        raise HTTPException(
            503, "Payment provider is unavailable; check payment status before retrying"
        ) from None


def request_params(order: Order) -> dict[str, Any]:
    origin = settings.STRIPE_CHECKOUT_ORIGIN.rstrip("/")
    return {
        "mode": "payment",
        "client_reference_id": str(order.id),
        "metadata": {
            "order_id": str(order.id),
            "payment_reference": order.payment_reference,
        },
        "success_url": f"{origin}/orders/{order.id}?payment=return",
        "cancel_url": f"{origin}/orders/{order.id}?payment=cancelled",
        "expires_at": int(aware(order.payment_expires_at).timestamp()),
        "integration_identifier": "vindor_"
        + "".join(secrets.choice(string.ascii_lowercase) for _ in range(8)),
        "line_items": [
            {
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": int(line.unit_price * 100),
                    "product_data": {"name": line.product_name},
                },
                "quantity": line.quantity,
            }
            for line in order.lines
        ],
        "adaptive_pricing": {"enabled": False},
    }


def get_session(
    db: Session, user_id: int | None, order_id: int, *, create: bool
) -> tuple[PaymentProvider, dict[str, Any] | None]:
    """Persist creation parameters once before I/O, including after lost responses.

    Stripe retains idempotency keys for at least 24 hours. After 23 hours an
    unbound attempt is held for operator reconciliation, never recreated.
    """
    provider = get_provider()
    try:
        order = lock_order(db, order_id, user_id)
        if order.payment_status != "pending":
            db.commit()
            return provider, None
        session_id = order.payment_session_id
        if not session_id and order.payment_started_at is None:
            if aware(order.payment_expires_at) <= now():
                finish(db, order, "expired")
                db.commit()
                return provider, None
            if not create:
                db.commit()
                return provider, None
            order.payment_started_at = now()
            # Give Checkout its required >=30 minute window, fixed for all retries.
            order.payment_expires_at = now() + timedelta(hours=1)
            order.payment_request = json.dumps(
                request_params(order), separators=(",", ":")
            )
        if not session_id:
            if aware(order.payment_started_at) + timedelta(hours=23) <= now():
                raise HTTPException(
                    409, "Uncertain payment creation requires operator reconciliation"
                )
            params = json.loads(order.payment_request)
            key = f"vindor-{order.payment_reference}"
        db.commit()
    except Exception:
        db.rollback()
        raise
    session = (
        provider_call(provider.retrieve, session_id)
        if session_id
        else provider_call(provider.create, params, key)
    )
    return provider, session


def start_payment(db: Session, user_id: int, order_id: int) -> dict[str, Any]:
    _, session = get_session(db, user_id, order_id, create=True)
    try:
        order = lock_order(db, order_id, user_id)
        if session:
            apply_session(db, order, session)
        db.commit()
        return {"order": order, "checkout_url": order.payment_checkout_url}
    except Exception:
        db.rollback()
        raise


def reconcile_payment(db: Session, user_id: int | None, order_id: int) -> Order:
    _, session = get_session(db, user_id, order_id, create=False)
    try:
        order = lock_order(db, order_id, user_id)
        if session:
            apply_session(db, order, session)
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise


def cancel_payment(db: Session, user_id: int, order_id: int) -> Order:
    # Unstarted intent can be cancelled under the same lock creation must acquire.
    try:
        order = lock_order(db, order_id, user_id)
        if order.payment_status == "pending" and order.payment_started_at is None:
            finish(db, order, "cancelled")
            db.commit()
            return order
        db.commit()
    except Exception:
        db.rollback()
        raise
    provider, session = get_session(db, user_id, order_id, create=False)
    if session and session.get("status") == "open":
        try:
            session = provider.expire(session["id"])
        except stripe.InvalidRequestError:
            # Checkout may have completed concurrently; obtain its authoritative state.
            session = provider_call(provider.retrieve, session["id"])
        except stripe.StripeError:
            raise HTTPException(
                503,
                "Cancellation is uncertain; inventory remains reserved. Check payment status",
            ) from None
    try:
        order = lock_order(db, order_id, user_id)
        if session:
            apply_session(db, order, session, terminal="cancelled")
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise


def handle_webhook(db: Session, payload: bytes, signature: str) -> None:
    provider = get_provider()
    try:
        event = provider.event(payload, signature)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature or payload") from None
    types = {
        "checkout.session.completed",
        "checkout.session.expired",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
    }
    if event.get("livemode") is not False:
        raise HTTPException(400, "Only sandbox webhook events are accepted")
    if event.get("type") not in types:
        return
    session = event.get("data", {}).get("object", {})
    metadata = session.get("metadata") or {}
    try:
        order_id = int(metadata.get("order_id", ""))
    except (ValueError, TypeError):
        # Other applications can share this account; no matching intent to mutate.
        return
    # A delayed failure can arrive after a newer success. Read current provider
    # state before any database lock; stale failures must not release paid stock.
    if event["type"] == "checkout.session.async_payment_failed":
        session = provider_call(provider.retrieve, session["id"])
    try:
        order = lock_order(db, order_id)
        if db.get(PaymentEvent, event["id"]) is None:
            apply_session(
                db,
                order,
                session,
                failed=event["type"] == "checkout.session.async_payment_failed",
                verified_paid=event["type"]
                in {
                    "checkout.session.completed",
                    "checkout.session.async_payment_succeeded",
                },
            )
            db.add(
                PaymentEvent(
                    id=event["id"], order_id=order.id, event_type=event["type"]
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
