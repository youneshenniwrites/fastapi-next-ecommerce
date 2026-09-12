import pytest
from sqlalchemy import func, select

from app import bootstrap
from app.core.security import verify_password
from app.models.product import Product
from app.models.user import User


def test_seed_preserves_edits_and_does_not_duplicate(db):
    assert bootstrap.seed_demo(db) == 12
    db.commit()
    product = db.scalar(select(Product).order_by(Product.id))
    product.name = "Edited name"
    product.stock = 1
    db.commit()
    assert bootstrap.seed_demo(db) == 0
    assert db.scalar(select(func.count()).select_from(Product)) == 12
    assert product.stock == 1
    assert product.name == "Edited name"
    assert all(p.currency == "GBP" for p in db.scalars(select(Product)))


def test_seed_preserves_unrelated_catalog(db):
    db.add(Product(name="Existing", price="1.00", stock=2, currency="GBP"))
    db.commit()
    assert bootstrap.seed_demo(db) == 0
    assert db.scalar(select(func.count()).select_from(Product)) == 1


def test_admin_creation_and_rerun_preserve_password(db):
    bootstrap.ensure_admin(db, "admin@example.com", "original-password")
    db.commit()
    bootstrap.ensure_admin(db, "admin@example.com", "different-password")
    user = db.scalar(select(User))
    assert user.is_active and user.is_superuser
    assert verify_password("original-password", user.hashed_password)
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_promotion_is_explicit_and_preserves_credentials(db, user):
    original = user.hashed_password
    with pytest.raises(ValueError, match="promote-existing"):
        bootstrap.ensure_admin(db, user.email)
    assert not user.is_superuser
    bootstrap.ensure_admin(db, user.email, promote_existing=True)
    assert user.is_superuser
    assert user.hashed_password == original
    user.is_active = False
    with pytest.raises(ValueError, match="Disabled"):
        bootstrap.ensure_admin(db, user.email, promote_existing=True)
    assert not user.is_active


def test_missing_promotion_target_and_invalid_credentials(db):
    with pytest.raises(ValueError, match="No existing"):
        bootstrap.ensure_admin(db, "absent@example.com", promote_existing=True)
    with pytest.raises(ValueError):
        bootstrap.ensure_admin(db, "invalid", "password123")
    with pytest.raises(ValueError):
        bootstrap.ensure_admin(db, "admin@example.com", "short")
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_cli_transactions_and_login(db, client, monkeypatch, capsys):
    # Reuse the disposable test engine, including PostgreSQL in CI.
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(bootstrap, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(bootstrap, "getpass", lambda _: "demo-password123")
    bootstrap.main(["seed-demo", "--confirm-demo"])
    bootstrap.main(["admin", "--email", "admin@example.com"])
    bootstrap.main(["admin", "--email", "admin@example.com"])
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "demo-password123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    result = client.post(
        "/api/v1/products/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Admin product", "price": "1.20", "stock": 1},
    )
    assert result.status_code == 201
    assert "demo-password123" not in capsys.readouterr().out


def test_cli_refusal_and_password_redaction(db, monkeypatch, capsys):
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(bootstrap, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(bootstrap, "getpass", lambda _: "short")
    with pytest.raises(SystemExit):
        bootstrap.main(["admin", "--email", "admin@example.com"])
    assert "short" not in capsys.readouterr().err
    assert db.scalar(select(func.count()).select_from(User)) == 0
    with pytest.raises(SystemExit):
        bootstrap.main(["seed-demo"])


def test_cli_rolls_back_partial_seed(db, monkeypatch, capsys):
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(bootstrap, "SessionLocal", sessionmaker(bind=db.get_bind()))

    def failed_seed(session):
        session.add(Product(name="Partial", price="1.00", stock=1, currency="GBP"))
        session.flush()
        raise SQLAlchemyError("sensitive database details")

    monkeypatch.setattr(bootstrap, "seed_demo", failed_seed)
    with pytest.raises(SystemExit):
        bootstrap.main(["seed-demo", "--confirm-demo"])
    assert db.scalar(select(func.count()).select_from(Product)) == 0
    assert "sensitive" not in capsys.readouterr().err


def test_expansion_preserves_legacy_edits_and_cart_and_runs_once(db, user):
    from app.models.cart import CartLine

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
    db.flush()
    original = db.scalars(select(Product).order_by(Product.id)).all()
    original[0].name = "Renamed original"
    original[0].price = "91.25"
    original[0].stock = 0
    db.add(CartLine(user_id=user.id, product_id=original[0].id, quantity=2))
    db.commit()
    before = [(p.id, p.name, p.description, str(p.price), p.stock) for p in original]
    assert bootstrap.expand_demo(db) == 6
    db.commit()
    after = db.scalars(select(Product).order_by(Product.id)).all()
    assert [
        (p.id, p.name, p.description, str(p.price), p.stock) for p in after[:6]
    ] == before
    assert db.get(CartLine, (user.id, original[0].id)).quantity == 2
    # Tracking cannot depend on a product's mutable name or stock.
    after[6].name = "Renamed addition"
    after[6].stock = 0
    db.delete(after[7])
    db.commit()
    assert bootstrap.expand_demo(db) == 0
    assert bootstrap.seed_demo(db) == 0
    assert db.scalar(select(func.count()).select_from(Product)) == 11
    assert after[6].stock == 0


def test_expansion_on_empty_catalog_is_complete_and_repeatable(db):
    assert bootstrap.expand_demo(db) == 12
    db.commit()
    assert bootstrap.expand_demo(db) == 0
    assert bootstrap.seed_demo(db) == 0
    assert db.scalar(select(func.count()).select_from(Product)) == 12


def test_expansion_refuses_name_collision_without_writes(db):
    from app.models.demo_catalog import DemoCatalog

    db.add(
        Product(
            name=bootstrap.ADDITIONAL_DEMO_PRODUCTS[0][0],
            price="1.00",
            stock=0,
            currency="GBP",
        )
    )
    db.commit()
    with pytest.raises(ValueError, match="already exist"):
        bootstrap.expand_demo(db)
    assert db.scalar(select(func.count()).select_from(Product)) == 1
    assert db.get(DemoCatalog, bootstrap.CATALOG_EDITION) is None


def test_expansion_cli_requires_confirmation_and_rolls_back(db, monkeypatch, capsys):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import sessionmaker

    from app.models.demo_catalog import DemoCatalog

    monkeypatch.setattr(bootstrap, "SessionLocal", sessionmaker(bind=db.get_bind()))
    with pytest.raises(SystemExit):
        bootstrap.main(["expand-demo"])

    def fail_marker(*_):
        raise SQLAlchemyError("sensitive error")

    event.listen(DemoCatalog, "before_insert", fail_marker)
    try:
        with pytest.raises(SystemExit):
            bootstrap.main(["expand-demo", "--confirm-demo"])
    finally:
        event.remove(DemoCatalog, "before_insert", fail_marker)
    assert db.scalar(select(func.count()).select_from(Product)) == 0
    assert db.get(DemoCatalog, bootstrap.CATALOG_EDITION) is None
    assert "sensitive error" not in capsys.readouterr().err
    bootstrap.main(["expand-demo", "--confirm-demo"])
    bootstrap.main(["expand-demo", "--confirm-demo"])
    assert db.scalar(select(func.count()).select_from(Product)) == 12
