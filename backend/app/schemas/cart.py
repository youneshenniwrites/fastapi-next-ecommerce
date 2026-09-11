from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.product import ProductRead


class CartQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: Annotated[int, Field(strict=True, ge=1, le=99)]


class CartItem(BaseModel):
    product: ProductRead
    quantity: int
    available: bool
    line_total: Decimal

    @field_serializer("line_total", when_used="json")
    def serialize_total(self, value: Decimal) -> str:
        return format(value, ".2f")


class CartRead(BaseModel):
    items: list[CartItem]
    currency: Literal["GBP"] = "GBP"
    subtotal: Decimal

    @field_serializer("subtotal", when_used="json")
    def serialize_total(self, value: Decimal) -> str:
        return format(value, ".2f")
