from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CartLine(Base):
    """The customer's active cart is its set of lines; an empty cart needs no row."""

    __tablename__ = "cart_lines"
    __table_args__ = (
        CheckConstraint("quantity >= 1 AND quantity <= 99", name="ck_cart_quantity"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
