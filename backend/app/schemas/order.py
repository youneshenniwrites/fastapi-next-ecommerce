from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class DraftLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: Annotated[int, Field(strict=True, ge=1, le=2147483647)]
    quantity: Annotated[int, Field(strict=True, ge=1, le=99)]


class DraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lines: Annotated[list[DraftLineCreate], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def unique_products(self) -> Self:
        """Reject ambiguous duplicate quantities rather than silently combine them."""
        if len({line.product_id for line in self.lines}) != len(self.lines):
            raise ValueError("Each product must appear once")
        return self


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal

    @field_serializer("unit_price", "line_total", when_used="json")
    def money(self, value: Decimal) -> str:
        """Return exact two-place GBP strings."""
        return format(value, ".2f")


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: Literal["draft", "placed"]
    currency: Literal["GBP"]
    total: Decimal
    created_at: datetime
    lines: list[OrderLineRead]

    @field_serializer("total", when_used="json")
    def money(self, value: Decimal) -> str:
        """Return an exact two-place GBP total."""
        return format(value, ".2f")
