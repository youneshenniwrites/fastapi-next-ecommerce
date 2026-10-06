from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud.product import list_category_counts
from app.db.session import get_db
from app.schemas.product import CategoryCount

router = APIRouter()


@router.get(
    "/",
    response_model=list[CategoryCount],
    summary="List categories",
    description=(
        "Public workspace categories in display order. Each count uses the same "
        "name search and stock filter as the catalog, and is not limited to one "
        "category. All is not a category; omit the catalog category filter to "
        "browse everything. Uncategorized is the stored fallback."
    ),
)
def read_categories(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(max_length=100, pattern=r"^[^\x00]*$")] = None,
    in_stock: Annotated[bool, Query()] = False,
):
    return [
        CategoryCount(slug=category.slug, name=category.name, count=count)
        for category, count in list_category_counts(db, query=q, in_stock=in_stock)
    ]
