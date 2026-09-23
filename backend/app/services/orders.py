from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.crud.cart import lock_customer
from app.crud.order import read_owned
from app.models.cart import CartLine
from app.models.order import Order, OrderLine
from app.models.product import Product
from app.schemas.order import DraftCreate


def create_draft(db: Session, user_id: int, payload: DraftCreate) -> Order:
    """Own one transaction, including the read already begun by authentication."""
    try:
        products = {
            p.id: p
            for p in db.scalars(
                select(Product).where(
                    Product.id.in_([line.product_id for line in payload.lines])
                )
            )
        }
        if len(products) != len(payload.lines):
            raise HTTPException(
                status_code=404, detail="A requested product no longer exists"
            )
        lines = [
            OrderLine(
                product_id=line.product_id,
                product_name=products[line.product_id].name,
                unit_price=products[line.product_id].price,
                quantity=line.quantity,
            )
            for line in payload.lines
        ]
        order = Order(
            user_id=user_id,
            total=sum((line.line_total for line in lines), Decimal("0.00")),
            lines=lines,
        )
        db.add(order)
        db.flush()
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise


def place_order(db: Session, user_id: int, order_id: int, key: str) -> Order:
    """Serialize customer retries and cart writes, then lock inventory in ID order."""
    try:
        lock_customer(db, user_id)
        existing = db.scalar(
            select(Order).where(Order.user_id == user_id, Order.idempotency_key == key)
        )
        if existing is not None:
            if existing.id != order_id:
                raise HTTPException(
                    409, "Idempotency key already used for another order"
                )
            db.commit()
            return existing
        order = read_owned(db, user_id, order_id)
        if order is None:
            raise HTTPException(404, "Order not found")
        if order.status != "draft":
            raise HTTPException(
                409, "Order already placed; retry with the original key"
            )
        if settings.STRIPE_ENABLED and not Decimal("0.30") <= order.total <= Decimal(
            "999999.99"
        ):
            raise HTTPException(
                409, "Sandbox payment total must be between GBP 0.30 and GBP 999999.99"
            )
        products = {
            p.id: p
            for p in db.scalars(
                select(Product)
                .where(Product.id.in_([line.product_id for line in order.lines]))
                .order_by(Product.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        }
        for line in order.lines:
            product = products.get(line.product_id)
            if product is None or product.stock < line.quantity:
                raise HTTPException(
                    409, "A product is unavailable or has insufficient stock"
                )
            if product.price != line.unit_price:
                raise HTTPException(
                    409, "Prices changed; create and confirm a new draft"
                )
            cart = db.get(CartLine, (user_id, line.product_id), populate_existing=True)
            if cart is None or cart.quantity != line.quantity:
                raise HTTPException(409, "Cart changed; create and confirm a new draft")
            product.stock -= line.quantity
            if settings.STRIPE_ENABLED:
                product.reserved_stock += line.quantity
            db.delete(cart)
        if settings.STRIPE_ENABLED:
            order.payment_status = "pending"
            order.payment_reference = str(uuid4())
            order.payment_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        order.status = "placed"
        order.idempotency_key = key
        db.flush()
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise
