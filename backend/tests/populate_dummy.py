"""
Script to populate the database with dummy organizations, users, and tickets.
Run this after tables are created to seed initial data for development/testing.
"""

import sys
import asyncio
from datetime import datetime
import uuid
from app.db import engine, SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.ticket import Ticket

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def populate():
    async with engine.begin() as conn:
        async with SessionLocal() as session:
            # Organizations
            org1 = Organization(
                company="Acme Corp",
                domain_names={"domains": ["acme.com"]},
                name_of_representative="Alice Smith",
                role="Admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                email="contact@acme.com",
                company_id=None,
                preferences={"theme": "dark"},
                integration_status={"zendesk": True},
                profile_url="https://acme.com/profile.png",
            )
            org2 = Organization(
                company="Beta LLC",
                domain_names={"domains": ["beta.io"]},
                name_of_representative="Bob Jones",
                role="User",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                email="info@beta.io",
                company_id=None,
                preferences={"theme": "light"},
                integration_status={"zendesk": False},
                profile_url="https://beta.io/profile.png",
            )
            session.add_all([org1, org2])
            await session.flush()

            # Users
            user1 = User(
                id=uuid.uuid4(),
                name="Alice Smith",
                email="alice@acme.com",
                phone="1234567890",
                role="Admin",
                active=True,
                verified=True,
                shared=False,
                last_login_at=datetime.utcnow(),
                details="CEO",
                notes="VIP",
                suspended=False,
                photo_url="https://acme.com/alice.png",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                ticket_restrictions=None,
                only_private_comments=None,
                organization_id=org1.id,
                url="https://acme.com/alice",
            )
            user2 = User(
                id=uuid.uuid4(),
                name="Bob Jones",
                email="bob@beta.io",
                phone="0987654321",
                role="User",
                active=True,
                verified=False,
                shared=True,
                last_login_at=datetime.utcnow(),
                details="Manager",
                notes="Regular",
                suspended=False,
                photo_url="https://beta.io/bob.png",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                ticket_restrictions=None,
                only_private_comments=None,
                organization_id=org2.id,
                url="https://beta.io/bob",
            )
            session.add_all([user1, user2])
            await session.flush()

            # Tickets
            ticket1 = Ticket(
                url="https://acme.com/ticket/1",
                source="email",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                type="bug",
                subject="Login issue",
                description="Cannot login to dashboard",
                priority="high",
                status="open",
                submitter_id=user1.id,
                tags="login,bug",
                rating=5.0,
                attachments="screenshot.png",
                organization_id=org1.id,
                feature="auth",
                hypothesis={"step": "investigate"},
            )
            ticket2 = Ticket(
                url="https://beta.io/ticket/2",
                source="web",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                type="feature",
                subject="Add export",
                description="Request to add export feature",
                priority="medium",
                status="pending",
                submitter_id=user2.id,
                tags="feature,request",
                rating=4.5,
                attachments="",
                organization_id=org2.id,
                feature="export",
                hypothesis={"step": "review"},
            )
            session.add_all([ticket1, ticket2])
            await session.commit()
            print("Database populated with dummy data.")


if __name__ == "__main__":
    asyncio.run(populate())
