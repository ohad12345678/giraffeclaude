from fastapi import APIRouter
from .auth import router as auth_router
from .checks import router as checks_router
from .dashboard import router as dashboard_router

# Create main v1 router
v1_router = APIRouter(prefix="/v1")

# Include all sub-routers
v1_router.include_router(auth_router)
v1_router.include_router(checks_router)
v1_router.include_router(dashboard_router)

__all__ = ["v1_router"]
