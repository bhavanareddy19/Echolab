from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.organization import Organization, OrganizationCreate
from app.crud.organization import create_organization, get_organization
from app.db import get_db

router = APIRouter(tags=["organization"])


@router.post("/organizations/", response_model=Organization)
async def create(org: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    return await create_organization(db, org)


@router.get("/organizations/{org_id}", response_model=Organization)
async def read(org_id: int, db: AsyncSession = Depends(get_db)):
    return await get_organization(db, org_id)


"""
FastAPI router for Organization endpoints.
Defines API routes for CRUD operations on organizations.
"""
