from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot


def test_empty_portfolio():

    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=100,
            stocks=0,
            etfs=0,
            crypto=0,
        ),
        total_value=100000,
        positions=0,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=["Cash concentration"],
    )

    assert portfolio.positions == 0
    assert portfolio.allocation.cash == 100
    assert "Cash concentration" in portfolio.risk_flags