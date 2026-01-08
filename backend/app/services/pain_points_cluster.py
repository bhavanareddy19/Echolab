from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func, update
from datetime import datetime
from app.models.pain_points_cluster import PainPointsCluster
from app.models.zendesk_ticket import ZendeskTicket

async def embed_texts(texts: List[str]) -> List[List[float]]:
    raise NotImplementedError

def cluster_embeddings(embeddings: List[List[float]], min_cluster_size: int = 5) -> Dict[int, Dict[str, Any]]:
    raise NotImplementedError

def _label_cluster(example_texts: List[str]) -> str:    return (example_texts[0][:80] if example_texts else "Cluster").replace("\n", " ").strip()

async def _fetch_corpus(db: AsyncSession, org_id: Optional[int]) -> List[Dict[str, Any]]:
    q = select(
        ZendeskTicket.json_payload["id"].as_integer().label("zd_id"),
        ZendeskTicket.json_payload["subject"].as_string().label("subject"),
        ZendeskTicket.json_payload["description"].as_string().label("desc"),
    )
    if org_id is not None:
        q = q.where(ZendeskTicket.org_id == str(org_id))

    rows = (await db.execute(q)).all()
    corpus = []
    for r in rows:
        text = ((r.subject or "") + " " + (r.desc or "")).strip()
        if text:
            corpus.append({"zendesk_ticket_id": int(r.zd_id), "subject": r.subject or "", "text": text})
    return corpus

async def build_and_persist_clusters(
    db: AsyncSession,
    *,
    org_id: Optional[int],
    min_cluster_size: int,
    top_k_examples: int,
    include_text_preview: bool,
) -> Dict[str, Any]:
    corpus = await _fetch_corpus(db, org_id)
    if not corpus:
        return {"created": 0}

    texts = [c["text"] for c in corpus]
    embeds = await embed_texts(texts)
    clusters = cluster_embeddings(embeds, min_cluster_size=min_cluster_size)

    created = 0
    for cid, info in clusters.items():
        if cid == -1:
            continue  # skip noise/outliers
        idxs: List[int] = info.get("indices", [])
        scores: List[Optional[float]] = info.get("scores", [None] * len(idxs))
        if not idxs:
            continue

        # Build tickets JSON payload (id + score + optional snippets)
        ticket_items: List[Dict[str, Any]] = []
        example_texts: List[str] = []
        for k, i in enumerate(idxs):
            item = {
                "zendesk_ticket_id": corpus[i]["zendesk_ticket_id"],
                "score": float(scores[k]) if k < len(scores) and scores[k] is not None else None,
            }
            if include_text_preview:
                item["subject"] = corpus[i]["subject"]
                item["preview"] = texts[i][:240]
            ticket_items.append(item)
            if len(example_texts) < top_k_examples:
                example_texts.append(texts[i])

        body = _label_cluster(example_texts)

        stmt = insert(PainPointsCluster).values(
            body=body,
            hypothesis=None,
            tickets=ticket_items,
            num_of_tickets=len(idxs),
            status="active",
        )
        await db.execute(stmt)
        created += 1

    await db.commit()
    return {"created": created}

async def list_clusters(db: AsyncSession, limit: int, offset: int) -> Tuple[List[PainPointsCluster], int]:
    total = (await db.execute(select(func.count()).select_from(PainPointsCluster))).scalar() or 0
    rows = (await db.execute(
        select(PainPointsCluster).order_by(PainPointsCluster.num_of_tickets.desc(), PainPointsCluster.id.desc())
        .offset(offset).limit(limit)
    )).scalars().all()
    return rows, total

async def get_cluster(db: AsyncSession, cluster_id: int) -> Optional[PainPointsCluster]:
    return await db.get(PainPointsCluster, cluster_id)

async def update_hypothesis(db: AsyncSession, cluster_id: int, hypothesis: Dict[str, Any]) -> bool:
    res = await db.execute(
        update(PainPointsCluster)
        .where(PainPointsCluster.id == cluster_id)
        .values(hypothesis=hypothesis)
    )
    await db.commit()
    return res.rowcount > 0

async def update_status(db: AsyncSession, cluster_id: int, status: str) -> bool:
    res = await db.execute(
        update(PainPointsCluster)
        .where(PainPointsCluster.id == cluster_id)
        .values(status=status)
    )
    await db.commit()
    return res.rowcount > 0