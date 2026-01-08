from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TEXT
from datetime import datetime
from typing import Optional, List, Dict, Any

INSERT_SQL = (
    text("""
      insert into zendesk_tickets (json_payload, created_at, org_id, tags, ticket_type)
      values (:json_payload, :created_at, :org_id, :tags, :ticket_type)
    """)
    .bindparams(
        bindparam("json_payload", type_=JSONB),
        bindparam("created_at"),
        bindparam("org_id"),
        bindparam("tags", type_=ARRAY(TEXT())),
        bindparam("ticket_type"),
    )
)

async def insert_ticket_row(
    db: AsyncSession,
    payload: Dict[str, Any],
    created_at: Optional[datetime],
    org_id: str,
    tags: Optional[List[str]],
    ticket_type: str = "unclassified",
):
    await db.execute(
        INSERT_SQL,
        {
            "json_payload": payload,
            "created_at": created_at or datetime.utcnow(),
            "org_id": org_id,
            "tags": tags or [],
            "ticket_type": ticket_type,
        },
    )