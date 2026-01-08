from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate


async def set_zendesk_credentials(db: AsyncSession, user_id, creds):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None
    user.zendesk_subdomain = creds.subdomain
    user.zendesk_email = creds.email
    user.zendesk_api_token = creds.api_token
    await db.commit()
    await db.refresh(user)
    return user


async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user(db: AsyncSession, user_id):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


"""
CRUD operations for User model.
Async functions for create, read, update, delete operations.
Used by API routers.
"""
