"""The six adversarial specimens, pinned before the kernel is redesigned.

`EVIDENCE_DELETION_AUDIT.md` found that deleting an *adverse* signal
can manufacture a BUY: the vote is a weighted sum in which UNKNOWN
scores `0`, and `0` is strictly better than `−1`. Six live securities
exhibit it.

These tests state the invariant the owner set — *deleting their
established LOW-quality evidence must never make the platform tell an
investor a stronger positive story*.

They were marked `xfail(strict=True)` while the kernel scored UNKNOWN
as zero. `decision-authority@1` made them hold, the strictness failed
the suite for passing unexpectedly, and the markers came off — which
is exactly the handover the strictness existed to force. They are
ordinary regressions now, and the six names stay pinned.
"""

from __future__ import annotations

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.finding import Finding
from app.domain.quality_signal import QualitySignal
from app.services.company_committee_service import CompanyCommitteeService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService
from tests.conftest import admissible_market_cap

#: How positive an investor-facing recommendation is. Only the ordering
#: matters: a design may not move a specimen *up* this scale by being
#: told less.
POSITIVITY = {"SELL": -1, "HOLD": 0, "BUY": 1}

#: The six live securities the audit named, with the readings that
#: produce the pathology: value CHEAP, quality LOW, momentum BULLISH.
#: The figures are the shapes measured in the stored corpus, not
#: invented — each of these companies reads LOW because its earnings or
#: its dividend fails, while its forward P/E sits under the cheap band.
#: A measured dividend of zero stands where the stored record carried
#: no dividend field. The counterfactual below deletes an
#: **established** quality band, so all three factors must read —
#: since `quality-authority@1` a partial set abstains and there is no
#: established band left to delete. A company that pays nothing
#: genuinely reads 0.0, so this is the shape the live path produces
#: once the field is present, not a convenience.
SPECIMENS = (
    ("DIDIY", 14.47, 15_911_532_544.0, 0.0, 0.0),
    ("DV", 11.15, 2_027_261_952.0, 0.37, 0.0),
    ("LUNR", -328.0, 2_631_417_600.0, -0.87, 0.0),
    ("MSTR", 2.02, 38_426_419_200.0, -99.16, 0.0),
    ("ORSTED.CO", 14.44, 187_458_699_264.0, -2.4, 0.0),
    ("RIVN", -8.96, 23_165_769_728.0, 0.0, 0.0),
)


def _facts(
    symbol: str,
    forward_pe: float,
    market_cap: float,
    eps: float | None,
    dividend_yield: float | None,
) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol=symbol,
        name=symbol,
        asset_type="stock",
        exchange="4",
        forward_pe=forward_pe,
        market_cap=market_cap,
        # Admissible on purpose: these specimens are about the vote's
        # treatment of absence, not about `market-cap-input-eligibility`.
        # Leaving the magnitude inadmissible would change the quality
        # band for a second reason and hide the case under test.
        market_cap_magnitude=admissible_market_cap(market_cap),
        eps=eps,
        dividend_yield=dividend_yield,
        daily_change_pct=2.1,
    )


def _recommendation(facts: CompanyFacts, quality: QualitySignal | None = None) -> str:
    signals = CompanySignals(
        value=ValueSignalService().build(facts, AssetClass.STOCK),
        quality=quality or QualitySignalService().build(facts, AssetClass.STOCK),
        momentum=MomentumSignalService().build(facts),
        risk=RiskSignalService().build(facts),
    )

    return CompanyCommitteeService().evaluate(facts.symbol, signals).recommendation


DELETED_QUALITY = QualitySignal(
    quality="UNKNOWN",
    confidence=20,
    evidence=(Finding.neutral("Business quality was not established."),),
)


@pytest.mark.parametrize(
    ("symbol", "forward_pe", "market_cap", "eps", "dividend_yield"),
    SPECIMENS,
    ids=[specimen[0] for specimen in SPECIMENS],
)
def test_the_specimens_read_low_quality_and_hold(
    symbol: str,
    forward_pe: float,
    market_cap: float,
    eps: float | None,
    dividend_yield: float | None,
) -> None:
    """The baseline these specimens exist to protect.

    Not xfailed: this is today's correct behaviour and it must not
    drift while the kernel is redesigned. A design that changes the
    *baseline* recommendation for these six is making a different
    change from the one under discussion, and should say so here.
    """

    facts = _facts(symbol, forward_pe, market_cap, eps, dividend_yield)

    quality = QualitySignalService().build(facts, AssetClass.STOCK)

    # These carry an admissible magnitude, so all three factors read and
    # the band is authorised. LOW here is a judgement of the business —
    # which is what makes them the right specimens for the deletion
    # counterfactual below.
    assert quality.quality == "LOW"
    assert quality.available == 3
    assert _recommendation(facts) == "HOLD"


@pytest.mark.parametrize(
    ("symbol", "forward_pe", "market_cap", "eps", "dividend_yield"),
    SPECIMENS,
    ids=[specimen[0] for specimen in SPECIMENS],
)
def test_forgetting_low_quality_never_tells_a_stronger_positive_story(
    symbol: str,
    forward_pe: float,
    market_cap: float,
    eps: float | None,
    dividend_yield: float | None,
) -> None:
    """The owner's invariant, now an ordinary regression.

    Deleting *established* adverse evidence — a quality band the
    platform genuinely read as LOW — must never move the
    investor-facing recommendation up the positivity scale.

    These were `xfail(strict=True)` while the kernel scored UNKNOWN as
    zero. `decision-authority@1` made them pass, the strictness failed
    the suite for passing unexpectedly, and the marker came off here —
    which is the handover the strictness existed to force.
    """

    facts = _facts(symbol, forward_pe, market_cap, eps, dividend_yield)

    before = _recommendation(facts)
    after = _recommendation(facts, quality=DELETED_QUALITY)

    assert POSITIVITY[after] <= POSITIVITY[before], (
        f"{symbol}: forgetting an established LOW quality moved the "
        f"recommendation {before} -> {after}"
    )
