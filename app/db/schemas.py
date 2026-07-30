from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

# --- BASE SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] =None
    is_active: bool = True


# --- REQUEST SCHEMAS (Input Validation) ---
class UserCreate(UserBase):
    """Schema used when creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema used for updating user profiles dynamically."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# --- RESPONSE SCHEMAS (Output Data Formatting) ---
class UserResponse(UserBase):
    """Schema returned by API endpoints (Hides hashed passwords)."""

    id: int
    created_at: datetime
    updated_at: datetime

    # ConfigDict allows Pydantic to read ORM objects directly (e.g., SQLAlchemy instances)
    model_config = ConfigDict(from_attributes=True)

