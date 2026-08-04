from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.signal_service import SignalService


def build_portfolio(
    *,
    cash: float,
    positions: int,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=cash,
            stocks=0.0,
            etfs=0.0,
            crypto=0.0,
            unclassified=max(100.0 - cash, 0.0),
        ),
        total_value=100_000,
        positions=positions,
        largest_position=None,
        largest_position_pct=0.0,
        risk_flags=(),
    )


def test_high_cash_creates_signal() -> None:
    current = build_portfolio(cash=45.0, positions=10)

    signals = SignalService().analyze(
        current=current,
        previous=None,
    )

    assert any(signal.type == "cash" for signal in signals)


def test_few_positions_creates_concentration_signal() -> None:
    current = build_portfolio(cash=10.0, positions=4)

    signals = SignalService().analyze(
        current=current,
        previous=None,
    )

    assert any(signal.type == "concentration" for signal in signals)


def test_balanced_portfolio_creates_no_signal() -> None:
    current = build_portfolio(cash=20.0, positions=10)

    signals = SignalService().analyze(
        current=current,
        previous=None,
    )

    assert signals == []
