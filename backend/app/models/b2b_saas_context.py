from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy import UniqueConstraint
from pgvector.sqlalchemy import Vector

Base = declarative_base()

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
