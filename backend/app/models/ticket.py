from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
import uuid


class Ticket(Base):
    """
    SQLAlchemy model for tickets.
    Fields:
        - id: Integer, primary key
        - url, source, type, subject, description: ticket info
        - priority, status, rating: ticket status and feedback
        - created_at, updated_at: timestamps
        - submitter_id: user who submitted
        - tags, attachments, feature, hypothesis: extra info
        - organization_id: organization reference
    Relationships:
        - submitter: user who submitted the ticket
        - organization: organization for the ticket
    """

    __tablename__ = "tickets"
    # id = Column(Integer, primary_key=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    type = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    description = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    status = Column(String, nullable=True)
    submitter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    tags = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    attachments = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    feature = Column(String, nullable=True)
    from sqlalchemy import types

    class Vector(types.UserDefinedType):
        def get_col_spec(self, **kw):
            return "vector"

    body_embedding = Column(Vector, nullable=True)
    cluster = Column(String, nullable=True)
    customer_problem = Column(String, nullable=True, name="Customer Problem")
    root_cause = Column(String, nullable=True, name="Root Cause")
    submitter = relationship("User", back_populates="tickets")
    organization = relationship("Organization", back_populates="tickets")
    clustered = Column(Boolean, nullable=True)
