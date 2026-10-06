from fastapi import APIRouter, Depends
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
        "Public workspace categories in display order, each with its product count. "
        "All is not a category; omit the catalog category filter to browse everything. "
        "Uncategorized is the stored fallback for products without a named category."
    ),
)
def read_categories(db: Session = Depends(get_db)):
    return [
        CategoryCount(slug=category.slug, name=category.name, count=count)
        for category, count in list_category_counts(db)
    ]
