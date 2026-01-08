from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ZendeskTicketIn(BaseModel):
    subject: str
    description: str
    tags: Optional[List[str]] = []
    organization_id: Optional[str] = None

class ZendeskTicketOut(BaseModel):
    id: int
    created_at: datetime
    ticket_type: str

    class Config:
        orm_mode = True
