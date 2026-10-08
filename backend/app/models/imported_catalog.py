from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportedCatalogItem(Base):
    """Remembers an imported identity after the product row is gone.

    A null product id means the imported product was deleted. The import must
    not create it again.
    """

    __tablename__ = "imported_catalog_items"
    __table_args__ = (
        UniqueConstraint("product_id", name="uq_imported_catalog_items_product_id"),
        CheckConstraint(
            "length(catalog_key) >= 1 AND length(catalog_key) <= 64",
            name="ck_imported_catalog_items_key",
        ),
    )

    catalog_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "products.id",
            name="fk_imported_catalog_items_product_id",
            ondelete="SET NULL",
        )
    )
