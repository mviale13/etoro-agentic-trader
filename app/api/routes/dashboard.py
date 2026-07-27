from fastapi import APIRouter

from app.api.models.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/", response_model=DashboardResponse)
async def get_dashboard() -> DashboardResponse:
    return await DashboardService().build()
