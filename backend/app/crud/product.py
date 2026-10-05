from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select, true
from sqlalchemy.orm import Session, aliased

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductSort, ProductUpdate


def get_products(db: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    """List products ordered by id with pagination."""
    return list(
        db.scalars(select(Product).order_by(Product.id).offset(skip).limit(limit)).all()
    )


def search_products(
    db: Session,
    *,
    query: str | None,
    in_stock: bool,
    sort: ProductSort,
    skip: int,
    limit: int,
) -> tuple[list[Product], int]:
    """Filter before counting and paging, with ID as the final sort key."""
    predicates = []
    if query := (query or "").strip():
        # Escape SQL LIKE wildcards so searches for '%' and '_' are literal.
        literal = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        predicates.append(Product.name.ilike(f"%{literal}%", escape="\\"))
    if in_stock:
        predicates.append(Product.stock > 0)

    sort_value = {
        "featured": Product.id,
        "name": func.lower(Product.name),
        "price-asc": Product.price,
        "price-desc": Product.price,
    }[sort]
    descending = sort == "price-desc"
    page = (
        select(Product, sort_value.label("sort_value"))
        .where(*predicates)
        .order_by(sort_value.desc() if descending else sort_value.asc(), Product.id)
        .offset(skip)
        .limit(limit)
        .subquery()
    )
    count = (
        select(func.count().label("total"))
        .select_from(Product)
        .where(*predicates)
        .subquery()
    )
    product_page = aliased(Product, page)
    # One statement gives count and rows the same snapshot. The outer join keeps
    # the count available even when an empty/out-of-range page has no products.
    rows = db.execute(
        select(product_page, count.c.total)
        .select_from(count)
        .outerjoin(product_page, true())
        .order_by(
            page.c.sort_value.desc() if descending else page.c.sort_value.asc(),
            page.c.id,
        )
    ).all()
    return [product for product, _ in rows if product is not None], rows[0].total


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
