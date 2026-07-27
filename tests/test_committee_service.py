from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.recommendation import Recommendation
from app.domain.sentiment_snapshot import SentimentSnapshot
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

    intelligence = MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="positive",
            volatility="low",
            summary="Positive market conditions.",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=72,
            label="Greed",
            source="Test",
        ),
        outlook="BULLISH",
        confidence=90,
        summary="Market momentum and sentiment are aligned.",
    )

    recommendation = Recommendation(
        symbol="MSFT",
        portfolio=cast(PortfolioSnapshot, cast(Any, object())),
        intelligence=intelligence,
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
    assert event.payload["regime"] == "BULL"
    assert event.payload["regime_confidence"] == 90
    assert event.payload["buy_votes"] == 2
    assert event.payload["hold_votes"] == 1
    assert event.payload["sell_votes"] == 0
    assert event.payload["votes"] == [
        {
            "member": "Momentum",
            "vote": "BUY",
            "confidence": 80,
            "rationale": "Positive momentum.",
            "evidence": [],
        },
        {
            "member": "Risk",
            "vote": "HOLD",
            "confidence": 70,
            "rationale": "Volatility remains elevated.",
            "evidence": [],
        },
        {
            "member": "Value",
            "vote": "BUY",
            "confidence": 90,
            "rationale": "Valuation is attractive.",
            "evidence": [],
        },
    ]
