from fastapi import APIRouter

from app.api.models.reflection import ReflectionResponse
from app.services.daily_reflection_service import DailyReflectionService

router = APIRouter(prefix="/reflection", tags=["reflection"])


@router.get("/", response_model=ReflectionResponse)
def get_reflection() -> ReflectionResponse:
    reflection = DailyReflectionService().today()

    return ReflectionResponse(
        title=reflection.title,
        message=reflection.message,
        source=reflection.source,
    )
