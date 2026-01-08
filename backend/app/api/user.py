from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import User, UserCreate, ZendeskCredentialsIn
from app.crud.user import create_user, get_user, set_zendesk_credentials
from app.db import get_db
from fastapi import HTTPException


router = APIRouter(tags=["user"])


# Route to link Zendesk account
@router.post("/users/{user_id}/zendesk/link")
async def link_zendesk_account(
    user_id: str, creds: ZendeskCredentialsIn, db: AsyncSession = Depends(get_db)
):
    user = await set_zendesk_credentials(db, user_id, creds)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Zendesk account linked"}


@router.post("/users/", response_model=User)
async def create(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user)


@router.get("/users/{user_id}", response_model=User)
async def read(user_id: str, db: AsyncSession = Depends(get_db)):
    return await get_user(db, user_id)


"""
FastAPI router for User endpoints.
Defines API routes for CRUD operations on users.
"""
