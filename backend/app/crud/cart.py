from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.cart import CartLine
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItem, CartRead
from app.schemas.product import ProductRead


def read_cart(db: Session, user_id: int) -> CartRead:
    # One statement: prices, availability and quantities share the same snapshot.
    """Read quantities and current prices together and calculate exact GBP totals."""
    rows = db.execute(
        select(CartLine, Product)
        .join(Product, Product.id == CartLine.product_id)
        .where(CartLine.user_id == user_id)
        .order_by(CartLine.product_id)
        .execution_options(populate_existing=True)
    ).all()
    items = [
        CartItem(
            product=ProductRead.model_validate(product),
            quantity=line.quantity,
            available=line.quantity <= product.stock,
            line_total=product.price * line.quantity,
        )
        for line, product in rows
    ]
    return CartRead(
        items=items, subtotal=sum((item.line_total for item in items), Decimal("0.00"))
    )


def lock_customer(db: Session, user_id: int) -> None:
    # Serialize mutations even when a cart has no rows yet. PostgreSQL is the
    # runtime; SQLite is only used for sequential behavioral tests.
    """Serialize writes even for empty carts and recheck active status under lock."""
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")


def set_quantity(db: Session, user_id: int, product_id: int, quantity: int) -> CartRead:
    """Commit an absolute quantity; stock limits apply only to new lines and increases."""
    lock_customer(db, user_id)
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    line = db.get(CartLine, (user_id, product_id), populate_existing=True)
    if (line is None or quantity > line.quantity) and quantity > product.stock:
        raise HTTPException(
            status_code=409, detail="Requested quantity exceeds current stock"
        )
    if line is None:
        db.add(CartLine(user_id=user_id, product_id=product_id, quantity=quantity))
    else:
        line.quantity = quantity
    db.flush()
    result = read_cart(db, user_id)
    db.commit()
    return result


def remove_line(db: Session, user_id: int, product_id: int) -> None:
    """Serialize and commit an idempotent removal scoped to the customer."""
    lock_customer(db, user_id)
    db.execute(
        delete(CartLine).where(
            CartLine.user_id == user_id, CartLine.product_id == product_id
        )
    )
    db.commit()
