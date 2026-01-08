from fastapi import FastAPI
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
)
from fastapi import FastAPI
from app.api import api_router
from fastapi import FastAPI
from app.api import api_router
from app.db import engine, Base
from app.api.ticket_read import router as ticket_read_router
from app.api.zendesk_sync import router as zendesk_sync_router
from app.api.pain_points import router as pain_points_router
from app.api import b2b_saas_context, growthbook

import app.models
import asyncio

app = FastAPI()


# @app.on_event("startup")
# async def startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


# Include routers
app.include_router(api_router)
app.include_router(ticket_read_router, tags=["tickets"])
app.include_router(zendesk_sync_router, tags=["zendesk"])
app.include_router(pain_points_router, tags=["painpoints"])
app.include_router(b2b_saas_context.router)
app.include_router(growthbook.router)

@app.get("/")
def root():
    return {"message": "API is running and tables are created if not exist."}
    attachments = Column(String, nullable=True)


"""
FastAPI application entry point.
Includes routers, startup event for table creation, and model registration.
"""
