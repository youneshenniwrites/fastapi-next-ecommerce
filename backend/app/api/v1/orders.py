from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import enforce_write_limit
from app.crud.order import list_owned, read_owned
from app.db.session import get_db
from app.models.user import User
from app.schemas.errors import RATE_LIMITED_RESPONSE, ErrorResponse
from app.schemas.order import DraftCreate, OrderRead
from app.services.orders import create_draft


def private_response(response: Response) -> None:
    """Keep successful customer order responses out of shared caches."""
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
    dependencies=[Depends(private_response)],
    responses={401: {"model": ErrorResponse}},
)
Database = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(get_current_user)]


@router.post(
    "/drafts",
    response_model=OrderRead,
    status_code=201,
    dependencies=[Depends(enforce_write_limit)],
    responses={404: {"model": ErrorResponse}, **RATE_LIMITED_RESPONSE},
)
def post_draft(payload: DraftCreate, db: Database, user: Customer):
    """Save a GBP quotation only: no stock reservation, cart change or placement.

    Repeating creation produces a new draft; placement idempotency is a later slice.
    Prices are copied from the backend and must be revalidated before purchase.
    """
    return create_draft(db, user.id, payload)


@router.get("/", response_model=list[OrderRead])
def get_orders(
    db: Database,
    user: Customer,
    after_id: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List your saved orders by ascending ID; use the last ID as after_id."""
    return list_owned(db, user.id, after_id, limit)


@router.get(
    "/{order_id}", response_model=OrderRead, responses={404: {"model": ErrorResponse}}
)
def get_order(
    order_id: Annotated[int, Path(ge=1, le=2147483647)], db: Database, user: Customer
):
    """Return your snapshot; other customers' IDs are indistinguishable from missing."""
    order = read_owned(db, user.id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
