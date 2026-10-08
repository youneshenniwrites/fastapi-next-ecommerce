import os
import threading
import time
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import bootstrap
from app.catalog_import import import_catalog
from app.catalog_manifest import (
    IMAGE_ALTS,
    PHOTO_ROOT,
    WORKSPACE_CATALOG,
    validate_manifest,
)
from app.catalog_media import PRODUCT_MEDIA
from app.catalog_taxonomy import CATEGORIES, PRODUCT_CATEGORIES
from app.core.security import create_access_token, get_password_hash
from app.models.cart import CartLine
from app.models.category import Category
from app.models.demo_catalog import DemoCatalog
from app.models.imported_catalog import ImportedCatalogItem
from app.models.order import Order, OrderLine
from app.models.product import Product
from app.models.user import User

PHOTO_BYTES = {
    "bottle.webp": 33306,
    "clock.webp": 41498,
    "cup.webp": 44464,
    "headphones.webp": 330532,
    "keyboard.webp": 50824,
    "lamp.webp": 137448,
    "mat.webp": 209944,
    "mouse.webp": 53290,
    "notebooks.webp": 139934,
    "planter.webp": 154792,
    "stand.webp": 74536,
    "tray.webp": 104714,
}


def test_reviewed_manifest_matches_demo_copy_and_photo_files():
    """The import set keeps the twelve demo rows and the licensed local files."""
    assert len(WORKSPACE_CATALOG) == 60
    assert validate_manifest(WORKSPACE_CATALOG) == list(WORKSPACE_CATALOG)
    legacy = {item.legacy_name: item for item in WORKSPACE_CATALOG if item.legacy_name}
    assert set(legacy) == set(PRODUCT_MEDIA)
    for name, description, price, stock in bootstrap.DEMO_PRODUCTS:
        item = legacy[name]
        media = PRODUCT_MEDIA[name]
        assert item.name == name
        assert item.description == description
        assert item.price == Decimal(price)
        assert item.stock == stock
        assert item.category == PRODUCT_CATEGORIES[name]
        assert item.image_key == media["image_key"]
        assert item.image_alt == media["image_alt"]
        assert item.material == media.get("material")
        assert item.width_mm == media.get("width_mm")
        assert item.depth_mm == media.get("depth_mm")
        assert item.height_mm == media.get("height_mm")
        assert item.image_alt == IMAGE_ALTS[item.image_key]
    sizes = {name: (PHOTO_ROOT / name).stat().st_size for name in PHOTO_BYTES}
    assert sizes == PHOTO_BYTES
    referenced = {
        f"{item.image_key}.webp" for item in WORKSPACE_CATALOG if item.image_key
    }
    assert referenced <= set(PHOTO_BYTES)
    assert "workspace.webp" not in referenced
    assert sum(PHOTO_BYTES[name] for name in referenced) == sum(PHOTO_BYTES.values())


def test_invalid_manifest_and_missing_photo_write_nothing(db, tmp_path):
    broken = [item.model_dump() for item in WORKSPACE_CATALOG]
    broken[0]["price"] = "-1.00"
    with pytest.raises(ValueError, match="invalid"):
        import_catalog(db, broken)
    with pytest.raises(ValidationError):
        validate_manifest(broken)
    with pytest.raises(ValueError, match="local photo set"):
        import_catalog(db, photo_root=tmp_path)
    with pytest.raises(ValueError, match="100"):
        import_catalog(db, list(WORKSPACE_CATALOG) + list(WORKSPACE_CATALOG))
    assert db.scalar(select(func.count()).select_from(Product)) == 0
    assert db.scalar(select(func.count()).select_from(ImportedCatalogItem)) == 0


def test_empty_import_is_repeatable_and_preserves_nothing_it_did_not_create(db):
    assert import_catalog(db) == 60
    db.commit()
    assert db.get(DemoCatalog, bootstrap.CATALOG_EDITION) is None
    first_ids = set(db.scalars(select(Product.id)))
    depleted = db.scalar(select(Product).where(Product.catalog_key == "task-light"))
    depleted.stock = 1
    depleted.price = Decimal("70.00")
    depleted.description = "Edited after import"
    db.commit()
    assert import_catalog(db) == 0
    db.commit()
    assert set(db.scalars(select(Product.id))) == first_ids
    assert db.scalar(select(func.count()).select_from(Product)) == 60
    assert depleted.stock == 1
    assert depleted.price == Decimal("70.00")
    assert depleted.description == "Edited after import"


