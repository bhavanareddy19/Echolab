from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import traceback  
from app.db import get_db

from app.schemas.zendesk_sync import ZendeskSyncRequest
from app.services.zendesk_client import search_tickets
from app.services.ingest import insert_ticket_row

router = APIRouter()

@router.post("/integrations/zendesk/sync")
async def zendesk_sync(body: ZendeskSyncRequest, db: AsyncSession = Depends(get_db)):
    imported = 0
    start_iso = body.start_date.isoformat()
    end_iso = body.end_date.isoformat()
    try:
        async for t in search_tickets(start_iso, end_iso):
            created_dt = None
            if t.get("created_at"):
                created_dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            await insert_ticket_row(
                db=db,
                payload=t,
                created_at=created_dt,
                org_id=str(body.org_id),
                tags=t.get("tags") or [],
                ticket_type="unclassified",
            )
            imported += 1

        await db.commit()
        return {"imported": imported}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print("SYNC ERROR:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))