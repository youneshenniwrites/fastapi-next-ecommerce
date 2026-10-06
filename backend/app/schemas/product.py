from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    field_validator,
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
ProductSort = Literal["featured", "name", "price-asc", "price-desc"]
CategorySlug = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    ),
]


class ProductBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProductName
    description: Description | None = None
    price: Price
    currency: Currency = "GBP"
    stock: Stock


def _reject_reserved_category(value: str) -> str:
    if value == "all":
        raise ValueError("all is not a stored category")
    return value


class ProductCreate(ProductBase):
    category: CategorySlug

    @field_validator("category")
    @classmethod
    def category_is_assignable(cls, value: str) -> str:
        return _reject_reserved_category(value)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProductName | None = None
    description: Description | None = None
    price: Price | None = None
    currency: Currency | None = None
    stock: Stock | None = None
    category: CategorySlug | None = None

    @field_validator("category")
    @classmethod
    def category_is_assignable(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _reject_reserved_category(value)

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> Self:
        for field in ("name", "price", "currency", "stock", "category"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class CategorySummary(BaseModel):
    slug: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class CategoryCount(CategorySummary):
    count: int


class ProductRead(ProductBase):
    id: int
    category: CategorySummary
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("price", when_used="json")
    def serialize_price(self, price: Decimal) -> str:
        return format(price, ".2f")


class ProductPageRead(BaseModel):
    """A bounded catalog slice and the count of all matching products."""

    items: list[ProductRead]
    total: int
    limit: int
    skip: int
