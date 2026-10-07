from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog_media import image_key_sql
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.category import Category


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "price >= 0 AND price <= 9999999999.99", name="ck_products_price_range"
        ),
        CheckConstraint(
            "stock >= 0 AND stock <= 2147483647", name="ck_products_stock_range"
        ),
        CheckConstraint(
            "reserved_stock >= 0 AND stock + reserved_stock <= 2147483647",
            name="ck_products_reservation_range",
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
        CheckConstraint(image_key_sql(), name="ck_products_image_key"),
        CheckConstraint(
            "(image_key IS NULL AND image_alt IS NULL) OR "
            "(image_key IS NOT NULL AND length(trim(image_alt)) >= 1 "
            "AND length(image_alt) <= 200)",
            name="ck_products_image_pair",
        ),
        CheckConstraint(
            "material IS NULL OR (length(trim(material)) >= 1 AND length(material) <= 80)",
            name="ck_products_material",
        ),
        CheckConstraint(
            "width_mm IS NULL OR (width_mm >= 1 AND width_mm <= 10000)",
            name="ck_products_width_mm",
        ),
        CheckConstraint(
            "depth_mm IS NULL OR (depth_mm >= 1 AND depth_mm <= 10000)",
            name="ck_products_depth_mm",
        ),
        CheckConstraint(
            "height_mm IS NULL OR (height_mm >= 1 AND height_mm <= 10000)",
            name="ck_products_height_mm",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="GBP", server_default="GBP"
    )
    reserved_stock: Mapped[int] = mapped_column(default=0, server_default="0")
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "categories.id", name="fk_products_category_id", ondelete="RESTRICT"
        ),
        nullable=False,
        index=True,
    )
    category: Mapped[Category] = relationship(back_populates="products")
    image_key: Mapped[str | None] = mapped_column(String(64))
    image_alt: Mapped[str | None] = mapped_column(String(200))
    material: Mapped[str | None] = mapped_column(String(80))
    width_mm: Mapped[int | None] = mapped_column()
    depth_mm: Mapped[int | None] = mapped_column()
    height_mm: Mapped[int | None] = mapped_column()

    @property
    def image(self) -> dict[str, str] | None:
        """Return the allowlisted photo, or nothing when the product has no key."""
        if self.image_key is None or self.image_alt is None:
            return None
        return {"key": self.image_key, "alt": self.image_alt}
