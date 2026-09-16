from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "price >= 0 AND price <= 9999999999.99", name="ck_products_price_range"
        ),
        CheckConstraint(
            "stock >= 0 AND stock <= 2147483647", name="ck_products_stock_range"
        ),
        CheckConstraint("currency = 'GBP'", name="ck_products_currency"),
        CheckConstraint(
            "length(trim(name)) >= 1 AND length(name) <= 255",
            name="ck_products_name_length",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 10000",
            name="ck_products_description_length",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="GBP", server_default="GBP"
    )
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
