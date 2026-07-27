from fastapi import FastAPI

from app.api.routes.doctor import router as doctor_router
from app.api.routes.explanation import router as explanation_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.reflection import router as reflection_router
from app.api.routes.today import router as today_router

app = FastAPI(
    title="MOVRvest API",
    description="Explainable investment intelligence for eToro investors.",
    version="0.6.0",
)

app.include_router(today_router)
app.include_router(doctor_router)
app.include_router(explanation_router)
app.include_router(opportunities_router)
app.include_router(reflection_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "movrvest",
    }
