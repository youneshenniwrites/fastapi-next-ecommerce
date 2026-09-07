from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.crud.product import (
    create_product,
    delete_product,
    get_product,
    get_products,
    update_product,
)
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter()


@router.get("/", response_model=List[ProductRead])
def read_products(
    skip: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_products(db=db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_new_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db=db, obj_in=product_in)


@router.put(
    "/{product_id}", response_model=ProductRead, dependencies=[Depends(require_admin)]
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
    dependencies=[Depends(require_admin)],
)
def delete_existing_product(product_id: int, db: Session = Depends(get_db)):
    db_obj = get_product(db=db, product_id=product_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Product not found")
    delete_product(db=db, db_obj=db_obj)
    return None
