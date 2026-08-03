from typing import cast

from app.committee.value import ValueCommittee
from app.domain.committee_context import CommitteeContext
from app.domain.finding import Finding
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.value_signal import ValueSignal


def context(
    pe: float | None = None,
    *,
    signal: ValueSignal | None = None,
) -> CommitteeContext:
    return CommitteeContext(
        intelligence=cast(MarketIntelligence, None),
        portfolio=cast(PortfolioSnapshot, None),
        policy=cast(InvestmentPolicy, None),
        valuation=ValuationSnapshot(
            forward_pe=pe,
            trailing_pe=pe,
            peg_ratio=1.2,
            dividend_yield=0.01,
        ),
        value_signal=signal,
    )


def test_buy_when_value_signal_is_cheap() -> None:
    opinion = ValueCommittee().evaluate(
        context(
            signal=ValueSignal(
                valuation="CHEAP",
                confidence=90,
                evidence=(Finding.favourable("Forward P/E is attractive."),),
            )
        )
    )

    assert opinion.vote == "BUY"
    assert opinion.confidence == 90


def test_hold_when_value_signal_is_fair() -> None:
    opinion = ValueCommittee().evaluate(
        context(
            signal=ValueSignal(
                valuation="FAIR",
                confidence=80,
                evidence=(Finding.neutral("Forward P/E is reasonable."),),
            )
        )
    )

    assert opinion.vote == "HOLD"


def test_hold_when_value_signal_is_expensive() -> None:
    opinion = ValueCommittee().evaluate(
        context(
            signal=ValueSignal(
                valuation="EXPENSIVE",
                confidence=85,
                evidence=(Finding.adverse("Forward P/E is elevated."),),
            )
        )
    )

    assert opinion.vote == "HOLD"


def test_legacy_valuation_remains_supported() -> None:
    opinion = ValueCommittee().evaluate(
        context(15),
    )

    assert opinion.vote == "BUY"
