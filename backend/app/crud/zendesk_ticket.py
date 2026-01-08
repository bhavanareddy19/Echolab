from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, cast, String
from sqlalchemy.dialects.postgresql import ARRAY, insert
from datetime import datetime
from app.models.zendesk_ticket import ZendeskTicket
from app.schemas.zendesk_ticket import ZendeskTicketIn
import json

async def insert_zendesk_ticket(
    db: AsyncSession,
    ticket: ZendeskTicketIn,
    ticket_type: str
):
    stmt = insert(ZendeskTicket).values(
        json_payload=ticket.dict(),
        created_at=datetime.utcnow(),
        org_id=ticket.organization_id,
        tags=cast(ticket.tags, ARRAY(String)),
        ticket_type=ticket_type
    )
    await db.execute(stmt)
    await db.commit()