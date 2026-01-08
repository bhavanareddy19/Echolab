from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

Base = declarative_base()

#DATABASE_URL = "postgresql+asyncpg://postgres:password@db.jdmxaatlrkfyfhlfenxs.supabase.co:5432/postgres"
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
engine = create_async_engine(
    DATABASE_URL, echo=True, future=True, connect_args={"statement_cache_size": 0}
)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db():
    async with SessionLocal() as session:
        yield session


"""
Database configuration and session management.
Defines async SQLAlchemy engine, session, and shared Base for models.
"""
