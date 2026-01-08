from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate


async def create_ticket(db: AsyncSession, ticket: TicketCreate):
    db_ticket = Ticket(**ticket.dict())
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket


async def get_ticket(db: AsyncSession, ticket_id: int):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    return result.scalars().first()


"""
CRUD operations for Ticket model.

Async functions for create, read, update, delete operations.
Used by API routers.
"""
