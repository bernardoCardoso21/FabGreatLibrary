"""
Pydantic schemas for auth endpoints.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Opaque refresh token previously issued by this API.")


class TokenResponse(BaseModel):
    access_token: str = Field(description="Short-lived JWT (15 min). Send as 'Authorization: Bearer <token>'.")
    token_type: str = Field(default="bearer", description="Always 'bearer'.")
    refresh_token: str = Field(description="Opaque long-lived token. Use with POST /auth/refresh to obtain a new access token.")


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique user identifier.")
    email: str = Field(description="The user's email address.")
    is_active: bool = Field(description="False if the account has been disabled by an administrator.")
    is_admin: bool = Field(description="True if the user has administrative privileges.")
    collection_mode: str = Field(description="Collection tracking mode: 'master_set' or 'playset'.")
    created_at: datetime = Field(description="UTC timestamp when the account was created.")


class UpdatePreferencesRequest(BaseModel):
    collection_mode: Literal["master_set", "playset"]
