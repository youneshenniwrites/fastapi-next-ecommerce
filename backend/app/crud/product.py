from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(db: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    """List products ordered by id with pagination."""
    return list(
        db.scalars(select(Product).order_by(Product.id).offset(skip).limit(limit)).all()
    )


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Return one product by id, or None."""
    return db.scalar(select(Product).where(Product.id == product_id))


def create_product(db: Session, obj_in: ProductCreate) -> Product:
    """Persist a new product and return it."""
    db_obj = Product(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_product(db: Session, db_obj: Product, obj_in: ProductUpdate) -> Product:
    """Apply a partial update to a product."""
    db_obj = db.scalar(
        select(Product)
        .where(Product.id == db_obj.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if db_obj is None:
        raise HTTPException(404, "Product not found")
    update_data = obj_in.model_dump(exclude_unset=True)
    if update_data.get("stock", db_obj.stock) + db_obj.reserved_stock > 2147483647:
        raise HTTPException(409, "Stock must leave room for reserved inventory")
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_product(db: Session, db_obj: Product) -> None:
    """Delete a product."""
    db_obj = db.scalar(
        select(Product)
        .where(Product.id == db_obj.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if db_obj is None:
        raise HTTPException(404, "Product not found")
    if db_obj.reserved_stock:
        raise HTTPException(409, "Product has active payment reservations")
    db.delete(db_obj)
    db.commit()
