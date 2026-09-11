from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer

from app.models.base import Base


class CartLine(Base):
    """The customer's active cart is its set of lines; an empty cart needs no row."""

    __tablename__ = "cart_lines"
    __table_args__ = (
        CheckConstraint("quantity >= 1 AND quantity <= 99", name="ck_cart_quantity"),
    )

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    quantity = Column(Integer, nullable=False)
