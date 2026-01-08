from sqlalchemy import Column, String, Integer, DateTime, JSON
from datetime import datetime
from app.db import Base

class ZendeskTicket(Base):
    __tablename__ = "zendesk_tickets"

    id = Column(Integer, primary_key=True, index=True)
    json_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    ticket_type = Column(String, nullable=True)