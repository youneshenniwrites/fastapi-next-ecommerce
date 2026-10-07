"""Add a deterministic multi-page fixture to a disposable browser-test database."""

from decimal import Decimal

from app.catalog_taxonomy import UNCATEGORIZED_SLUG
from app.crud.product import require_category
from app.db.session import SessionLocal
from app.models.product import Product
from app.schemas.product import ProductCreate

SPECIAL = {
    3: "100% Wool Tray",
    5: "Under_score Stand",
}


def fixture_products():
    for number in range(1, 49):
        name = SPECIAL.get(
            number,
            f"Lumen Lamp {number:02d}" if number % 4 == 0 else f"Studio Item {number:02d}",
        )
        # Repeated prices make price ordering rely on the API's stable ID tie-break.
        price = Decimal(10 + (number % 6) * 5)
        category = "lighting" if name.startswith("Lumen Lamp") else UNCATEGORIZED_SLUG
        yield ProductCreate(
            name=name,
            description=f"Fixture object {number:02d} for pagination checks.",
            price=f"{price:.2f}",
            stock=0 if number % 6 == 0 else 5,
            currency="GBP",
            category=category,
        )


if __name__ == "__main__":
    with SessionLocal() as db:
        for data in fixture_products():
            category = require_category(db, data.category)
            db.add(
                Product(
                    **data.model_dump(exclude={"category", "image"}),
                    category=category,
                )
            )
        db.commit()
