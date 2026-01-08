from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ZendeskCredentialsIn(BaseModel):
    subdomain: str
    email: str
    api_token: str


class UserBase(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    active: Optional[bool]
    verified: Optional[bool]
    shared: Optional[bool]
    last_login_at: Optional[datetime]
    details: Optional[str]
    notes: Optional[str]
    suspended: Optional[bool]
    photo_url: Optional[str]
    ticket_restrictions: Optional[str]
    only_private_comments: Optional[str]
    organization_id: Optional[int]
    url: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
