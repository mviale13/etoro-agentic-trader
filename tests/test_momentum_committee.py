from typing import cast

from app.committee.momentum import MomentumCommittee
from app.domain.committee_context import CommitteeContext
from app.domain.finding import Finding
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_intelligence import MarketIntelligence
from app.domain.momentum_signal import MomentumSignal
from app.domain.portfolio_snapshot import PortfolioSnapshot


def context(
    signal: MomentumSignal,
) -> CommitteeContext:
    return CommitteeContext(
        intelligence=cast(MarketIntelligence, None),
        portfolio=cast(PortfolioSnapshot, None),
        policy=cast(InvestmentPolicy, None),
        momentum_signal=signal,
    )


def test_buy_vote_for_bullish_signal() -> None:
    opinion = MomentumCommittee().evaluate(
        context(
            MomentumSignal(
                trend="BULLISH",
                strength="STRONG",
                confidence=85,
                evidence=(Finding.favourable("Short-term momentum is positive."),),
            )
        )
    )

    assert opinion.vote == "BUY"
    assert opinion.confidence == 85


def test_sell_vote_for_bearish_signal() -> None:
    opinion = MomentumCommittee().evaluate(
        context(
            MomentumSignal(
                trend="BEARISH",
                strength="STRONG",
                confidence=85,
                evidence=(Finding.adverse("Short-term momentum is negative."),),
            )
        )
    )

    assert opinion.vote == "SELL"


def test_hold_vote_for_neutral_signal() -> None:
    opinion = MomentumCommittee().evaluate(
        context(
            MomentumSignal(
                trend="NEUTRAL",
                strength="WEAK",
                confidence=60,
                evidence=(Finding.neutral("No meaningful momentum is visible."),),
            )
        )
    )

    assert opinion.vote == "HOLD"


def test_hold_vote_for_unknown_signal() -> None:
    opinion = MomentumCommittee().evaluate(
        context(
            MomentumSignal(
                trend="UNKNOWN",
                strength="UNKNOWN",
                confidence=20,
                evidence=(Finding.neutral("Daily price change is unavailable."),),
            )
        )
    )

    assert opinion.vote == "HOLD"
