from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)

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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="GBP", server_default="GBP")
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
