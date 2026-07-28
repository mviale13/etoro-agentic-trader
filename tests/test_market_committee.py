from datetime import UTC, datetime

from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.services.committees.market_committee import (
    MarketCommittee,
)

NOW = datetime.now(UTC)


def fact(
    symbol: str,
    change_percent: float,
) -> MarketFact:
    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        source="test",
        as_of=NOW,
    )


def test_votes_buy_when_breadth_is_positive() -> None:
    facts = MarketFacts(
        instruments=(
            fact("SPY", 0.8),
            fact("QQQ", 1.2),
            fact("IWM", 0.4),
        ),
        vix=15.0,
        source="test",
        as_of=NOW,
    )

    vote = MarketCommittee().vote(facts)

    assert vote.recommendation == "BUY"
    assert vote.confidence == 80
    assert "SPY: +0.80%" in vote.evidence
    assert "VIX: 15.00" in vote.evidence


def test_votes_wait_when_market_is_stressed() -> None:
    facts = MarketFacts(
        instruments=(
            fact("SPY", -1.0),
            fact("QQQ", -1.5),
            fact("IWM", -0.7),
        ),
        vix=30.0,
        source="test",
        as_of=NOW,
    )

    vote = MarketCommittee().vote(facts)

    assert vote.recommendation == "WAIT"
    assert vote.confidence == 85


def test_votes_hold_when_evidence_is_mixed() -> None:
    facts = MarketFacts(
        instruments=(
            fact("SPY", 0.4),
            fact("QQQ", -0.2),
            fact("IWM", 0.0),
        ),
        vix=21.0,
        source="test",
        as_of=NOW,
    )

    vote = MarketCommittee().vote(facts)

    assert vote.recommendation == "HOLD"
