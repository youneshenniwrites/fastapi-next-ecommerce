"""Loopback-only sandbox provider fixture; never imported by the deployed API."""

import copy
import hashlib
import hmac
import json
import threading
import time
from typing import Literal
from uuid import uuid4

import httpx
import stripe
from app.core.settings import settings
from app.db.session import SessionLocal
from app.models.order import Order
from app.models.product import Product
from app.providers.stripe import StripeProvider
from app.services import payments
from browser_api import app
from fastapi import HTTPException
from pydantic import BaseModel


class FixtureProvider:
    """Simulate provider I/O while retaining real signed-event verification."""

    def __init__(self):
        self.lock = threading.Lock()
        self.sessions = {}
        self.keys = {}
        self.calls = {}
        self.faults = {}
        self.signer = StripeProvider()

    def account_id(self):
        return "acct_browser_fixture"

    def create(self, params, key):
        with self.lock:
            oid = int(params["client_reference_id"])
            self.calls[oid] = self.calls.get(oid, 0) + 1
            if key not in self.keys:
                sid = "cs_test_" + params["metadata"]["payment_reference"].replace(
                    "-", ""
                )
                self.keys[key] = sid
                self.sessions[sid] = {
                    "id": sid,
                    "object": "checkout.session",
                    "livemode": False,
                    "mode": "payment",
                    "currency": "gbp",
                    "amount_total": sum(
                        line["price_data"]["unit_amount"] * line["quantity"]
                        for line in params["line_items"]
                    ),
                    "client_reference_id": str(oid),
                    "metadata": copy.deepcopy(params["metadata"]),
                    "status": "open",
                    "payment_status": "unpaid",
                    "url": f"https://checkout.stripe.com/c/pay/{sid}",
                }
            if self.faults.get(oid, {}).pop("lose_create_response", False):
                raise stripe.APIConnectionError(
                    "Disposable fixture: lost creation response"
                )
            return copy.deepcopy(self.sessions[self.keys[key]])

    def retrieve(self, session_id):
        with self.lock:
            return copy.deepcopy(self.sessions[session_id])

    def expire(self, session_id):
        with self.lock:
            session = self.sessions[session_id]
            if session["status"] != "open":
                raise stripe.InvalidRequestError(
                    "Disposable fixture: session not open", "id"
                )
            session["status"] = "expired"
            oid = int(session["client_reference_id"])
            if self.faults.get(oid, {}).pop("lose_expire_response", False):
                raise stripe.APIConnectionError(
                    "Disposable fixture: lost expiry response"
                )
            return copy.deepcopy(session)

    def event(self, payload, signature):
        return self.signer.event(payload, signature)


provider = FixtureProvider()
payments.get_provider = lambda: provider


class EventFixture(BaseModel):
    order_id: int
    state: Literal["paid", "expired", "failed", "processing"]
    event_id: str | None = None


class FaultFixture(BaseModel):
    order_id: int
    lose_create_response: bool = False
    lose_expire_response: bool = False


@app.post("/__test/payment-fault")
def payment_fault(body: FaultFixture):
    with provider.lock:
        provider.faults[body.order_id] = body.model_dump(exclude={"order_id"})
    return {"ok": True}


@app.post("/__test/payment-event")
async def payment_event(body: EventFixture):
    with provider.lock:
        session = next(
            (
                session
                for session in provider.sessions.values()
                if session["client_reference_id"] == str(body.order_id)
            ),
            None,
        )
        if session is None:
            raise HTTPException(404, "Fixture session not found")
        session["status"] = "expired" if body.state == "expired" else "complete"
        session["payment_status"] = "paid" if body.state == "paid" else "unpaid"
        types = {
            "paid": "checkout.session.completed",
            "processing": "checkout.session.completed",
            "expired": "checkout.session.expired",
            "failed": "checkout.session.async_payment_failed",
        }
        event = {
            "id": body.event_id or "evt_" + uuid4().hex,
            "object": "event",
            "livemode": False,
            "type": types[body.state],
            "data": {"object": copy.deepcopy(session)},
        }
    payload = json.dumps(event).encode()
    timestamp = int(time.time())
    digest = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.get_secret_value().encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://fixture"
    ) as client:
        response = await client.post(
            "/api/v1/payments/webhook",
            content=payload,
            headers={"Stripe-Signature": f"t={timestamp},v1={digest}"},
        )
    if response.status_code != 200:
        raise HTTPException(
            response.status_code,
            response.json().get("detail", "Fixture event rejected"),
        )
    return {"ok": True, "event_id": event["id"]}


@app.get("/__test/payment/{order_id}")
def inspect_payment(order_id: int):
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if order is None:
            raise HTTPException(404, "Fixture order not found")
        products = [db.get(Product, line.product_id) for line in order.lines]
        with provider.lock:
            count = sum(
                session["client_reference_id"] == str(order_id)
                for session in provider.sessions.values()
            )
            calls = provider.calls.get(order_id, 0)
        return {
            "session_count": count,
            "create_calls": calls,
            "payment_status": order.payment_status,
            "products": [
                {
                    "id": product.id,
                    "stock": product.stock,
                    "reserved_stock": product.reserved_stock,
                }
                for product in products
                if product
            ],
        }
