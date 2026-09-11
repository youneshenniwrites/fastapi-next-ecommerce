from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.cart import read_cart, remove_line, set_quantity
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartQuantity, CartRead
from app.schemas.errors import ErrorResponse

router = APIRouter(responses={401: {"model": ErrorResponse}})
ProductId = Annotated[int, Path(ge=1, le=2147483647)]


def private_response(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


router.dependencies.append(Depends(private_response))


@router.get(
    "/",
    response_model=CartRead,
    summary="Read your saved cart",
    description="Current GBP prices and availability; stock is not reserved. Saved shortages remain visible. Deleted products are removed from carts.",
)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return read_cart(db, user.id)


@router.put(
    "/items/{product_id}",
    response_model=CartRead,
    summary="Set an absolute cart quantity",
    description="Idempotent quantity 1–99. New lines/increases require stock; reductions and unchanged quantities remain allowed during shortages. Concurrent writes serialize per customer: last serialized write wins. Prices and ownership cannot be supplied.",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def put_cart_item(
    product_id: ProductId,
    payload: CartQuantity,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return set_quantity(db, user.id, product_id, payload.quantity)


@router.delete(
    "/items/{product_id}",
    status_code=204,
    summary="Remove a product from your cart",
    description="Idempotent: missing lines also return 204. Only your own line can be removed.",
)
def delete_cart_item(
    product_id: ProductId,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    remove_line(db, user.id, product_id)