def test_import_adopts_the_twelve_without_overwriting_edits(db, user):
    assert bootstrap.seed_demo(db) == 12
    db.commit()
    original = db.scalars(select(Product).order_by(Product.id)).all()
    original_ids = [product.id for product in original]
    stand = original[0]
    stand.price = Decimal("91.25")
    stand.stock = 1
    stand.description = "Kept description"
    stand.image_alt = "Kept alt"
    stand.reserved_stock = 2
    light = next(product for product in original if product.name == "Task Light")
    order = Order(
        user_id=user.id,
        status="draft",
        currency="GBP",
        total=Decimal("65.00"),
    )
    db.add(order)
    db.flush()
    db.add(
        OrderLine(
            order_id=order.id,
            product_id=light.id,
            product_name="Task Light",
            unit_price=Decimal("65.00"),
            quantity=1,
        )
    )
    db.add(CartLine(user_id=user.id, product_id=stand.id, quantity=2))
    db.commit()
    assert import_catalog(db) == 48
    db.commit()
    assert [product.id for product in original] == original_ids
    assert stand.price == Decimal("91.25")
    assert stand.stock == 1
    assert stand.description == "Kept description"
    assert stand.image_alt == "Kept alt"
    assert stand.reserved_stock == 2
    assert stand.catalog_key == "oak-monitor-stand"
    assert db.get(CartLine, (user.id, stand.id)).quantity == 2
    line = db.scalar(select(OrderLine))
    assert line.product_name == "Task Light"
    assert line.unit_price == Decimal("65.00")
    assert light.price == Decimal("65.00")
    assert db.get(DemoCatalog, bootstrap.CATALOG_EDITION) is not None
    assert db.scalar(select(func.count()).select_from(Product)) == 60
    assert import_catalog(db) == 0


def test_import_refuses_ambiguous_legacy_rows_without_writes(db):
    db.add(Product(name="Oak Monitor Stand", price="10.00", stock=1, currency="GBP"))
    db.add(Product(name="Oak Monitor Stand", price="12.00", stock=1, currency="GBP"))
    db.commit()
    with pytest.raises(ValueError, match="more than one"):
        import_catalog(db)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Product)) == 2
    assert db.scalar(select(func.count()).select_from(ImportedCatalogItem)) == 0
    assert set(db.scalars(select(Product.catalog_key))) == {None}

    for name, description, price, stock in bootstrap.DEMO_PRODUCTS[:6]:
        db.add(
            Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                currency="GBP",
            )
        )
    db.commit()
    with pytest.raises(ValueError, match="missing while other products exist"):
        import_catalog(db)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Product)) == 8
    assert db.scalar(select(func.count()).select_from(ImportedCatalogItem)) == 0
    assert all(product.catalog_key is None for product in db.scalars(select(Product)))


def test_import_links_an_existing_key_without_changing_the_row(db):
    assert bootstrap.seed_demo(db) == 12
    product = db.scalar(select(Product).where(Product.name == "Task Light"))
    product.catalog_key = "task-light"
    product.price = Decimal("12.34")
    db.commit()
    assert import_catalog(db) == 48
    db.commit()
    assert product.price == Decimal("12.34")
    assert product.description == "Fictional adjustable warm-white desk lamp."
    assert db.get(ImportedCatalogItem, "task-light").product_id == product.id


def test_import_refuses_when_categories_are_missing(db):
    for category in db.scalars(select(Category)):
        db.delete(category)
    db.commit()
    with pytest.raises(ValueError, match="apply migrations"):
        import_catalog(db)
    assert db.scalar(select(func.count()).select_from(Product)) == 0


