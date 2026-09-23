"""Public signed Stripe event ingress; no customer login dependency."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.services.payments import handle_webhook

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post(
    "/webhook",
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    stripe_signature: Annotated[str, Header(max_length=2048)] = "",
) -> dict[str, bool]:
    """Verify the exact raw signed body and commit deduplication with its effects."""
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > 262144:
            raise HTTPException(413, "Webhook payload too large")
    await run_in_threadpool(handle_webhook, db, bytes(payload), stripe_signature)
    return {"received": True}
