import os, httpx
from typing import AsyncIterator, Dict, Any
from urllib.parse import urlencode

def _base_url() -> str:
    sub = os.getenv("ZENDESK_SUBDOMAIN")
    if not sub:
        raise RuntimeError("ZENDESK_SUBDOMAIN not set")
    return f"https://{sub}.zendesk.com"

def _auth():
    email = os.getenv("ZENDESK_EMAIL")
    token = os.getenv("ZENDESK_API_TOKEN")
    if not email or not token:
        raise RuntimeError("ZENDESK_EMAIL or ZENDESK_API_TOKEN not set")
    return (f"{email}/token", token)

async def search_tickets(start_iso: str, end_iso: str) -> AsyncIterator[Dict[str, Any]]:
    """
    Uses Zendesk Search API with created date range.
    Yields ticket dicts across pages.
    """
    base = _base_url()
    auth = _auth()
    query = f"type:ticket created>={start_iso} created<={end_iso}"
    url = f"{base}/api/v2/search.json?{urlencode({'query': query})}"

    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            r = await client.get(url, auth=auth)
            r.raise_for_status()
            data = r.json()
            for item in data.get("results", []):
                if item.get("result_type") == "ticket":
                    yield item
            url = data.get("next_page")