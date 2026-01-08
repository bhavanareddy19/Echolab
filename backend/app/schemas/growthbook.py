# app/schemas/growthbook.py
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class GrowthBookExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class GrowthBookExperimentCreate(GrowthBookExperimentBase):
    hypothesis: str
    # [{"key": "control", "name": "Current", "weight": 0.5}, ...]
    variation_ranks: List[Dict[str, Any]]

class GrowthBookExperimentUpdate(GrowthBookExperimentBase):
    hypothesis: Optional[str] = None
    variation_ranks: Optional[List[Dict[str, Any]]] = None

class GrowthBookExperiment(GrowthBookExperimentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    growthbook_id: Optional[str] = None
    tracking_key: Optional[str] = None
    hypothesis: Optional[str] = None

    class Config:
        from_attributes = True
