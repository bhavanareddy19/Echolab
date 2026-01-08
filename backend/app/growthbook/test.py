# tests/manual_gb_create.py
import os
import asyncio
from dotenv import load_dotenv

from app.schemas.growthbook import GrowthBookExperimentCreate
from app.growthbook.growthbook import create_growthbook_experiment

load_dotenv()

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
