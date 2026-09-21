from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order


def read_owned(db: Session, user_id: int, order_id: int) -> Order | None:
    """Apply ownership in SQL for every detail lookup, including administrators."""
    return db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.lines))
    )


def list_owned(db: Session, user_id: int, after_id: int, limit: int) -> list[Order]:
    """Bound reads and use a stable increasing-ID cursor."""
    return list(
        db.scalars(
            select(Order)
            .where(Order.user_id == user_id, Order.id > after_id)
            .order_by(Order.id)
            .limit(limit)
            .options(selectinload(Order.lines))
        )
    )
