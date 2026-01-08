from pydantic import BaseModel
from typing import Optional, List

class Ticket(BaseModel):
    subject: str
    description: str
    priority: Optional[str] = "normal"
    tags: Optional[List[str]] = []
    assignee: Optional[str] = None
