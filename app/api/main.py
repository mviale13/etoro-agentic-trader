from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.brain import router as brain_router
from app.api.routes.committee import router as committee_router
from app.api.routes.committee_matrix import router as committee_matrix_router
from app.api.routes.committee_weights import (
    router as committee_weights_router,
)
from app.api.routes.crypto_dossier import router as crypto_dossier_router
from app.api.routes.cycle import router as cycle_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.doctor import router as doctor_router
from app.api.routes.executive import router as executive_router
from app.api.routes.executive_dashboard import (
    router as executive_dashboard_router,
)
from app.api.routes.explanation import router as explanation_router
from app.api.routes.home import router as home_router
from app.api.routes.investor_dna import router as investor_dna_router
from app.api.routes.market import router as market_router
from app.api.routes.observation import router as observation_router
from app.api.routes.personal_news import router as personal_news_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.portfolio_health import (
    router as portfolio_health_router,
)
from app.api.routes.recommendation import (
    router as recommendation_router,
)
from app.api.routes.recommendation_timeline import (
    router as recommendation_timeline_router,
)
from app.api.routes.reflection import router as reflection_router
from app.api.routes.research import router as research_router
from app.api.routes.strategy import router as strategy_router
from app.api.routes.today import router as today_router
from app.api.routes.track_record import router as track_record_router

app = FastAPI(
    title="MOVRvest API",
    description="Explainable investment intelligence for eToro investors.",
    version="0.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategy_router)
app.include_router(today_router)
app.include_router(doctor_router)
app.include_router(explanation_router)
app.include_router(research_router)
app.include_router(reflection_router)
app.include_router(recommendation_timeline_router)
app.include_router(portfolio_health_router)
app.include_router(investor_dna_router)
app.include_router(portfolio_router)
app.include_router(observation_router)
app.include_router(committee_router)
app.include_router(committee_matrix_router)
app.include_router(crypto_dossier_router)
app.include_router(personal_news_router)
app.include_router(cycle_router)
app.include_router(dashboard_router)
app.include_router(executive_dashboard_router)
app.include_router(executive_router)
app.include_router(recommendation_router)
app.include_router(committee_weights_router)
app.include_router(home_router)
app.include_router(track_record_router)
app.include_router(brain_router)
app.include_router(market_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "movrvest",
    }
