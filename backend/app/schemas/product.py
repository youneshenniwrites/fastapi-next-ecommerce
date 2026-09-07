from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    model_validator,
)

ProductName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
Price = Annotated[
    Decimal,
    Field(
        ge=0,
        le=Decimal("9999999999.99"),
        max_digits=12,
        decimal_places=2,
        allow_inf_nan=False,
    ),
]
Stock = Annotated[int, Field(ge=0, le=2147483647, strict=True)]
Description = Annotated[str, Field(max_length=10000)]
Currency = Literal["GBP"]


class ProductBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProductName
    description: Description | None = None
    price: Price
    currency: Currency = "GBP"
    stock: Stock


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProductName | None = None
    description: Description | None = None
    price: Price | None = None
    currency: Currency | None = None
    stock: Stock | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> Self:
        for field in ("name", "price", "currency", "stock"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price", when_used="json")
    def serialize_price(self, price: Decimal) -> str:
        return format(price, ".2f")
