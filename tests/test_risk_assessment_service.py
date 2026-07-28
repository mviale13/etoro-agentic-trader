from datetime import UTC, datetime

from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.domain.portfolio_facts import (
    PortfolioFacts,
)
from app.services.risk_assessment_service import (
    RiskAssessmentService,
)


def test_high_vix_creates_high_risk() -> None:
    market = MarketFacts(
        instruments=(
            MarketFact(
                symbol="SPY",
                name="S&P 500",
                price=600,
                change_percent=0.4,
                source="Yahoo",
                as_of=datetime.now(UTC),
            ),
        ),
        vix=32,
        source="Yahoo",
        as_of=datetime.now(UTC),
    )

    portfolio = PortfolioFacts(
        total_value_usd=100000,
        total_value_eur=92000,
        cash_usd=95000,
        invested_usd=5000,
        unrealized_pnl_usd=0,
        cash_allocation=95,
        positions=1,
        pending_orders=0,
        copy_portfolios=0,
        connected=True,
        latency_ms=200,
        last_sync=datetime.now(UTC),
        source="eToro",
    )

    assessment = RiskAssessmentService().assess(
        portfolio,
        market,
    )

    assert assessment.market == "HIGH"
    assert assessment.overall == "HIGH"
