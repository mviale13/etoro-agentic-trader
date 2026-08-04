from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.morning_brief_service import MorningBriefService


def build_portfolio(
    *,
    cash: float,
    positions: int,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            stocks=100 - cash,
            etfs=0,
            crypto=0,
            cash=cash,
            unclassified=0,
        ),
        total_value=100_000,
        positions=positions,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )


def test_high_cash_allocation_recommends_waiting():
    portfolio = build_portfolio(
        cash=100,
        positions=0,
    )

    brief = MorningBriefService().build(portfolio)

    assert brief.recommendation == "WAIT"
    assert brief.confidence == 95
    assert brief.portfolio_health == "Healthy"
    assert "mostly cash" in brief.summary


def test_invested_portfolio_recommends_review():
    portfolio = build_portfolio(
        cash=40,
        positions=5,
    )

    brief = MorningBriefService().build(portfolio)

    assert brief.recommendation == "REVIEW"
    assert brief.confidence == 80
    assert brief.portfolio_health == "Balanced"
    assert "invested assets" in brief.summary


def test_cash_threshold_is_inclusive():
    portfolio = build_portfolio(
        cash=80,
        positions=2,
    )

    brief = MorningBriefService().build(portfolio)

    assert brief.recommendation == "WAIT"
