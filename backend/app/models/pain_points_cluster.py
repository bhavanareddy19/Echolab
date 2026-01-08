from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db import Base

class PainPointsCluster(Base):
    __tablename__ = "pain_points_cluster"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    body = Column(Text, nullable=True)
    hypothesis = Column(JSONB, nullable=True) 
    tickets = Column(JSONB, nullable=False, default=list)
    num_of_tickets = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active") 