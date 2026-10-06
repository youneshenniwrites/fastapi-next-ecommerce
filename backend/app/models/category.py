from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "length(slug) >= 1 AND length(slug) <= 64",
            name="ck_categories_slug_length",
        ),
        CheckConstraint("slug <> 'all'", name="ck_categories_slug_not_all"),
        CheckConstraint(
            "length(trim(name)) >= 1 AND length(name) <= 80",
            name="ck_categories_name_length",
        ),
        CheckConstraint("position >= 0", name="ck_categories_position"),
        Index("ix_categories_slug", "slug", unique=True),
        Index("ix_categories_name", "name", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    products: Mapped[list[Product]] = relationship(back_populates="category")
