from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    """
    User roles with there priviledges.

    Viewer: Can view dashboard data and own records.
    Analyst: Can view records and access insights/summaries
    Admin: Full access
    """

    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


# -------------------------------------------------------
# Request schemas
# -------------------------------------------------------


class RegisterRequest(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters long",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
    )

    model_config = {"extra": "forbid"}


class LoginRequest(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    model_config = {"extra": "forbid"}


# -------------------------------------------------------
# Response schemas
# -------------------------------------------------------


class UserResponse(BaseModel):
    """User data returned in API responses"""

    id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned after successful login or registration"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
