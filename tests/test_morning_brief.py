from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.morning_brief_service import MorningBriefService


def test_empty_portfolio_generates_wait_recommendation():
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=100,
            stocks=0,
            etfs=0,
            crypto=0,
            unclassified=0,
        ),
        total_value=100000,
        positions=0,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=("Cash concentration",),
    )

    brief = MorningBriefService().build(portfolio)

    assert brief.recommendation == "WAIT"
    assert brief.confidence == 95
    assert brief.portfolio_health == "Healthy"
