from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    email: EmailStr


# Schema for creating a user (signup)
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}
