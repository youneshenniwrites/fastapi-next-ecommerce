from sqlalchemy import Column, String

from app.models.base import Base


class DemoCatalog(Base):
    """Records the one-time catalog expansion independently of mutable products."""

    __tablename__ = "demo_catalog_editions"

    edition = Column(String(64), primary_key=True)
