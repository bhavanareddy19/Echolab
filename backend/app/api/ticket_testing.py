from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.zendesk_ticket import ZendeskTicketIn
from app.crud.zendesk_ticket import insert_zendesk_ticket
from app.schemas.ticket import TicketCreate
import os
import httpx
from app.db import get_db
from typing import List

# TESTING ROUTES (for demo/testing purposes only)
testing_router = APIRouter(tags=["testing"])


@testing_router.post(
    "/tickets/webhook/zendesk",
    summary="[TEST] Webhook Zendesk (single)",
    description="[TEST] Accept a single Zendesk ticket via webhook. This route is for testing only.",
)
async def webhook_zendesk(ticket: ZendeskTicketIn, db: AsyncSession = Depends(get_db)):
    ticket_type = "unclassified"  #  no AI model yet for zendesk classifcation
    await insert_zendesk_ticket(db, ticket, ticket_type)
    return {"message": "Zendesk ticket received", "ticket_type": ticket_type}


@testing_router.post(
    "/tickets/webhook/zendesk/bulk",
    summary="[TEST] Webhook Zendesk (bulk)",
    description="[TEST] Accept multiple Zendesk tickets via webhook. This route is for testing only.",
)
async def webhook_zendesk_bulk(
    tickets: List[ZendeskTicketIn], db: AsyncSession = Depends(get_db)
):
    ticket_type = "unclassified"  # no AI model yet for zendesk classification
    for ticket in tickets:
        await insert_zendesk_ticket(db, ticket, ticket_type)
    return {
        "message": f"{len(tickets)} Zendesk tickets received",
        "ticket_type": ticket_type,
    }


@testing_router.post(
    "/tickets/zendesk/create",
    summary="[TEST] Create Ticket Zendesk",
    description="[TEST] Create a ticket in Zendesk using static environment credentials. This route is for testing only.",
)
async def create_ticket_zendesk(ticket: TicketCreate):
    """
    [TEST] Create a ticket in Zendesk using the Zendesk API.
    Requires ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN in environment.
    """
    subdomain = os.getenv("ZENDESK_SUBDOMAIN")
    email = os.getenv("ZENDESK_EMAIL")
    api_token = os.getenv("ZENDESK_API_TOKEN")
    if not all([subdomain, email, api_token]):
        raise HTTPException(
            status_code=500, detail="Zendesk credentials not set in environment."
        )

    url = f"https://{subdomain}.zendesk.com/api/v2/tickets.json"
    auth = (f"{email}/token", api_token)
    headers = {"Content-Type": "application/json"}
    payload = {
        "ticket": {
            "subject": ticket.subject or "No subject",
            "description": ticket.description or "No description",
            "priority": ticket.priority or "normal",
            "status": ticket.status or "open",
            # Add more fields as needed
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, auth=auth, headers=headers)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
