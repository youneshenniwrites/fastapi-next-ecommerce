from pydantic import BaseModel, EmailStr
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr

# Schema for creating a user (signup)
class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}
