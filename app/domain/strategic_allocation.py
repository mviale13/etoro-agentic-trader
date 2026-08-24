"""The investor's strategic allocation, and what being away from it means.

The owner's policy of 2026-08-24 draws three distinctions this platform
did not have, and the whole module exists to keep them apart:

- **A strategic target is a destination, not a gate.** 25% cash is where
  the account is heading, not a floor under every deployment.
- **An operating range permits tactical flexibility.** Sitting outside a
  target but inside its range is a normal state, not a breach.
- **A hard limit is the only allocation boundary that blocks an
  action** — and it has exactly one author. The active policy states
  the minimum cash and the maximum crypto; this module holds neither
  as a constant and receives both as `HardLimits`, so the boundary the
  CIO quotes is the boundary the Capital Action Envelope funds
  against. A copy here would let one owner edit move the envelope and
  leave the guidance quoting the old figure, with nothing able to see
  the disagreement.

The failure this replaces made all three one thing. `target_cash_pct`
was 5 beside `minimum_cash_pct` 40 — two incompatible statements — and
the capital envelope funded from `max(target, minimum)`, which turned
whichever number happened to be larger into a hard floor. Meanwhile the
three non-cash targets were **hardcoded to zero** in the policy mapper,
so the strategy page showed 0/0/0/5 and totalled 5%.

**Nothing here authorizes a trade.** An allocation standing is
guidance: it says where the account sits against the investor's own
plan and what that permits, and it can neither manufacture an OPEN, ADD
or REDUCE course for a security nor size one. Courses come from the
canonical decision path, and only from there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

#: How far the four targets may sum from 100 and still be accepted.
#: An arithmetic tolerance for decimal input, not a licence to state a
#: plan that does not add up.
TOTAL_TOLERANCE = 0.01

#: What each asset class is called in a sentence. "etfs" is a field
#: name; "ETFs" is what an investor reads.
ASSET_LABELS = {
    "stocks": "stocks",
    "etfs": "ETFs",
    "crypto": "crypto",
    "cash": "cash",
}


@dataclass(frozen=True, slots=True)
class HardLimits:
    """The two allocation limits that block an action, as policy states them.

    **These were module constants — 15.0 and 40.0 — and that was a
    second authority.** The active strategy file already states a
    minimum cash and a maximum crypto, and the Capital Action Envelope
    funds against *those*; a copy here meant one owner edit could move
    the envelope's floor and leave the CIO's guidance quoting the old
    number, with nothing in the code able to see the disagreement.

    So the limits arrive from the same validated reading the envelope
    uses and are never defaulted: this object has no fallback values,
    and `StrategicAllocation` requires one, so no production path can
    reach a hard limit this platform invented.
    """

    minimum_cash_pct: float
    maximum_crypto_pct: float

    def __post_init__(self) -> None:
        for name, value in (
            ("minimum_cash_pct", self.minimum_cash_pct),
            ("maximum_crypto_pct", self.maximum_crypto_pct),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"the hard {name} is not a finite number")

            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"the hard {name} is outside 0..100")


class AllocationStanding(StrEnum):
    """Where one asset class sits against its own operating range."""

    #: Under the range's minimum. Guidance is to build toward it — and
    #: only through courses that are independently eligible.
    BELOW_RANGE = "below_range"

    #: Inside the range, wherever it sits against the target. The
    #: ordinary state, and the one that suggests nothing.
    WITHIN_RANGE = "within_range"

    #: Over the range's maximum. New deployment goes elsewhere; no sale
    #: follows from allocation alone.
    ABOVE_RANGE = "above_range"

    #: The allocation could not be read. Guidance is refused rather
    #: than computed from a substituted zero — an unread allocation is
    #: not an allocation of nothing.
    UNMEASURED = "unmeasured"


@dataclass(frozen=True, slots=True)
class AllocationBand:
    """One asset class's strategic target inside its operating range."""

    asset: str
    target_pct: float
    minimum_pct: float
    maximum_pct: float

    def __post_init__(self) -> None:
        for name, value in (
            ("target", self.target_pct),
            ("minimum", self.minimum_pct),
            ("maximum", self.maximum_pct),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{self.asset} {name} is not a finite number")

            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{self.asset} {name} is outside 0..100")

        if not self.minimum_pct <= self.target_pct <= self.maximum_pct:
            raise ValueError(
                f"{self.asset} requires minimum <= target <= maximum, and "
                f"states {self.minimum_pct:g} / {self.target_pct:g} / "
                f"{self.maximum_pct:g}"
            )

    @property
    def stated_range(self) -> str:
        """The range as the investor reads it, e.g. "25–45%"."""

        return f"{self.minimum_pct:g}–{self.maximum_pct:g}%"

    def standing_of(self, current_pct: float | None) -> AllocationStanding:
        if current_pct is None:
            return AllocationStanding.UNMEASURED

        if current_pct < self.minimum_pct:
            return AllocationStanding.BELOW_RANGE

        if current_pct > self.maximum_pct:
            return AllocationStanding.ABOVE_RANGE

        return AllocationStanding.WITHIN_RANGE


@dataclass(frozen=True, slots=True)
class StrategicAllocation:
    """The four bands, validated as one plan rather than four numbers."""

    stocks: AllocationBand
    etfs: AllocationBand
    crypto: AllocationBand
    cash: AllocationBand

    #: The active policy's own hard limits, required and never
    #: defaulted. The ranges above are validated against *these*, so
    #: the boundary the guidance quotes is the boundary the envelope
    #: funds against — by construction rather than by coincidence.
    limits: HardLimits

    def __post_init__(self) -> None:
        total = sum(band.target_pct for band in self.bands)

        if abs(total - 100.0) > TOTAL_TOLERANCE:
            raise ValueError(
                "the four strategic targets must total 100%, and they total "
                f"{total:g}% (stocks {self.stocks.target_pct:g}, ETFs "
                f"{self.etfs.target_pct:g}, crypto {self.crypto.target_pct:g}, "
                f"cash {self.cash.target_pct:g})"
            )

        # The bands are checked against the hard limits, never the other
        # way round: a plan may sit anywhere inside them and may not
        # describe a state the limits forbid. A range that contradicts
        # the active limit refuses the whole plan by name — this platform
        # does not pick whichever of the two numbers it prefers.
        floor = self.limits.minimum_cash_pct
        ceiling = self.limits.maximum_crypto_pct

        if self.cash.minimum_pct < floor:
            raise ValueError(
                f"the cash range's minimum ({self.cash.minimum_pct:g}%) is "
                f"below the {floor:g}% hard minimum-cash limit"
            )

        if self.cash.target_pct < floor:
            raise ValueError(
                f"the strategic cash target ({self.cash.target_pct:g}%) is "
                f"below the {floor:g}% hard minimum-cash limit"
            )

        if self.crypto.maximum_pct > ceiling:
            raise ValueError(
                f"the crypto range's maximum ({self.crypto.maximum_pct:g}%) "
                f"exceeds the {ceiling:g}% hard maximum-crypto limit"
            )

        if self.crypto.target_pct > ceiling:
            raise ValueError(
                f"the strategic crypto target ({self.crypto.target_pct:g}%) "
                f"exceeds the {ceiling:g}% hard maximum-crypto limit"
            )

    @property
    def bands(self) -> tuple[AllocationBand, ...]:
        return (self.stocks, self.etfs, self.crypto, self.cash)

    def band(self, asset: str) -> AllocationBand | None:
        return next((band for band in self.bands if band.asset == asset), None)


@dataclass(frozen=True, slots=True)
class AllocationGuidance:
    """One asset class's standing, and what this platform says about it.

    Descriptive throughout. `stated` is guidance about the *account's
    shape*, and no sentence it can produce names a security, proposes a
    trade or sizes one — allocation drift authorizes nothing.
    """

    asset: str

    #: None where the allocation could not be read. Never substituted.
    current_pct: float | None
    target_pct: float
    minimum_pct: float
    maximum_pct: float

    #: None exactly where `current_pct` is. An unmeasured allocation is
    #: not a difference of zero.
    difference_pct: float | None

    standing: AllocationStanding
    stated: str

    @property
    def stated_range(self) -> str:
        return f"{self.minimum_pct:g}–{self.maximum_pct:g}%"


def guidance_for(
    band: AllocationBand,
    current_pct: float | None,
    limits: HardLimits,
) -> AllocationGuidance:
    """One asset class's standing and its worded guidance.

    Cash and crypto carry their own wording because their hard limits
    make the same standing mean different things: cash above its range
    is *available*, and cash below its hard floor is a breach that
    stops deployment; crypto above its target but inside its range is
    permitted and forces no reduction, and crypto above the hard
    maximum is a breach whose remedy is the existing REDUCE policy
    floor rather than an exit.

    `limits` is required, so every hard-limit figure a reader sees was
    supplied by the active policy rather than remembered here.
    """

    standing = band.standing_of(current_pct)

    if standing is AllocationStanding.UNMEASURED:
        return AllocationGuidance(
            asset=band.asset,
            current_pct=None,
            target_pct=band.target_pct,
            minimum_pct=band.minimum_pct,
            maximum_pct=band.maximum_pct,
            difference_pct=None,
            standing=standing,
            stated=(
                f"The {ASSET_LABELS.get(band.asset, band.asset)} allocation "
                "could not be read, so no "
                "allocation guidance is offered for it. That is a limit of "
                "what this platform has read, not a reading of zero."
            ),
        )

    assert current_pct is not None

    return AllocationGuidance(
        asset=band.asset,
        current_pct=round(current_pct, 2),
        target_pct=band.target_pct,
        minimum_pct=band.minimum_pct,
        maximum_pct=band.maximum_pct,
        difference_pct=round(current_pct - band.target_pct, 2),
        standing=standing,
        stated=_stated(band, current_pct, standing, limits),
    )


def _stated(
    band: AllocationBand,
    current_pct: float,
    standing: AllocationStanding,
    limits: HardLimits,
) -> str:
    if band.asset == "cash":
        return _cash_stated(band, current_pct, standing, limits)

    if band.asset == "crypto":
        return _crypto_stated(band, current_pct, standing, limits)

    if standing is AllocationStanding.BELOW_RANGE:
        return (
            "Below the operating range. Build toward it only through "
            "independently eligible OPEN or ADD courses."
        )

    if standing is AllocationStanding.ABOVE_RANGE:
        return (
            "Above the operating range. Direct new deployment elsewhere; no "
            "sale follows from allocation alone."
        )

    return "Within the operating range. No allocation-driven action is suggested."


def _cash_stated(
    band: AllocationBand,
    current_pct: float,
    standing: AllocationStanding,
    limits: HardLimits,
) -> str:
    """Cash, where the target and the floor mean opposite things.

    The distinction the previous behaviour destroyed: below the
    strategic target is *permitted*, and below the hard floor is a
    breach. Calling the first one non-compliant is what made the
    account look wrong for holding the cash its own plan allows it to
    deploy.

    Every figure named here is the policy's own — the same
    `minimum_cash_pct` the envelope's funding room is measured above.
    """

    floor = limits.minimum_cash_pct

    if current_pct < floor:
        return (
            f"Below the {floor:g}% hard minimum-cash limit. "
            "This is a limit breach: no OPEN or ADD capacity exists while it "
            "stands."
        )

    if standing is AllocationStanding.ABOVE_RANGE:
        return (
            "Above the operating range. This cash is available to fund "
            "independently qualified opportunities while preserving the "
            f"{floor:g}% hard floor; holding it is not a "
            "fault, and deploying it is not required."
        )

    if current_pct < band.target_pct:
        return (
            f"Below the {band.target_pct:g}% strategic cash target and above "
            f"the {floor:g}% hard floor. This is permitted, "
            "not non-compliant: the target is a destination, and only the "
            "floor blocks deployment."
        )

    return "Within the operating range. No allocation-driven action is suggested."


def _crypto_stated(
    band: AllocationBand,
    current_pct: float,
    standing: AllocationStanding,
    limits: HardLimits,
) -> str:
    """Crypto, where above the target is not a reduction instruction."""

    ceiling = limits.maximum_crypto_pct

    if current_pct > ceiling:
        return (
            f"Above the {ceiling:g}% hard maximum-crypto "
            "limit. This is a limit breach; any reduction follows the "
            "existing REDUCE policy floor, which is the minimum that "
            "restores the limit and never a full exit."
        )

    if standing is AllocationStanding.BELOW_RANGE:
        return (
            "Below the operating range. Build toward it only through "
            "independently eligible OPEN or ADD courses."
        )

    if current_pct > band.target_pct:
        return (
            f"Above the {band.target_pct:g}% strategic crypto target and "
            "within the permitted range. No reduction follows: the target is "
            "a destination, and only the hard limit forces anything."
        )

    return "Within the operating range. No allocation-driven action is suggested."


@dataclass(frozen=True, slots=True)
class PortfolioAllocationGuidance:
    """The CIO's account of the account's shape, recorded once per cycle.

    Composed during the cycle from that cycle's own portfolio reading
    and the active policy, then rendered from the record — a page view
    recomputes nothing, so the homepage and any other surface cannot
    disagree about what the review said.

    What it will not do, by construction rather than by convention: it
    names no security (a security is named only where it already
    carries an eligible canonical course, which this object has no
    access to), it allocates nothing to make percentages match, it
    forces no sale of an asset inside its range, it reads no
    conviction, and it forecasts nothing.
    """

    allocations: tuple[AllocationGuidance, ...]

    #: The whole account in one sentence, built only from the standings
    #: above. Empty exactly where no allocation could be read.
    stated: str

    #: Why no guidance could be given, where that is the case.
    refused_because: str = ""

    def __post_init__(self) -> None:
        if bool(self.stated.strip()) == bool(self.refused_because.strip()):
            raise ValueError(
                "allocation guidance carries exactly one of: a statement, a refusal"
            )

    @property
    def below_range(self) -> tuple[str, ...]:
        return tuple(
            item.asset
            for item in self.allocations
            if item.standing is AllocationStanding.BELOW_RANGE
        )

    @property
    def above_range(self) -> tuple[str, ...]:
        return tuple(
            item.asset
            for item in self.allocations
            if item.standing is AllocationStanding.ABOVE_RANGE
        )


def portfolio_guidance_for(
    allocation: StrategicAllocation,
    current: dict[str, float | None],
) -> PortfolioAllocationGuidance:
    """The whole account's allocation guidance, from its own standings.

    Deterministic and read-only. `current` is the cycle's own portfolio
    reading, keyed by asset class, with None wherever a share could not
    be computed.
    """

    guidance = tuple(
        guidance_for(band, current.get(band.asset), allocation.limits)
        for band in allocation.bands
    )

    measured = [
        item for item in guidance if item.standing is not AllocationStanding.UNMEASURED
    ]

    if not measured:
        return PortfolioAllocationGuidance(
            allocations=guidance,
            stated="",
            refused_because=(
                "No allocation could be read for this account, so no "
                "allocation guidance is offered. That is a limit of what "
                "this platform has read, not a reading of zero."
            ),
        )

    return PortfolioAllocationGuidance(
        allocations=guidance,
        stated=_portfolio_stated(guidance, allocation.limits),
    )


def _portfolio_stated(
    guidance: tuple[AllocationGuidance, ...],
    limits: HardLimits,
) -> str:
    """One paragraph, assembled only from the standings themselves.

    Every clause is licensed by a standing this platform measured, and
    the closing sentence is the ruling's own: allocation drift alone
    authorizes no trade.
    """

    by_asset = {item.asset: item for item in guidance}

    clauses: list[str] = []

    below = [
        ASSET_LABELS.get(item.asset, item.asset)
        for item in guidance
        if item.standing is AllocationStanding.BELOW_RANGE and item.asset != "cash"
    ]

    if below:
        clauses.append(f"{_and(below)} below their operating ranges")

    crypto = by_asset.get("crypto")

    if crypto is not None and crypto.current_pct is not None:
        if crypto.standing is AllocationStanding.WITHIN_RANGE:
            clauses.append(
                "crypto is above its strategic target but remains within its "
                "permitted range"
                if crypto.current_pct > crypto.target_pct
                else "crypto is within its operating range"
            )
        elif crypto.standing is AllocationStanding.ABOVE_RANGE:
            clauses.append(
                f"crypto is above its {limits.maximum_crypto_pct:g}% hard limit"
            )

    cash = by_asset.get("cash")

    if cash is not None and cash.current_pct is not None:
        if cash.current_pct < limits.minimum_cash_pct:
            clauses.append(
                f"cash is below its {limits.minimum_cash_pct:g}% hard floor, so "
                "no new deployment is available"
            )
        elif cash.standing is AllocationStanding.ABOVE_RANGE:
            clauses.append(
                "cash is above its operating range and may fund "
                "independently qualified opportunities while preserving the "
                f"{limits.minimum_cash_pct:g}% hard floor"
            )
        elif cash.current_pct < cash.target_pct:
            clauses.append(
                "cash is below its strategic target and above its hard floor, "
                "which is permitted"
            )

    unmeasured = [
        ASSET_LABELS.get(item.asset, item.asset)
        for item in guidance
        if item.standing is AllocationStanding.UNMEASURED
    ]

    if unmeasured:
        clauses.append(
            f"{_and(unmeasured)} could not be read, so nothing is claimed "
            "about {}".format("them" if len(unmeasured) > 1 else "it")
        )

    if not clauses:
        return (
            "Every allocation sits within its operating range. No "
            "allocation-driven action is suggested, and allocation drift "
            "alone authorizes no trade."
        )

    body = ". ".join(_sentence(clause) for clause in clauses)

    return f"{body}. Move gradually; allocation drift alone authorizes no trade."


def _sentence(clause: str) -> str:
    return clause[0].upper() + clause[1:]


def _and(names: list[str]) -> str:
    if len(names) == 1:
        return f"{names[0]} is"

    return f"{', '.join(names[:-1])} and {names[-1]} are"
