from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas.pain_points_cluster import (
    PainPointClusterBuildRequest, PainPointClusterList, PainPointClusterItem,
    PainPointClusterDetail, PainPointHypothesisUpdate, PainPointStatusUpdate
)
from app.services.pain_points_cluster import (
    build_and_persist_clusters, list_clusters, get_cluster,
    update_hypothesis, update_status,
)

router = APIRouter(prefix="/painpoints", tags=["painpoints"])

@router.post("/cluster")
async def cluster_pain_points(req: PainPointClusterBuildRequest, db: AsyncSession = Depends(get_db)):
    """
    Build clusters from zendesk_tickets and persist into pain_points_cluster.
    """
    out = await build_and_persist_clusters(
        db,
        org_id=req.org_id,
        min_cluster_size=req.min_cluster_size,
        top_k_examples=req.top_k_examples,
        include_text_preview=req.include_text_preview,
    )
    return out

@router.get("", response_model=PainPointClusterList)
async def get_pain_points(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await list_clusters(db, limit=limit, offset=offset)
    items = [PainPointClusterItem(
        id=r.id,
        created_at=r.created_at,
        body=r.body,
        hypothesis=r.hypothesis,
        tickets=r.tickets or [],
        num_of_tickets=r.num_of_tickets,
        status=r.status,
    ) for r in rows]
    return PainPointClusterList(items=items, total=total)

@router.get("/{cluster_id}", response_model=PainPointClusterDetail)
async def get_pain_point(cluster_id: int, db: AsyncSession = Depends(get_db)):
    r = await get_cluster(db, cluster_id)
    if not r:
        raise HTTPException(404, "Pain point not found")
    return PainPointClusterDetail(
        id=r.id,
        created_at=r.created_at,
        body=r.body,
        hypothesis=r.hypothesis,
        tickets=r.tickets or [],
        num_of_tickets=r.num_of_tickets,
        status=r.status,
    )

@router.patch("/{cluster_id}/hypothesis")
async def patch_hypothesis(cluster_id: int, body: PainPointHypothesisUpdate, db: AsyncSession = Depends(get_db)):
    ok = await update_hypothesis(db, cluster_id, body.hypothesis)
    if not ok:
        raise HTTPException(404, "Pain point not found")
    return {"updated": True}

@router.patch("/{cluster_id}/status")
async def patch_status(cluster_id: int, body: PainPointStatusUpdate, db: AsyncSession = Depends(get_db)):
    ok = await update_status(db, cluster_id, body.status)
    if not ok:
        raise HTTPException(404, "Pain point not found")
    return {"updated": True}