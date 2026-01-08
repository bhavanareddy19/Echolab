from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class TicketBase(BaseModel):
    url: Optional[str]
    source: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    type: Optional[str]
    subject: Optional[str]
    description: Optional[str]
    priority: Optional[str]
    status: Optional[str]
    submitter_id: Optional[uuid.UUID]
    tags: Optional[str]
    rating: Optional[float]
    attachments: Optional[str]
    organization_id: Optional[int]
    feature: Optional[str]
    clustered: Optional[bool]


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
