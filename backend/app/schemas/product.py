from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class ProductRead(ProductBase):
    id: int
    # Pydantic v2: use ConfigDict(from_attributes=True) to allow ORM objects
    model_config = ConfigDict(from_attributes=True)
