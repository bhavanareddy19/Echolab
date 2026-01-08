from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_db

router = APIRouter()

SQL_RECENT = text("""
  select id, json_payload, org_id, tags, ticket_type, created_at
  from zendesk_tickets
  order by id desc
  limit :limit
""")

@router.get("/zendesk/tickets/recent")
async def recent_tickets(limit: int = 50, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(SQL_RECENT, {"limit": limit})).fetchall()
    return [
        {
            "id": r[0], "json_payload": r[1], "org_id": r[2],
            "tags": r[3], "ticket_type": r[4], "created_at": r[5]
        } for r in rows
    ]