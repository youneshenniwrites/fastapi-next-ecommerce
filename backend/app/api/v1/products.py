from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.rate_limit import enforce_write_limit
from app.crud.product import (
    create_product,
    delete_product,
    get_product,
    get_products,
    search_products,
    update_product,
)
from app.db.session import get_db
from app.schemas.errors import RATE_LIMITED_RESPONSE, ErrorResponse
from app.schemas.product import (
    ProductCreate,
    ProductPageRead,
    ProductRead,
    ProductSort,
    ProductUpdate,
)

router = APIRouter()
AUTH_ERRORS = {
    401: {
        "model": ErrorResponse,
        "description": "Active authenticated account required.",
    },
    403: {"model": ErrorResponse, "description": "Admin privileges required."},
}
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Product does not exist."}}
WRITE_ERRORS = {**AUTH_ERRORS, **RATE_LIMITED_RESPONSE}


@router.get(
    "/",
    response_model=List[ProductRead],
    summary="List products",
    description="Public catalog in stable ID order. Pagination limit is 1–100; skip is 0–100000.",
)
def read_products(
    skip: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_products(db=db, skip=skip, limit=limit)


@router.get(
    "/search",
    response_model=ProductPageRead,
    summary="Search and page the complete catalog",
    description=(
        "Public, server-filtered catalog page. Search matches product names, ignores "
        "case using the database locale and treats percent/underscore as literal "
        "characters. Featured order "
        "uses stable product IDs; name ordering follows the database collation "
        "after lowercasing. All sorts break ties by ID. Each page and its count "
        "share one database snapshot; catalog edits can change later requests."
    ),
)
def search_catalog(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(max_length=100, pattern=r"^[^\x00]*$")] = None,
    in_stock: Annotated[bool, Query()] = False,
    sort: Annotated[ProductSort, Query()] = "featured",
    skip: Annotated[int, Query(ge=0, le=100000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
):
    items, total = search_products(
        db, query=q, in_stock=in_stock, sort=sort, skip=skip, limit=limit
    )
    return ProductPageRead(items=items, total=total, limit=limit, skip=skip)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Read a product",
    responses=NOT_FOUND,
)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post(
    "/",
    response_model=ProductRead,
    summary="Create a product",
    description="Active admin only. GBP price has at most two decimal places; stock is a nonnegative integer. Unknown fields are rejected.",
    responses=WRITE_ERRORS,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin), Depends(enforce_write_limit)],
)
def create_new_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db=db, obj_in=product_in)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_admin), Depends(enforce_write_limit)],
    summary="Partially update a product",
    description="Active admin only. Omitted fields retain their values; only description may explicitly be null. This PUT intentionally has partial-update semantics.",
    responses={**WRITE_ERRORS, **NOT_FOUND, 409: {"model": ErrorResponse}},
)
def update_existing_product(
    product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)
):
    db_obj = get_product(db=db, product_id=product_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return update_product(db=db, db_obj=db_obj, obj_in=product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Active admin only. Returns no body on success.",
    responses={**WRITE_ERRORS, **NOT_FOUND, 409: {"model": ErrorResponse}},
    dependencies=[Depends(require_admin), Depends(enforce_write_limit)],
)
def delete_existing_product(product_id: int, db: Session = Depends(get_db)):
    db_obj = get_product(db=db, product_id=product_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Product not found")
    delete_product(db=db, db_obj=db_obj)
    return None
