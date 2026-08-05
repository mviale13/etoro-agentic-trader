"""Read each holding's measured market exposure off the Brain."""

from __future__ import annotations

from app.brain.brain import Brain
from app.domain.holding_exposure import HoldingExposure
from app.domain.market_sensitivity import MarketSensitivity


def holding_exposures(brain: Brain) -> tuple[HoldingExposure, ...]:
    """
    One exposure per holding the broker reported, measured or not.

    Nothing here fetches and nothing here computes: the sensitivity was
    regressed during perception and stored on the security's evidence, and
    the weight is the snapshot's own arithmetic. A holding the Brain holds
    no security evidence for is still listed, with its sensitivity absent —
    the count of unmeasured holdings is what lets a feed line say honestly
    how much of the account it could not speak for.
    """

    portfolio = brain.portfolio

    return tuple(
        HoldingExposure(
            symbol=holding.symbol,
            weight_pct=portfolio.weight_pct(holding),
            sensitivity=_sensitivity_of(brain, holding.symbol),
        )
        for holding in portfolio.holdings
    )


def _sensitivity_of(brain: Brain, symbol: str) -> MarketSensitivity | None:
    """The measured sensitivity on this security's evidence, or nothing."""

    evidence = brain.security_evidence(symbol)

    if evidence is None:
        return None

    risk = evidence.signals.risk

    if risk is None:
        return None

    return risk.market_sensitivity
