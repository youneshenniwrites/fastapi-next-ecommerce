from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, select, true
from sqlalchemy.orm import Session, aliased, selectinload

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductSort, ProductUpdate


def get_products(db: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    """List products ordered by id with pagination."""
    return list(
        db.scalars(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.id)
            .offset(skip)
            .limit(limit)
        ).all()
    )


def get_category_by_slug(db: Session, slug: str) -> Category | None:
    """Return the stored category for a slug, or None."""
    return db.scalar(select(Category).where(Category.slug == slug))


def require_category(db: Session, slug: str) -> Category:
    """Resolve an admin-supplied slug, rejecting ones that are not stored."""
    category = get_category_by_slug(db, slug)
    if category is None:
        raise HTTPException(422, "Unknown category")
    return category


def name_matches(query: str | None):
    """Case-insensitive name predicate, or None when the search is blank."""
    if not (query := (query or "").strip()):
        return None
    literal = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return Product.name.ilike(f"%{literal}%", escape="\\")


def list_category_counts(
    db: Session, *, query: str | None = None, in_stock: bool = False
) -> list[tuple[Category, int]]:
    """Count products per category after the same search and stock filters."""
    matched = [Product.category_id == Category.id]
    if (predicate := name_matches(query)) is not None:
        matched.append(predicate)
    if in_stock:
        matched.append(Product.stock > 0)
    return list(
        db.execute(
            select(Category, func.count(Product.id))
            .outerjoin(Product, and_(*matched))
            .group_by(Category.id)
            .order_by(Category.position, Category.id)
        ).all()
    )


def search_products(
    db: Session,
    *,
    query: str | None,
    in_stock: bool,
    sort: ProductSort,
    skip: int,
    limit: int,
    category_id: int | None = None,
) -> tuple[list[Product], int]:
    """Filter before counting and paging, with ID as the final sort key."""
    predicates = []
    if (predicate := name_matches(query)) is not None:
        predicates.append(predicate)
    if in_stock:
        predicates.append(Product.stock > 0)
    if category_id is not None:
        predicates.append(Product.category_id == category_id)

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
        .options(selectinload(product_page.category))
        .order_by(
            page.c.sort_value.desc() if descending else page.c.sort_value.asc(),
            page.c.id,
        )
    ).all()
    return [product for product, _ in rows if product is not None], rows[0].total


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """Return one product by id, or None."""
    return db.scalar(
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )


def _product_columns(obj_in: ProductCreate | ProductUpdate, *, partial: bool) -> dict:
    """Map the API image object onto the stored key and alternative text."""
    data = obj_in.model_dump(exclude={"category", "image"}, exclude_unset=partial)
    if (not partial) or ("image" in obj_in.model_fields_set):
        image = obj_in.image
        data["image_key"] = None if image is None else image.key
        data["image_alt"] = None if image is None else image.alt
    return data


def create_product(db: Session, obj_in: ProductCreate) -> Product:
    """Persist a new product in an existing category and return it."""
    category = require_category(db, obj_in.category)
    db_obj = Product(**_product_columns(obj_in, partial=False), category=category)
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
    update_data = _product_columns(obj_in, partial=True)
    if "category" in obj_in.model_fields_set:
        if obj_in.category is None:
            raise HTTPException(422, "category cannot be null")
        update_data["category"] = require_category(db, obj_in.category)
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
