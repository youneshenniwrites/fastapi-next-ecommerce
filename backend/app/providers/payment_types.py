"""The Stripe fields consumed by the sandbox payment service.

These are transport types, not evidence of payment or ownership. The service
still validates session binding and signed event state before changing inventory.
Absent and nullable session fields remain distinct from validated local state.
"""

from typing import NotRequired, Protocol, TypedDict

from stripe.params.checkout import SessionCreateParams


class PaymentSession(TypedDict, total=False):
    id: str
    livemode: bool
    mode: str
    currency: str | None
    amount_total: int | None
    client_reference_id: str | None
    metadata: dict[str, str] | None
    payment_status: str
    status: str | None
    url: str | None


class SessionPage(TypedDict):
    data: list[PaymentSession]
    has_more: bool


class EventData(TypedDict):
    object: NotRequired[PaymentSession]


class PaymentWebhookEvent(TypedDict):
    id: str
    type: str
    livemode: bool
    data: NotRequired[EventData]
    created: NotRequired[int]


class PaymentProvider(Protocol):
    def account_id(self) -> str: ...
    def create(self, params: SessionCreateParams, key: str) -> PaymentSession: ...
    def retrieve(self, session_id: str) -> PaymentSession: ...
    def expire(self, session_id: str) -> PaymentSession: ...
    def event(self, payload: bytes, signature: str) -> PaymentWebhookEvent: ...
    def find_sessions(
        self, reference: str, expires_at: int
    ) -> tuple[list[PaymentSession], bool]: ...
