"""Apply the reviewed catalog once, without repairing or resetting a shop.

The caller owns the transaction. This function flushes and does not commit.
A refusal or a database error leaves the caller to roll every change back.
"""

from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.catalog_manifest import WORKSPACE_CATALOG, CatalogItem, validate_manifest
from app.models.category import Category
from app.models.demo_catalog import DemoCatalog
from app.models.imported_catalog import ImportedCatalogItem
from app.models.product import Product


def import_catalog(db: Session, items=None, *, photo_root: Path | None = None) -> int:
    """Insert missing reviewed products and return how many new rows were added.

    An existing product is adopted only when its name is the unique original
    demo name and it has no different catalog key. Adoption stores the key and
    leaves the name, price, stock, photo, facts and id unchanged. A later run
    does not replenish stock, overwrite edits, or recreate a deleted import.
    """
    raw = WORKSPACE_CATALOG if items is None else items
    try:
        catalog = validate_manifest(raw, photo_root=photo_root)
    except ValidationError as exc:
        raise ValueError("Catalog manifest is invalid.") from exc
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("LOCK TABLE products IN SHARE ROW EXCLUSIVE MODE"))
        db.execute(
            text("LOCK TABLE imported_catalog_items IN SHARE ROW EXCLUSIVE MODE")
        )
    categories = {category.slug: category for category in db.scalars(select(Category))}
    missing = {item.category for item in catalog} - set(categories)
    if missing:
        raise ValueError(
            "Catalog categories are missing; apply migrations before importing."
        )
    products = list(db.scalars(select(Product)))
    if not products and _seeded_edition_remains(db):
        raise ValueError(
            "The twelve-product edition remains after its products were deleted; "
            "import refused."
        )
    by_id = {product.id: product for product in products}
    by_key = {
        product.catalog_key: product
        for product in products
        if product.catalog_key is not None
    }
    by_name: dict[str, list[Product]] = {}
    for product in products:
        by_name.setdefault(product.name, []).append(product)
    ledgers = {row.catalog_key: row for row in db.scalars(select(ImportedCatalogItem))}
    planned, errors = _plan(catalog, products, by_id, by_key, by_name, ledgers)
    if errors:
        raise ValueError("; ".join(errors))
    return _apply(db, planned, categories)


def _seeded_edition_remains(db: Session) -> bool:
    """The edition marker is the guard against recreating a deleted demo."""
    from app.bootstrap import CATALOG_EDITION

    return db.get(DemoCatalog, CATALOG_EDITION) is not None


def _plan(catalog, products, by_id, by_key, by_name, ledgers):
    planned = []
    errors = []
    for item in catalog:
        ledger = ledgers.get(item.key)
        keyed = by_key.get(item.key)
        if ledger is not None and ledger.product_id is None:
            if keyed is not None:
                errors.append(
                    f"Retired catalog key {item.key!r} is still assigned to a product."
                )
            else:
                planned.append(("skip", item, None))
            continue
        if ledger is not None and ledger.product_id is not None:
            product = by_id.get(ledger.product_id)
            if product is None or product.catalog_key != item.key:
                errors.append(
                    f"Catalog key {item.key!r} does not match its import ledger."
                )
            elif keyed is not None and keyed.id != product.id:
                errors.append(
                    f"Catalog key {item.key!r} is already stored on a different product."
                )
            else:
                planned.append(("skip", item, product))
            continue
        if keyed is not None:
            planned.append(("repair", item, keyed))
            continue
        if item.legacy_name is not None:
            matches = by_name.get(item.legacy_name, [])
            if len(matches) > 1:
                errors.append(
                    f"Legacy name {item.legacy_name!r} matches more than one product."
                )
                continue
            if len(matches) == 0 and products:
                errors.append(
                    f"Legacy name {item.legacy_name!r} is missing while other products exist."
                )
                continue
            if len(matches) == 1:
                product = matches[0]
                if product.catalog_key not in (None, item.key):
                    errors.append(
                        f"Legacy product {item.legacy_name!r} already has catalog key "
                        f"{product.catalog_key!r}."
                    )
                else:
                    planned.append(("adopt", item, product))
                continue
        planned.append(("insert", item, None))
    return planned, errors


def _apply(db: Session, planned, categories: dict[str, Category]) -> int:
    created = 0
    fresh: list[Product] = []
    for action, item, product in planned:
        if action == "skip":
            continue
        if action == "repair":
            db.add(ImportedCatalogItem(catalog_key=item.key, product_id=product.id))
            continue
        if action == "adopt":
            product.catalog_key = item.key
            db.add(ImportedCatalogItem(catalog_key=item.key, product_id=product.id))
            continue
        fresh.append(_new_product(item, categories))
        created += 1
    for product in fresh:
        db.add(product)
    db.flush()
    for product in fresh:
        db.add(
            ImportedCatalogItem(catalog_key=product.catalog_key, product_id=product.id)
        )
    db.flush()
    return created


def _new_product(item: CatalogItem, categories: dict[str, Category]) -> Product:
    return Product(
        name=item.name,
        description=item.description,
        price=item.price,
        currency="GBP",
        stock=item.stock,
        catalog_key=item.key,
        image_key=item.image_key,
        image_alt=item.image_alt,
        material=item.material,
        width_mm=item.width_mm,
        depth_mm=item.depth_mm,
        height_mm=item.height_mm,
        category=categories[item.category],
    )
