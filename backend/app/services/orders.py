from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

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
