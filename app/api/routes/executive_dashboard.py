from fastapi import APIRouter

from app.api.models.committee_statistics import (
    CommitteeStatisticsResponse,
)
from app.api.models.executive_dashboard import (
    ExecutiveDashboardResponse,
)
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)
from app.services.investor_dna_service import InvestorDNAService
from app.services.memory_service import MemoryService
from app.services.pattern_engine import PatternEngine

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/executive",
    response_model=ExecutiveDashboardResponse,
)
async def executive_dashboard() -> ExecutiveDashboardResponse:
    repository = JsonEventRepository()

    analytics = CommitteeAnalyticsService(repository)

    statistics = analytics.statistics()
    performance = analytics.performance()

    memories = MemoryService(repository).history()
    patterns = PatternEngine().analyze(memories)
    dna = InvestorDNAService().analyze(patterns)

    return ExecutiveDashboardResponse(
        committee=CommitteeStatisticsResponse(
            recommendations=statistics.recommendations,
            buy=statistics.buy,
            hold=statistics.hold,
            sell=statistics.sell,
            average_confidence=statistics.average_confidence,
        ),
        committee_accuracy=performance.accuracy,
        investor_understanding=dna.confidence,
    )
