"""
Pydantic schemas for Organization model.
Used for request/response validation in FastAPI endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class OrganizationBase(BaseModel):
    company: Optional[str]
    domain_names: Optional[Dict]
    name_of_representative: Optional[str]
    role: Optional[str]
    email: Optional[str]
    company_id: Optional[int]
    preferences: Optional[Dict]
    integration_status: Optional[Dict]
    profile_url: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class OrganizationCreate(OrganizationBase):
    pass


class Organization(OrganizationBase):
    id: int

    class Config:
        orm_mode = True
