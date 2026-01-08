from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


async def create_organization(db: AsyncSession, org: OrganizationCreate):
    db_org = Organization(**org.dict())
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org


async def get_organization(db: AsyncSession, org_id: int):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalars().first()


"""
CRUD operations for Organization model.
Async functions for create, read, update, delete operations.
Used by API routers.
"""