def test_deleted_import_is_not_recreated(db):
    assert import_catalog(db) == 60
    db.commit()
    retired = db.scalar(
        select(Product).where(Product.catalog_key == "unmarked-sample-box")
    )
    retired_id = retired.id
    db.delete(retired)
    db.commit()
    ledger = db.get(ImportedCatalogItem, "unmarked-sample-box")
    assert ledger.product_id is None
    assert import_catalog(db) == 0
    db.commit()
    assert db.get(Product, retired_id) is None
    assert db.scalar(select(func.count()).select_from(Product)) == 59
    db.add(
        Product(
            name="Imposter box",
            price="1.00",
            stock=1,
            currency="GBP",
            catalog_key="unmarked-sample-box",
        )
    )
    db.commit()
    with pytest.raises(ValueError, match="Retired catalog key"):
        import_catalog(db)
    db.rollback()
    assert (
        db.scalar(select(Product).where(Product.name == "Unmarked Sample Box")) is None
    )
    assert db.scalar(select(func.count()).select_from(Product)) == 60


def test_import_rolls_back_when_a_write_fails(db):
    def fail_insert(*_args):
        raise SQLAlchemyError("sensitive marker")

    event.listen(Product, "before_insert", fail_insert)
    try:
        with pytest.raises(SQLAlchemyError, match="sensitive marker"):
            import_catalog(db)
    finally:
        event.remove(Product, "before_insert", fail_insert)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Product)) == 0
    assert db.scalar(select(func.count()).select_from(ImportedCatalogItem)) == 0


def test_overlapping_import_cannot_duplicate_the_catalog(tmp_path):
    from app.models.base import Base

    engine = create_engine(
        f"sqlite:///{tmp_path / 'overlap.db'}",
        connect_args={"check_same_thread": False, "timeout": 2},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            Category(slug=slug, name=name, position=position)
            for slug, name, position in CATEGORIES
        )
        session.commit()
    first = Session(engine)
    second = Session(engine)
    first.begin()
    assert import_catalog(first) == 60
    second.begin()
    with pytest.raises((IntegrityError, OperationalError)):
        import_catalog(second)
    second.rollback()
    second.close()
    first.commit()
    first.close()
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Product)) == 60
        assert import_catalog(session) == 0
        session.commit()
        assert session.scalar(select(func.count()).select_from(Product)) == 60
    engine.dispose()


def test_overlapping_postgresql_import_waits_and_adds_nothing(db):
    """The second import must see the first commit, not insert a second copy."""
    if db.get_bind().dialect.name != "postgresql":
        pytest.skip("Requires disposable PostgreSQL TEST_DATABASE_URL")
    engine = db.get_bind()
    outcome = {}
    committed = False

    def second_import():
        with Session(engine) as second:
            second.begin()
            second.execute(text("SET lock_timeout = '5s'"))
            try:
                outcome["count"] = import_catalog(second)
                second.commit()
            except Exception as exc:
                outcome["error"] = exc
                second.rollback()

    worker = threading.Thread(target=second_import)
    try:
        assert import_catalog(db) == 60
        worker.start()
        deadline = time.monotonic() + 5
        waiting = 0
        while time.monotonic() < deadline:
            waiting = db.scalar(
                text(
                    "SELECT COUNT(*) FROM pg_locks "
                    "WHERE NOT granted AND relation = 'products'::regclass"
                )
            )
            if waiting:
                break
            time.sleep(0.05)
        assert waiting, "second import did not wait for the product lock"
        db.commit()
        committed = True
    finally:
        if not committed:
            db.rollback()
        worker.join(timeout=5)
    assert not worker.is_alive()
    assert outcome.get("error") is None
    assert outcome["count"] == 0
    db.expire_all()
    products = list(db.scalars(select(Product)))
    ledgers = list(db.scalars(select(ImportedCatalogItem)))
    assert len(products) == 60
    assert len({product.catalog_key for product in products}) == 60
    assert {ledger.catalog_key for ledger in ledgers} == {
        product.catalog_key for product in products
    }
    assert {ledger.product_id for ledger in ledgers} == {
        product.id for product in products
    }


