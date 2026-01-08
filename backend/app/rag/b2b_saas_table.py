from supabase import create_client
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, select
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from pgvector.sqlalchemy import Vector  # Import Vector from pgvector
from sqlalchemy.sql import func
from dotenv import load_dotenv
from sqlalchemy import UniqueConstraint

load_dotenv()

# Supabase client setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Warning: Supabase client credentials not found.")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)

# SQLAlchemy async setup with pgbouncer compatibility
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

# Add connection arguments to disable statement caching for pgbouncer
engine = create_async_engine(
    SUPABASE_DB_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "application_name": "rag_app"
        }
    }
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


# Table model definition
class B2BSaasContextTable(Base):
    __tablename__ = "b2b_saas_context"

    id = Column(Integer, primary_key=True)
    url = Column(Text, nullable=False)
    title = Column(Text)
    chunk_order = Column(Integer, nullable=False, default=0)
    embedding = Column(Vector(1024))
    chunk_metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    __table_args__ = (
        UniqueConstraint("url", "chunk_order", name="_url_chunk_order_uc"),
    )


# Basic database operations (can be used by data.py)
async def get_all_records():
    """Fetch all records from the table"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(B2BSaasContextTable))
        return result.scalars().all()


async def create_record(data_dict):
    """Create a new record in the table"""
    async with AsyncSessionLocal() as session:
        new_record = B2BSaasContextTable(**data_dict)
        session.add(new_record)
        await session.commit()
        await session.refresh(new_record)
        return new_record


async def get_record_by_id(record_id):
    """Get a specific record by ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(B2BSaasContextTable).where(B2BSaasContextTable.id == record_id)
        )
        return result.scalar_one_or_none()


# Similarity search using Supabase RPC
def search_similar(embedding, limit=5):
    """Search for similar records using vector similarity"""
    if not supabase:
        raise ValueError("Supabase client not initialized.")

    response = supabase.rpc(
        "match_context", {"query_embedding": embedding, "match_count": limit}
    ).execute()
    return response.data
