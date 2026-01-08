from sqlalchemy import LargeBinary
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
import uuid


class User(Base):
    zendesk_subdomain = Column(String, nullable=True)
    zendesk_email = Column(String, nullable=True)
    zendesk_api_token = Column(String, nullable=True)
    """
    SQLAlchemy model for users.
    Fields:
        - id: UUID, primary key
        - name, email, phone, role: user info
        - active, verified, shared, suspended: status flags
        - last_login_at, created_at, updated_at: timestamps
        - details, notes, ticket_restrictions, only_private_comments: extra info
        - organization_id: foreign key to organizations
        - url, photo_url: profile links
    Relationships:
        - organization: links to Organization
        - tickets: tickets submitted by user
    """

    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=True)
    active = Column(Boolean, nullable=True)
    verified = Column(Boolean, nullable=True)
    shared = Column(Boolean, nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    suspended = Column(Boolean, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    ticket_restrictions = Column(String, nullable=True)
    only_private_comments = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    url = Column(String, nullable=True)
    organization = relationship("Organization", back_populates="users")
    tickets = relationship("Ticket", back_populates="submitter")
