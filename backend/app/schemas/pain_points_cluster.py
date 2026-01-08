from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class PainPointClusterBuildRequest(BaseModel):
    org_id: Optional[int] = None
    min_cluster_size: int = 5
    top_k_examples: int = 5
    include_text_preview: bool = True

class PainPointClusterItem(BaseModel):
    id: int
    created_at: datetime
    body: Optional[str] = None
    hypothesis: Optional[dict] = None
    tickets: List[dict] = Field(default_factory=list)
    num_of_tickets: int
    status: str

class PainPointClusterList(BaseModel):
    items: List[PainPointClusterItem]
    total: int

class PainPointClusterDetail(PainPointClusterItem):
    pass

class PainPointHypothesisUpdate(BaseModel):
    hypothesis: dict

class PainPointStatusUpdate(BaseModel):
    status: str