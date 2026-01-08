# tests/manual_gb_create.py
import os
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from app.schemas.growthbook import GrowthBookExperimentCreate
from app.growthbook.growthbook import create_growthbook_experiment

load_dotenv()

router = APIRouter(prefix="/growthbook", tags=["growthbook"])

# ---------------------- Pydantic Models ----------------------

class CreateExperimentRequest(BaseModel):
    experiment: GrowthBookExperimentCreate
    project_id: str
    datasource_id: str
    assignment_query_id: str
    hash_attribute: Optional[str] = "id"

class CreateExperimentResponse(BaseModel):
    success: bool
    tracking_key: str
    experiment_id: str
    variation_key_to_id: Dict[str, str]
    growthbook_response: Dict[str, Any]
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# ---------------------- Routes ----------------------

@router.post("/experiments", response_model=CreateExperimentResponse)
async def create_experiment(request: CreateExperimentRequest):
    """
    Create a new GrowthBook experiment.
    
    Requires:
    - experiment: Complete experiment configuration with hypothesis and variations
    - project_id: GrowthBook project ID
    - datasource_id: GrowthBook datasource ID  
    - assignment_query_id: GrowthBook assignment query/table ID
    - hash_attribute: User attribute for hashing (default: "id")
    """
    
    # Get API key from environment
    api_key = os.getenv("GROWTHBOOK_PAT")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GROWTHBOOK_PAT environment variable not set"
        )
    
    try:
        # Validate experiment data
        if not request.experiment.variation_ranks:
            raise HTTPException(
                status_code=400,
                detail="Experiment must have at least one variation"
            )
        
        # Validate weights sum to 1.0 (approximately)
        total_weight = sum(v.get("weight", 0) for v in request.experiment.variation_ranks)
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Variation weights must sum to 1.0, got {total_weight}"
            )
        
        # Create the experiment
        result = await create_growthbook_experiment(
            experiment=request.experiment,
            api_key=api_key,
            project_id=request.project_id,
            datasource_id=request.datasource_id,
            assignment_query_id=request.assignment_query_id,
            hash_attribute=request.hash_attribute
        )
        
        return CreateExperimentResponse(
            success=True,
            tracking_key=result["trackingKey"],
            experiment_id=result["experimentId"],
            variation_key_to_id=result["variation_key_to_id"],
            growthbook_response=result["growthbook_response"],
            message="Experiment created successfully"
        )
        
    except HTTPException:
        # Re-raise FastAPI HTTPExceptions
        raise
    except Exception as e:
        # Handle any other errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create GrowthBook experiment: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Simple health check for the GrowthBook service."""
    api_key = os.getenv("GROWTHBOOK_PAT")
    return {
        "status": "healthy",
        "api_key_configured": bool(api_key),
        "service": "growthbook"
    }

# Example request body for documentation
@router.get("/example-request")
async def get_example_request():
    """Get an example request body for creating an experiment."""
    return {
        "experiment": {
            "name": "Checkout Form Optimization",
            "description": "Test shorter checkout form to improve conversion",
            "tags": ["checkout", "conversion", "form"],
            "hypothesis": "If we simplify the checkout form, then conversion rate will improve because users say the current form is too long",
            "variation_ranks": [
                {"key": "control", "name": "Original Form", "weight": 0.5},
                {"key": "variant_a", "name": "Simplified Form", "weight": 0.5}
            ]
        },
        "project_id": "prj_your_project_id",
        "datasource_id": "ds_your_datasource_id", 
        "assignment_query_id": "tbl_your_table_id",
        "hash_attribute": "id"
    }

async def example_usage():
    variation_ranks = [
        {"key": "control",   "name": "Current",       "weight": 0.5},
        {"key": "variant_a", "name": "Shorter form",  "weight": 0.5},
    ]
    exp = GrowthBookExperimentCreate(
        name="Shorter checkout form",
        description="Test a shorter checkout form to improve conversion rates.",
        tags=["checkout", "form", "A/B test"],
        hypothesis="Shorter checkout form increases purchase completion.",
        variation_ranks=variation_ranks,
    )

    api_key = os.getenv("GROWTHBOOK_PAT")
    if not api_key:
        raise RuntimeError("Set GROWTHBOOK_PAT in your environment")

    result = await create_growthbook_experiment(
        experiment=exp,
        api_key=api_key,
        project_id="prj_org_19g621melrgi0s_demo-datasource-project",
        datasource_id="ds_19g623memi9uu7",
        assignment_query_id="tbl_memif5dh",
        hash_attribute="id",
    )
    print(result)




if __name__ == "__main__":
    asyncio.run(example_usage())
