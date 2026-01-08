from app.crud.user import get_user
from app.prompt.prompt_Classification import classify_and_store
import sys
import os

# Fix the path to access your existing clustering script
from app.supabase_ingestion.cluster_tickets import process_existing_supabase_data

import httpx
from fastapi import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ticket import Ticket, TicketCreate
from app.crud.ticket import create_ticket, get_ticket
from app.schemas.zendesk_ticket import ZendeskTicketIn
from app.crud.zendesk_ticket import insert_zendesk_ticket
from app.db import get_db
from typing import List, Optional

router = APIRouter(tags=["ticket"])


@router.post(
    "/prod/tickets/zendesk/import",
    summary="Bulk Import All Zendesk Tickets",
    description="Fetches all tickets from the linked user's Zendesk account using the Zendesk API and stores them in the local tickets table. Use for initial import or periodic sync. This is a PULL operation initiated by your backend.",
)
async def import_zendesk_tickets(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user or not (
        user.zendesk_subdomain and user.zendesk_email and user.zendesk_api_token
    ):
        raise HTTPException(
            status_code=400, detail="User has not linked Zendesk account."
        )
    url = f"https://{user.zendesk_subdomain}.zendesk.com/api/v2/tickets.json"
    auth = (f"{user.zendesk_email}/token", user.zendesk_api_token)
    headers = {"Content-Type": "application/json"}
    imported = []
    async with httpx.AsyncClient() as client:
        response = await client.get(url, auth=auth, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        data = response.json()
        for ticket in data.get("tickets", []):
            # Map Zendesk fields to your TicketCreate schema as needed
            ticket_create = TicketCreate(
                url=ticket.get("url"),
                source="zendesk",
                created_at=ticket.get("created_at"),
                updated_at=ticket.get("updated_at"),
                type=ticket.get("type"),
                subject=ticket.get("subject"),
                description=ticket.get("description"),
                priority=ticket.get("priority"),
                status=ticket.get("status"),
                submitter_id=user.id,
                tags=",".join(ticket.get("tags", [])),
                rating=None,
                attachments=None,
                organization_id=user.organization_id,
                feature=None,
            )
            created = await create_ticket(db, ticket_create)
            imported.append(created)
    return {"imported": len(imported)}


# Production: Create Zendesk ticket using linked user credentials
@router.post("/prod/tickets/zendesk/create")
async def prod_create_ticket_zendesk(
    ticket: TicketCreate, user_id: str, db: AsyncSession = Depends(get_db)
):
    user = await get_user(db, user_id)
    if not user or not (
        user.zendesk_subdomain and user.zendesk_email and user.zendesk_api_token
    ):
        raise HTTPException(
            status_code=400, detail="User has not linked Zendesk account."
        )
    url = f"https://{user.zendesk_subdomain}.zendesk.com/api/v2/tickets.json"
    auth = (f"{user.zendesk_email}/token", user.zendesk_api_token)
    headers = {"Content-Type": "application/json"}
    payload = {
        "ticket": {
            "subject": ticket.subject or "No subject",
            "description": ticket.description or "No description",
            "priority": ticket.priority or "normal",
            "status": ticket.status or "open",
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, auth=auth, headers=headers)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()




# Production: Webhook Zendesk (bulk) using linked user credentials
@router.post("/prod/tickets/webhook/zendesk/bulk")
async def prod_webhook_zendesk_bulk(
    tickets: List[ZendeskTicketIn], user_id: str, db: AsyncSession = Depends(get_db)
):
    user = await get_user(db, user_id)
    if not user or not (
        user.zendesk_subdomain and user.zendesk_email and user.zendesk_api_token
    ):
        raise HTTPException(
            status_code=400, detail="User has not linked Zendesk account."
        )
    url = f"https://{user.zendesk_subdomain}.zendesk.com/api/v2/tickets.json"
    auth = (f"{user.zendesk_email}/token", user.zendesk_api_token)
    headers = {"Content-Type": "application/json"}
    results = []
    async with httpx.AsyncClient() as client:
        for ticket in tickets:
            payload = {
                "ticket": {
                    "subject": ticket.subject or "No subject",
                    "description": ticket.description or "No description",
                    "priority": ticket.priority or "normal",
                    "status": ticket.status or "open",
                }
            }
            response = await client.post(url, json=payload, auth=auth, headers=headers)
            if response.status_code == 201:
                results.append(response.json())
            else:
                results.append({"error": response.text})
    return {"results": results}


# add single ticket
@router.post(
    "/tickets/",
    response_model=Ticket,
    summary="Create single Ticket",
    description="Create a single ticket in the system.",
    tags=["ticket"],
)
async def create(ticket: TicketCreate, db: AsyncSession = Depends(get_db)):
    return await create_ticket(db, ticket)


# add multiple tickets at a time
@router.post(
    "/tickets/bulk/",
    response_model=List[Ticket],
    summary="Create Bulk Ticket",
    description="Create multiple tickets in a single request. Accepts a list of ticket objects and returns the created tickets.",
    tags=["ticket"],
)
async def create_bulk_tickets(
    tickets: List[TicketCreate], db: AsyncSession = Depends(get_db)
):
    created = []
    for ticket in tickets:
        created_ticket = await create_ticket(db, ticket)
        created.append(created_ticket)
    return created


@router.get(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    summary="Get Ticket by ID",
    description="Retrieve a ticket by its ID.",
    tags=["ticket"],
)
async def read(ticket_id: str, db: AsyncSession = Depends(get_db)):
    return await get_ticket(db, ticket_id)


@router.post(
    "/classification",
    summary="Classify and Cluster Tickets",
    description="Runs ticket classification and clustering on tickets for the specified organization.",
)
async def classification(
    organization_id: str,
    limit: Optional[int] = 50
):
    """
    Run ticket classification and clustering process.

    Args:
        organization_id: Organization ID to filter tickets
        limit: Maximum number of tickets to process

    Returns:
        Classification and clustering results
    """
    try:
        # Step 1: Run classification (sync function)
        classification_result = classify_and_store(
            limit=limit,
            batch_size=50, 
            sleep_between=2
        )
        
        # Step 2: Run clustering script - Remove await since it's likely not async
        # and add error handling for database connection issues
        try:
            clustering_result = await process_existing_supabase_data(
                organization_id=organization_id,
                limit=limit
            )
        except Exception as cluster_error:
            print(f"Clustering error: {cluster_error}")
            # Return classification results even if clustering fails
            clustering_result = {
                "error": "Clustering failed - database connection issue",
                "message": str(cluster_error),
                "organization_id": organization_id,
                "total_tickets": 0,
                "clusters": []
            }
        
        return {
            "organization_id": organization_id,
            "classification": classification_result,
            "clustering": clustering_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
