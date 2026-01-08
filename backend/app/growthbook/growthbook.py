# app/growthbook/growthbook.py
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import httpx
from dotenv import load_dotenv
from app.schemas.growthbook import GrowthBookExperimentCreate

load_dotenv()

GROWTHBOOK_BASE = os.getenv("GROWTHBOOK_BASE_URL", "https://api.growthbook.io/api/v1")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)

def _normalize_weights(variation_ranks: List[Dict[str, Any]]) -> List[float]:
    try:
        weights = [float(v.get("weight")) for v in variation_ranks]
    except Exception:
        return [1.0 / len(variation_ranks)] * len(variation_ranks)
    if any(w is None for w in weights):
        return [1.0 / len(variation_ranks)] * len(variation_ranks)
    total = sum(w for w in weights if isinstance(w, (int, float)))
    if total <= 0:
        return [1.0 / len(variation_ranks)] * len(variation_ranks)
    return [w / total for w in weights]

def _extract_experiment_object(payload: Any) -> Optional[Dict[str, Any]]:
    """
    Accepts several possible response shapes:
      {id: ..., variations: [...]}                  -> return as-is
      {experiment: {...}}                           -> return inner
      {data: {...}}                                 -> return inner
    """
    if not isinstance(payload, dict):
        return None
    if "id" in payload and "variations" in payload:
        return payload
    if isinstance(payload.get("experiment"), dict):
        return payload["experiment"]
    if isinstance(payload.get("data"), dict):
        return payload["data"]
    return None

async def _find_experiment_by_tracking_key(client: httpx.AsyncClient, api_key: str, tracking_key: str) -> Optional[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {api_key}"}
    limit, offset = 100, 0
    while True:
        resp = await client.get(f"{GROWTHBOOK_BASE}/experiments?limit={limit}&offset={offset}", headers=headers)
        if not resp.is_success:
            raise RuntimeError(f"List experiments failed: {resp.status_code} {resp.text}")
        data = resp.json() or {}
        for exp in data.get("experiments", []):
            if exp.get("trackingKey") == tracking_key:
                return exp
        if not data.get("hasMore") or data.get("nextOffset") is None:
            return None
        offset = data["nextOffset"]

async def create_growthbook_experiment(
    *,
    experiment: GrowthBookExperimentCreate,
    api_key: str,
    project_id: str,
    datasource_id: str,
    assignment_query_id: str,
    hash_attribute: str = "id",
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Option 1: always-unique trackingKey (append 6-char suffix).
    Create -> map returned variationIds -> update trafficSplit.
    Robust to differing API response envelopes.
    """
    base = base_url or GROWTHBOOK_BASE
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # unique tracking key to avoid 400 'already exists'
    slug = _slugify(experiment.name)
    tracking_key = f"exp-{slug}-{uuid.uuid4().hex[:6]}"

    payload_create: Dict[str, Any] = {
        "trackingKey": tracking_key,
        "name": experiment.name,
        "type": "standard",
        "project": project_id,
        "hypothesis": experiment.hypothesis,
        "status": "draft",
        "hashAttribute": hash_attribute,
        "datasourceId": datasource_id,
        "assignmentQueryId": assignment_query_id,
        "tags": experiment.tags or [],
        "variations": [{"key": v["key"], "name": v["name"]} for v in experiment.variation_ranks],
        "phases": [{
            "name": "Main",
            "dateStarted": _utc_now_iso(),
            "coverage": 1,
            "targetingCondition": ""  # empty = all users
        }],
        "statsEngine": "bayesian",
        "attributionModel": "firstExposure",
        "inProgressConversions": "loose",
        "autoRefresh": False,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: create
        r = await client.post(f"{base}/experiments", headers=headers, json=payload_create)
        if not r.is_success:
            raise RuntimeError(f"Create failed: {r.status_code} {r.text}")
        created_raw = r.json()
        created = _extract_experiment_object(created_raw)

        # fallback: locate by trackingKey if no id in response
        if not created or "id" not in created:
            located = await _find_experiment_by_tracking_key(client, api_key, tracking_key)
            if not located:
                raise RuntimeError(
                    "Experiment created but response missing 'id', and lookup by trackingKey failed. "
                    f"Raw response: {created_raw}"
                )
            created = located

        exp_id = created["id"]

        # Map key -> variationId
        key_to_varid = {v["key"]: v["variationId"] for v in (created.get("variations") or []) if "key" in v and "variationId" in v}
        if len(key_to_varid) != len(experiment.variation_ranks):
            # fetch fresh copy (some responses omit variationId on create)
            gr = await client.get(f"{base}/experiments/{exp_id}", headers=headers)
            if not gr.is_success:
                raise RuntimeError(f"Fetch after create failed: {gr.status_code} {gr.text}")
            fresh = _extract_experiment_object(gr.json()) or gr.json()
            key_to_varid = {v["key"]: v["variationId"] for v in (fresh.get("variations") or []) if "key" in v and "variationId" in v}

        # Step 2: update traffic split (optional but recommended)
        weights = _normalize_weights(experiment.variation_ranks)
        traffic_split = [{"variationId": key_to_varid[v["key"]], "weight": w}
                         for v, w in zip(experiment.variation_ranks, weights)]

        phases0 = (created.get("phases") or [{}])[0]
        payload_update = {
            "phases": [{
                "name": phases0.get("name", "Main"),
                "dateStarted": phases0.get("dateStarted", _utc_now_iso()),
                "coverage": 1,
                "trafficSplit": traffic_split,
                "targetingCondition": phases0.get("targetingCondition", "")
            }]
        }
        ur = await client.post(f"{base}/experiments/{exp_id}", headers=headers, json=payload_update)
        if not ur.is_success:
            raise RuntimeError(f"Update split failed: {ur.status_code} {ur.text}")
        updated_raw = ur.json()
        updated = _extract_experiment_object(updated_raw) or updated_raw

    return {
        "trackingKey": tracking_key,
        "experimentId": updated["id"],
        "variation_key_to_id": key_to_varid,
        "growthbook_response": updated,
    }
