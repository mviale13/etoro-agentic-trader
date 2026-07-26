from fastapi import FastAPI

from app.api.routes.today import router as today_router

app = FastAPI(
    title="MOVRvest API",
    description="Explainable investment intelligence for eToro investors.",
    version="0.6.0",
)

app.include_router(today_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "movrvest",
    }
