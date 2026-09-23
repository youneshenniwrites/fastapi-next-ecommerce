"""Stripe-only I/O; callers must commit and release database locks first."""

from typing import Any

import stripe

from app.core.settings import settings


class StripeProvider:
    def __init__(self) -> None:
        self.client = stripe.StripeClient(
            settings.STRIPE_API_KEY.get_secret_value(),
            stripe_version="2026-08-26.dahlia",
            max_network_retries=1,
        )

    def create(self, params: dict[str, Any], key: str) -> dict[str, Any]:
        return self.client.v1.checkout.sessions.create(
            params, options={"idempotency_key": key}
        ).to_dict()

    def retrieve(self, session_id: str) -> dict[str, Any]:
        return self.client.v1.checkout.sessions.retrieve(session_id).to_dict()

    def expire(self, session_id: str) -> dict[str, Any]:
        return self.client.v1.checkout.sessions.expire(session_id).to_dict()

    def event(self, payload: bytes, signature: str) -> dict[str, Any]:
        return stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        ).to_dict()
