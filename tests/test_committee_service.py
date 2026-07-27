from pathlib import Path
from typing import Any, cast

from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.recommendation import Recommendation
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_service import CommitteeService


def test_logs_complete_committee_audit_event(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = CommitteeService(repository)

    opinions = (
        CommitteeOpinion(
            member="Momentum",
            vote="BUY",
            confidence=80,
            rationale="Positive momentum.",
        ),
        CommitteeOpinion(
            member="Risk",
            vote="HOLD",
            confidence=70,
            rationale="Volatility remains elevated.",
        ),
        CommitteeOpinion(
            member="Value",
            vote="BUY",
            confidence=90,
            rationale="Valuation is attractive.",
        ),
    )

    decision = CommitteeDecision(
        recommendation="BUY",
        confidence=80,
        buy_votes=2,
        hold_votes=1,
        sell_votes=0,
        opinions=opinions,
    )

    recommendation = Recommendation(
        symbol="MSFT",
        portfolio=cast(PortfolioSnapshot, cast(Any, object())),
        intelligence=cast(MarketIntelligence, cast(Any, object())),
        decision=decision,
    )

    service._log_recommendation(recommendation)

    events = repository.load_all()

    assert len(events) == 1

    event = events[0]

    assert event.event_type == "recommendation_generated"
    assert event.symbol == "MSFT"
    assert event.payload["recommendation"] == "BUY"
    assert event.payload["confidence"] == 80
    assert event.payload["buy_votes"] == 2
    assert event.payload["hold_votes"] == 1
    assert event.payload["sell_votes"] == 0
    assert event.payload["votes"] == [
        {
            "member": "Momentum",
            "vote": "BUY",
            "confidence": 80,
            "rationale": "Positive momentum.",
        },
        {
            "member": "Risk",
            "vote": "HOLD",
            "confidence": 70,
            "rationale": "Volatility remains elevated.",
        },
        {
            "member": "Value",
            "vote": "BUY",
            "confidence": 90,
            "rationale": "Valuation is attractive.",
        },
    ]
