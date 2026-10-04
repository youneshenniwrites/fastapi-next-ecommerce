"""Stripe-only I/O; callers must commit and release database locks first."""

from typing import cast

import stripe
from stripe.params.checkout import SessionCreateParams, SessionListParams

from app.core.settings import settings
from app.providers.payment_types import PaymentSession, PaymentWebhookEvent, SessionPage


class StripeProvider:
    def __init__(self) -> None:
        self.client = stripe.StripeClient(
            settings.STRIPE_API_KEY.get_secret_value(),
            stripe_version="2026-08-26.dahlia",
            max_network_retries=1,
        )

    def account_id(self) -> str:
        """Resolve the account attached to this immutable client credential."""
        return self.client.v1.accounts.retrieve_current().id

    def create(self, params: SessionCreateParams, key: str) -> PaymentSession:
        # SDK serialization erases its resource field types. Keep that boundary
        # here; this cast does not replace the service's payment validation.
        return cast(
            PaymentSession,
            self.client.v1.checkout.sessions.create(
                params, options={"idempotency_key": key}
            ).to_dict(),
        )

    def retrieve(self, session_id: str) -> PaymentSession:
        return cast(
            PaymentSession,
            self.client.v1.checkout.sessions.retrieve(session_id).to_dict(),
        )

    def expire(self, session_id: str) -> PaymentSession:
        return cast(
            PaymentSession,
            self.client.v1.checkout.sessions.expire(session_id).to_dict(),
        )

    def find_sessions(
        self, reference: str, expires_at: int
    ) -> tuple[list[PaymentSession], bool]:
        """Scan at most 1,000 sessions; incomplete scans never establish absence.

        A session must be created within 24 hours before its fixed expires_at.
        This provider-enforced bound avoids depending on application clock skew.
        """
        params: SessionListParams = {
            "limit": 100,
            "created": {"gte": expires_at - 86460, "lte": expires_at},
        }
        matches: list[PaymentSession] = []
        for _ in range(10):
            page = cast(
                SessionPage, self.client.v1.checkout.sessions.list(params).to_dict()
            )
            data = page["data"]
            matches.extend(
                session
                for session in data
                if (session.get("metadata") or {}).get("payment_reference") == reference
            )
            if not page["has_more"]:
                return matches, True
            if not data:
                return matches, False
            params["starting_after"] = data[-1]["id"]
        return matches, False

    def event(self, payload: bytes, signature: str) -> PaymentWebhookEvent:
        return cast(
            PaymentWebhookEvent,
            stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
            ).to_dict(),
        )
