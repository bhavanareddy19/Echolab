from fastapi import APIRouter

from app.api.organization import router as organization_router
from app.api.user import router as user_router
from app.api.ticket import router as ticket_router
from app.api.ticket_testing import testing_router as ticket_testing_router
from app.api.b2b_saas_context import router as b2b_saas_context_router

api_router = APIRouter()
api_router.include_router(organization_router)
api_router.include_router(user_router)
api_router.include_router(ticket_router)
api_router.include_router(b2b_saas_context_router)
api_router.include_router(ticket_testing_router)
"""
API package: Contains FastAPI routers for each resource.
Defines endpoints for Organization, User, and Ticket CRUD operations.
"""
