"""
Models package: Contains SQLAlchemy ORM models for Organization, User, and Ticket.
Importing all models here ensures relationships are registered for table creation and queries.
"""

from .organization import Organization
from .user import User
from .ticket import Ticket