def test_imported_catalog_pages_every_category_and_hides_the_key(client, db):
    assert import_catalog(db) == 60
    db.commit()
    first = client.get("/api/v1/products/search", params={"limit": 24})
    assert first.status_code == 200
    assert first.json()["total"] == 60
    assert len(first.json()["items"]) == 24
    assert "catalog_key" not in first.json()["items"][0]
    assert (
        len(
            client.get(
                "/api/v1/products/search", params={"limit": 24, "skip": 24}
            ).json()["items"]
        )
        == 24
    )
    third = client.get("/api/v1/products/search", params={"limit": 24, "skip": 48})
    assert len(third.json()["items"]) == 12
    for slug, _, _ in CATEGORIES:
        page = client.get(
            "/api/v1/products/search", params={"category": slug, "limit": 100}
        )
        assert page.status_code == 200
        assert page.json()["total"] >= 1
    found = client.get("/api/v1/products/search", params={"q": "Unmarked Sample Box"})
    assert found.json()["total"] == 1
    assert found.json()["items"][0]["image"] is None
    assert found.json()["items"][0]["name"] in {
        item["name"] for item in third.json()["items"]
    }
    stocked = client.get(
        "/api/v1/products/search", params={"in_stock": True, "limit": 100}
    )
    assert stocked.json()["total"] == 58
    names = {item["name"] for item in stocked.json()["items"]}
    assert "Ceramic Pen Cup" not in names
    assert "Unmarked Sample Box" not in names
    schema = client.get("/openapi.json").json()
    for name in ("ProductRead", "ProductCreate", "ProductUpdate"):
        assert "catalog_key" not in schema["components"]["schemas"][name]["properties"]


def test_admin_edits_cannot_set_or_clear_the_catalog_key(client, db):
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=True,
    )
    db.add(admin)
    db.commit()
    token = create_access_token(admin.id)
    rejected = client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Admin product",
            "price": "1.20",
            "stock": 1,
            "category": "desk-organization",
            "catalog_key": "smuggled-key",
        },
    )
    assert rejected.status_code == 422
    assert import_catalog(db) == 60
    db.commit()
    product = db.scalar(select(Product).where(Product.catalog_key == "task-light"))
    updated = client.put(
        f"/api/v1/products/{product.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": "11.00", "description": "Admin edited copy"},
    )
    assert updated.status_code == 200
    assert "catalog_key" not in updated.json()
    db.refresh(product)
    assert product.catalog_key == "task-light"
    assert product.price == Decimal("11.00")
    assert product.description == "Admin edited copy"
    rejected_edit = client.put(
        f"/api/v1/products/{product.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": "12.00", "catalog_key": "other-key"},
    )
    assert rejected_edit.status_code == 422
    db.refresh(product)
    assert product.catalog_key == "task-light"
    assert product.price == Decimal("11.00")


def test_import_cli_requires_confirmation_and_hides_database_errors(
    db, monkeypatch, capsys
):
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(bootstrap, "SessionLocal", sessionmaker(bind=db.get_bind()))
    with pytest.raises(SystemExit):
        bootstrap.main(["import-catalog"])
    assert db.scalar(select(func.count()).select_from(Product)) == 0

    def fail_import(_session):
        raise SQLAlchemyError("sensitive marker")

    monkeypatch.setattr(bootstrap, "import_catalog", fail_import)
    with pytest.raises(SystemExit):
        bootstrap.main(["import-catalog", "--confirm-import"])
    assert "sensitive" not in capsys.readouterr().err
    monkeypatch.setattr(bootstrap, "import_catalog", import_catalog)
    bootstrap.main(["import-catalog", "--confirm-import"])
    assert "Imported 60 catalog products" in capsys.readouterr().out
    bootstrap.main(["import-catalog", "--confirm-import"])
    assert "Imported 0 catalog products" in capsys.readouterr().out
    assert db.scalar(select(func.count()).select_from(Product)) == 60


def test_manifest_parser_rejects_a_short_row():
    with pytest.raises(ValueError, match="12 fields"):
        from app.catalog_manifest import _parse_row

        _parse_row("only | three | fields")


def test_photo_bytes_match_the_files_on_disk():
    """Recorded sizes are the product photographs, not the storefront hero."""
    assert os.path.basename(PHOTO_ROOT) == "photos"
    hero = Path(PHOTO_ROOT / "workspace.webp")
    assert hero.is_file()
    assert hero.name not in PHOTO_BYTES
