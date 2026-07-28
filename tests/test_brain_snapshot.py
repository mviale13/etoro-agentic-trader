from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from app.domain.brain_snapshot import BrainSnapshot
from app.domain.insight import Insight
from app.domain.investor_dna import InvestorDNA
from app.domain.observation import Observation
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.recommendation import Recommendation


def test_brain_snapshot_is_immutable() -> None:
    insight = Insight(
        priority=100,
        category="portfolio",
        title="High Cash Allocation",
        message="Cash preserves flexibility.",
        evidence=[
            "Cash allocation: 100.0%",
            "Open positions: 0",
        ],
    )

    snapshot = BrainSnapshot(
        portfolio=cast(PortfolioSnapshot, cast(Any, object())),
        recommendation=cast(Recommendation, cast(Any, object())),
        observation=Observation(
            title="Steady Course",
            message="Portfolio remains balanced.",
            category="general",
        ),
        investor_dna=InvestorDNA(
            confidence=0,
            prefers_quality=False,
            prefers_diversification=False,
            prefers_value=False,
            avoids_high_volatility=False,
        ),
        summary="Steady Course. Investor understanding: 0%.",
        insights=[insight],
    )

    assert snapshot.observation.title == "Steady Course"
    assert snapshot.investor_dna.confidence == 0
    assert snapshot.insights[0].title == "High Cash Allocation"

    with pytest.raises(FrozenInstanceError):
        snapshot.summary = "Changed"
