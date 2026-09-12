"""Explicit operator commands for a disposable portfolio demo database."""

import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.demo_catalog import DemoCatalog
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate
from app.schemas.user import UserBase, UserCreate

DEMO_PRODUCTS = (
    ("Oak Monitor Stand", "Fictional solid-oak desk riser.", "79.00", 12),
    ("Felt Desk Mat", "Fictional charcoal felt workspace mat.", "29.50", 24),
    ("Task Light", "Fictional adjustable warm-white desk lamp.", "65.00", 8),
    ("Cable Tray", "Fictional under-desk cable organiser.", "24.00", 18),
    ("Notebook Set", "Fictional set of three dotted notebooks.", "12.90", 30),
    ("Ceramic Pen Cup", "Fictional hand-finished stationery holder.", "18.00", 0),
)
ADDITIONAL_DEMO_PRODUCTS = (
    (
        "Compact Keyboard",
        "Fictional low-profile keyboard for everyday desk work.",
        "49.00",
        16,
    ),
    (
        "Focus Headphones",
        "Fictional padded over-ear headphones for a quiet workspace.",
        "89.00",
        7,
    ),
    (
        "Insulated Bottle",
        "Fictional green steel bottle for desk-side hydration.",
        "26.00",
        22,
    ),
    (
        "Handled Planter",
        "Fictional rustic ceramic planter; plant not included.",
        "21.00",
        9,
    ),
    (
        "Analogue Desk Clock",
        "Fictional round bedside or desk clock with a warm metallic finish.",
        "32.00",
        11,
    ),
    (
        "Wireless Mouse",
        "Fictional compact red wireless mouse for everyday browsing.",
        "23.00",
        14,
    ),
)
DEMO_PRODUCTS += ADDITIONAL_DEMO_PRODUCTS
CATALOG_EDITION = "twelve-products"


def seed_demo(db):
    """Populate only an empty catalog; never overwrite or replenish existing data."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("LOCK TABLE products IN SHARE ROW EXCLUSIVE MODE"))
    if db.get(DemoCatalog, CATALOG_EDITION) is not None:
        return 0
    if db.scalar(select(Product.id).limit(1)) is not None:
        return 0
    for name, description, price, stock in DEMO_PRODUCTS:
        data = ProductCreate(
            name=name, description=description, price=price, stock=stock, currency="GBP"
        )
        db.add(Product(**data.model_dump()))
    db.add(DemoCatalog(edition=CATALOG_EDITION))
    db.flush()
    return len(DEMO_PRODUCTS)


def expand_demo(db):
    """Append this edition once without touching existing products or saved carts."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("LOCK TABLE products IN SHARE ROW EXCLUSIVE MODE"))
    if db.get(DemoCatalog, CATALOG_EDITION) is not None:
        return 0
    if db.scalar(select(Product.id).limit(1)) is None:
        return seed_demo(db)
    # Refuse ambiguity instead of silently adopting or duplicating existing items.
    names = [product[0] for product in ADDITIONAL_DEMO_PRODUCTS]
    if db.scalar(select(Product.id).where(Product.name.in_(names)).limit(1)):
        raise ValueError("Expansion names already exist; inspect the catalog manually.")
    for name, description, price, stock in ADDITIONAL_DEMO_PRODUCTS:
        data = ProductCreate(
            name=name, description=description, price=price, stock=stock, currency="GBP"
        )
        db.add(Product(**data.model_dump()))
    db.add(DemoCatalog(edition=CATALOG_EDITION))
    db.flush()
    return len(ADDITIONAL_DEMO_PRODUCTS)


def ensure_admin(db, email, password=None, *, promote_existing=False):
    email = str(UserBase(email=email).email)
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if user is not None:
        if not user.is_active:
            raise ValueError("Disabled accounts cannot be bootstrapped.")
        if user.is_superuser:
            return "Admin already exists; credentials unchanged."
        if not promote_existing:
            raise ValueError("Existing customer requires --promote-existing.")
        user.is_superuser = True
        db.flush()
        return "Existing account promoted; credentials unchanged."
    if promote_existing:
        raise ValueError("No existing account to promote.")
    data = UserCreate(email=email, password=password)
    db.add(
        User(
            email=str(data.email),
            hashed_password=get_password_hash(data.password),
            is_active=True,
            is_superuser=True,
        )
    )
    db.flush()
    return "Admin created."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed-demo")
    seed.add_argument("--confirm-demo", action="store_true", required=True)
    expand = commands.add_parser("expand-demo")
    expand.add_argument("--confirm-demo", action="store_true", required=True)
    admin = commands.add_parser("admin")
    admin.add_argument("--email", required=True)
    admin.add_argument("--promote-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        with SessionLocal.begin() as db:
            if args.command in {"seed-demo", "expand-demo"}:
                count = (
                    seed_demo(db) if args.command == "seed-demo" else expand_demo(db)
                )
                message = (
                    f"Created {count} demo products; existing catalogs are preserved."
                )
            else:
                email = str(UserBase(email=args.email).email)
                existing = db.scalar(select(User.id).where(User.email == email))
                password = None
                if existing is None and not args.promote_existing:
                    password = getpass("New admin password (8–128 characters): ")
                    if password != getpass("Confirm password: "):
                        raise ValueError("Passwords do not match.")
                message = ensure_admin(
                    db, email, password, promote_existing=args.promote_existing
                )
        print(message)
    except ValidationError:
        parser.exit(1, "Invalid email or password (must be 8–128 characters).\n")
    except (ValueError, EOFError) as exc:
        parser.exit(1, f"Bootstrap refused: {exc}\n")
    except SQLAlchemyError:
        parser.exit(
            1,
            "Database operation failed; transaction rolled back. Check migrations and connection.\n",
        )


if __name__ == "__main__":
    main()
