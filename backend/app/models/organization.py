from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db import Base


class Organization(Base):
    __tablename__ = "organizations"
    """
    SQLAlchemy model for organizations.
    Fields:
        - id: Integer, primary key
        - company, domain_names, name_of_representative, role, email: organization info
        - company_id: external company reference
        - preferences, integration_status: settings and integrations
        - profile_url: image link
        - created_at, updated_at: timestamps
    Relationships:
        - users: all users in this organization
        - tickets: all tickets for this organization
    """
    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=True)
    domain_names = Column(JSON, nullable=True)
    name_of_representative = Column(String, nullable=True)
    role = Column(String, nullable=True)
    email = Column(String, nullable=True)
    company_id = Column(Integer, nullable=True)
    preferences = Column(JSON, nullable=True)
    integration_status = Column(JSON, nullable=True)
    profile_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    users = relationship(
        "User", back_populates="organization"
    )  # Users in this organization
    tickets = relationship(
        "Ticket", back_populates="organization"
    )  # Tickets for this organization
