from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    """Immutable quotation lines; placement claims inventory exactly once."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "payment_status IS NULL OR payment_status IN ('pending', 'paid', 'failed', 'cancelled', 'expired')",
            name="ck_orders_payment_status",
        ),
        CheckConstraint(
            "payment_status IS NULL OR (status = 'placed' AND payment_reference IS NOT NULL AND payment_expires_at IS NOT NULL)",
            name="ck_orders_payment_managed",
        ),
        CheckConstraint(
            "inventory_released_at IS NULL OR payment_status IN ('failed', 'cancelled', 'expired')",
            name="ck_orders_payment_release",
        ),
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_customer_key"),
        CheckConstraint("status IN ('draft', 'placed')", name="ck_orders_status"),
        CheckConstraint("currency = 'GBP'", name="ck_orders_currency"),
        CheckConstraint(
            "total >= 0 AND total <= 98999999999901.00", name="ck_orders_total"
        ),
    )
    payment_status: Mapped[str | None] = mapped_column(String(20))
    payment_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_reference: Mapped[str | None] = mapped_column(String(36), unique=True)
    payment_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_session_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    payment_checkout_url: Mapped[str | None] = mapped_column(String(2048))
    payment_request: Mapped[str | None] = mapped_column(Text)
    inventory_released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", server_default="draft"
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="GBP", server_default="GBP"
    )
    total: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lines: Mapped[list["OrderLine"]] = relationship(
        cascade="all, delete-orphan", order_by="OrderLine.id"
    )


class OrderLine(Base):
    """Product identity is historical: catalog deletion cannot erase a snapshot."""

    __tablename__ = "order_lines"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_lines_product"),
        CheckConstraint(
            "quantity >= 1 AND quantity <= 99", name="ck_order_lines_quantity"
        ),
        CheckConstraint(
            "unit_price >= 0 AND unit_price <= 9999999999.99",
            name="ck_order_lines_price",
        ),
        CheckConstraint("product_id >= 1", name="ck_order_lines_product_id"),
        CheckConstraint(
            "length(trim(product_name)) >= 1 AND length(product_name) <= 255",
            name="ck_order_lines_name",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column()
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column()

    @property
    def line_total(self) -> Decimal:
        """Derive a line total from its immutable exact price and quantity."""
        return self.unit_price * self.quantity


class PaymentEvent(Base):
    """Event identity and effects commit together; no sensitive provider payloads."""

    __tablename__ = "payment_events"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"))
    event_type: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
