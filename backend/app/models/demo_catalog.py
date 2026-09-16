from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DemoCatalog(Base):
    """Records the one-time catalog expansion independently of mutable products."""

    __tablename__ = "demo_catalog_editions"

    edition: Mapped[str] = mapped_column(String(64), primary_key=True)
