"""What kind of crypto market an asset is trading inside, right now.

The third canonical evidence family, and the one that answers a
different class of question from the first two. S1–S3 answer *what is
this asset, which questions apply to it, and what is known about its own
economics*. This answers *what is the environment doing* — so that a
future Artificial CIO can eventually tell apart:

```text
HYPE is weakening                    from   crypto broadly is weakening
HYPE is falling, outperforming       from   HYPE is falling much more
its peers                                   than its peers
```

**Market context is not Asset Quality**, and the separation is
structural rather than a convention: nothing here is a token fact and
nothing here is a protocol fact, no score consumes any of it, and the
boundary is guarded by test.

Three disciplines this module exists to enforce.

**An interval is part of a figure.** A provider field called `change` is
not a fact until it says what it changed over. Every observation carries
its `MarketInterval`, a level carries `INSTANT`, and nothing is ever
collapsed into a generic "trend" — that word is an interpretation, and
no layer here is entitled to make one.

**A capitalisation change is not a return.** The provider publishes the
24-hour change in *total market capitalisation*, which moves with
issuance and with new listings as well as with prices. It is carried as
what it is. The comparator used for relative performance is a separate
figure this platform computes: a capitalisation-weighted return over a
**named universe**, which is the same kind of quantity as an asset's own
return and can therefore be subtracted from one.

**Relative performance is arithmetic, never an opinion.** *"HYPE
returned 3.2 percentage points less than its peer group over 24 hours"*
is a measurement. *"HYPE is showing relative weakness"* is a verdict,
and S4 makes none — no threshold, no band, no regime label.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.evidence_standing import EvidenceStanding


class MarketInterval(StrEnum):
    """What a figure covers in time. Never assumed, never dropped."""

    #: A level at the moment of reading.
    INSTANT = "instant"

    HOURS_1 = "1h"
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"

    @property
    def stated(self) -> str:
        return _INTERVALS[self]

    @property
    def is_window(self) -> bool:
        return self is not MarketInterval.INSTANT


_INTERVALS = {
    MarketInterval.INSTANT: "at the moment of reading",
    MarketInterval.HOURS_1: "over 1 hour",
    MarketInterval.HOURS_24: "over 24 hours",
    MarketInterval.DAYS_7: "over 7 days",
    MarketInterval.DAYS_30: "over 30 days",
}


class MarketUnit(StrEnum):
    """How a figure is worded. Formatting, and nothing more."""

    USD = "usd"

    #: A percentage change over the observation's interval.
    PERCENT_CHANGE = "percent_change"

    #: A share of a stated whole, in percent.
    PERCENT_SHARE = "percent_share"

    #: A difference between two percentages.
    PERCENTAGE_POINTS = "percentage_points"

    COUNT = "count"


class MarketPeriodicity(StrEnum):
    """Whether a metric is a level or a change.

    Kept explicit so a level can never acquire a window and a change can
    never lose one — the two failure modes that make market data lie.
    """

    LEVEL = "level"
    CHANGE = "change"


class MarketMetric(StrEnum):
    """The market facts this platform knows how to hold."""

    TOTAL_MARKET_CAP = "total_market_cap"
    TOTAL_VOLUME = "total_volume"
    MARKET_CAP_CHANGE = "market_cap_change"
    VOLUME_CHANGE = "volume_change"

    BTC_DOMINANCE = "btc_dominance"
    ETH_DOMINANCE = "eth_dominance"
    STABLECOIN_SHARE = "stablecoin_share"

    #: This platform's capitalisation-weighted return over a named
    #: universe. The comparator relative performance is measured
    #: against, and the only market figure that is the same kind of
    #: quantity as an asset's own return.
    MARKET_RETURN = "market_return"

    ADVANCING = "advancing"
    DECLINING = "declining"
    TRACKED_ASSETS = "tracked_assets"

    #: One security's own price return. Held here rather than with its
    #: market facts because it exists to be compared with the two above,
    #: and a return without its comparator's interval is not usable.
    ASSET_RETURN = "asset_return"

    #: A peer group's state.
    PEER_MARKET_CAP = "peer_market_cap"
    PEER_MARKET_CAP_CHANGE = "peer_market_cap_change"
    PEER_RETURN = "peer_return"
    PEER_VOLUME = "peer_volume"
    PEER_ADVANCING = "peer_advancing"
    PEER_DECLINING = "peer_declining"


@dataclass(frozen=True, slots=True)
class MarketMeasure:
    """Exactly what one market metric means, before any value is attached."""

    metric: MarketMetric
    label: str
    unit: MarketUnit
    periodicity: MarketPeriodicity

    #: This platform's own definition, independent of any provider.
    definition: str

    #: True where this platform computed it rather than read it.
    derived: bool = False


MEASURES: dict[MarketMetric, MarketMeasure] = {
    MarketMetric.TOTAL_MARKET_CAP: MarketMeasure(
        metric=MarketMetric.TOTAL_MARKET_CAP,
        label="Total crypto market capitalisation",
        unit=MarketUnit.USD,
        periodicity=MarketPeriodicity.LEVEL,
        definition=(
            "The summed market value of every asset the provider tracks, "
            "as the provider computes it. The universe is the provider's "
            "own, so this is not independently reproducible."
        ),
    ),
    MarketMetric.TOTAL_VOLUME: MarketMeasure(
        metric=MarketMetric.TOTAL_VOLUME,
        label="Total market trading volume",
        unit=MarketUnit.USD,
        periodicity=MarketPeriodicity.LEVEL,
        definition=(
            "Value traded across every venue the provider tracks over "
            "the preceding day. A measure of how active the market is — "
            "never a measure of whether one position can be left."
        ),
    ),
    MarketMetric.MARKET_CAP_CHANGE: MarketMeasure(
        metric=MarketMetric.MARKET_CAP_CHANGE,
        label="Change in total market capitalisation",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How far the aggregate capitalisation moved over the "
            "interval. **Not a return**: it also moves with issuance and "
            "with assets entering and leaving the provider's universe, "
            "so it is never subtracted from an asset's price return."
        ),
    ),
    MarketMetric.VOLUME_CHANGE: MarketMeasure(
        metric=MarketMetric.VOLUME_CHANGE,
        label="Change in total market volume",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How far the market's traded value moved over the interval, "
            "as the provider computes it."
        ),
    ),
    MarketMetric.BTC_DOMINANCE: MarketMeasure(
        metric=MarketMetric.BTC_DOMINANCE,
        label="Bitcoin dominance",
        unit=MarketUnit.PERCENT_SHARE,
        periodicity=MarketPeriodicity.LEVEL,
        definition=(
            "Bitcoin's share of the tracked market's capitalisation. A "
            "statement about concentration, and not on its own a "
            "statement about direction."
        ),
    ),
    MarketMetric.ETH_DOMINANCE: MarketMeasure(
        metric=MarketMetric.ETH_DOMINANCE,
        label="Ethereum dominance",
        unit=MarketUnit.PERCENT_SHARE,
        periodicity=MarketPeriodicity.LEVEL,
        definition="Ethereum's share of the tracked market's capitalisation.",
    ),
    MarketMetric.STABLECOIN_SHARE: MarketMeasure(
        metric=MarketMetric.STABLECOIN_SHARE,
        label="Stablecoin share",
        unit=MarketUnit.PERCENT_SHARE,
        periodicity=MarketPeriodicity.LEVEL,
        definition=(
            "The share of the tracked market's capitalisation held in "
            "the stablecoins the provider names in its dominance table. "
            "A floor rather than a total: the table lists only the "
            "largest assets, so smaller stablecoins are not counted."
        ),
        derived=True,
    ),
    MarketMetric.MARKET_RETURN: MarketMeasure(
        metric=MarketMetric.MARKET_RETURN,
        label="Market return",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "This platform's capitalisation-weighted average of the "
            "price returns of a named universe of assets. The same kind "
            "of quantity as one asset's return, which is what makes the "
            "difference between them meaningful."
        ),
        derived=True,
    ),
    MarketMetric.ADVANCING: MarketMeasure(
        metric=MarketMetric.ADVANCING,
        label="Assets advancing",
        unit=MarketUnit.COUNT,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How many assets in the named universe rose over the "
            "interval. Breadth: whether a move was broad or carried by "
            "a few large assets."
        ),
        derived=True,
    ),
    MarketMetric.DECLINING: MarketMeasure(
        metric=MarketMetric.DECLINING,
        label="Assets declining",
        unit=MarketUnit.COUNT,
        periodicity=MarketPeriodicity.CHANGE,
        definition="How many assets in the named universe fell over the interval.",
        derived=True,
    ),
    MarketMetric.TRACKED_ASSETS: MarketMeasure(
        metric=MarketMetric.TRACKED_ASSETS,
        label="Assets tracked",
        unit=MarketUnit.COUNT,
        periodicity=MarketPeriodicity.LEVEL,
        definition="How many assets the provider's universe contains.",
    ),
    MarketMetric.ASSET_RETURN: MarketMeasure(
        metric=MarketMetric.ASSET_RETURN,
        label="Price return",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How far this asset's own price moved over the interval, as "
            "the provider reports it."
        ),
    ),
    MarketMetric.PEER_MARKET_CAP: MarketMeasure(
        metric=MarketMetric.PEER_MARKET_CAP,
        label="Peer group capitalisation",
        unit=MarketUnit.USD,
        periodicity=MarketPeriodicity.LEVEL,
        definition=(
            "The summed market value of the peer group, as the provider "
            "computes it over its own category membership."
        ),
    ),
    MarketMetric.PEER_MARKET_CAP_CHANGE: MarketMeasure(
        metric=MarketMetric.PEER_MARKET_CAP_CHANGE,
        label="Change in peer group capitalisation",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How far the peer group's aggregate capitalisation moved, as "
            "the provider computes it. Carried for transparency and "
            "**not** the comparator: like the market's own figure it "
            "moves with issuance and with membership, so it is never "
            "subtracted from a price return."
        ),
    ),
    MarketMetric.PEER_RETURN: MarketMeasure(
        metric=MarketMetric.PEER_RETURN,
        label="Peer group return",
        unit=MarketUnit.PERCENT_CHANGE,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "This platform's capitalisation-weighted average of the "
            "price returns of the peer group's members, over the page of "
            "the group it read. The same kind of quantity as one asset's "
            "return, which is what makes the difference meaningful."
        ),
        derived=True,
    ),
    MarketMetric.PEER_VOLUME: MarketMeasure(
        metric=MarketMetric.PEER_VOLUME,
        label="Peer group volume",
        unit=MarketUnit.USD,
        periodicity=MarketPeriodicity.LEVEL,
        definition="Value traded across the peer group over the preceding day.",
    ),
    MarketMetric.PEER_ADVANCING: MarketMeasure(
        metric=MarketMetric.PEER_ADVANCING,
        label="Peers advancing",
        unit=MarketUnit.COUNT,
        periodicity=MarketPeriodicity.CHANGE,
        definition=(
            "How many of the peer group's assets rose over the interval, "
            "counted over the page of it this platform read."
        ),
        derived=True,
    ),
    MarketMetric.PEER_DECLINING: MarketMeasure(
        metric=MarketMetric.PEER_DECLINING,
        label="Peers declining",
        unit=MarketUnit.COUNT,
        periodicity=MarketPeriodicity.CHANGE,
        definition="How many of the peer group's assets fell over the interval.",
        derived=True,
    ),
}


@dataclass(frozen=True, slots=True)
class MarketUniverse:
    """The set of assets a figure was computed over, named so it can be argued with.

    Every aggregate on this page is an aggregate *of something*, and the
    something is a vendor's decision. "The market rose 0.2%" means
    nothing until it says which assets were counted and who chose them.
    """

    key: str
    name: str

    #: What the universe contains and who decided it, in one sentence.
    described: str

    #: How many assets it covers, where the count is known.
    counted: int | None = None


@dataclass(frozen=True, slots=True)
class MarketObservation:
    """One market figure, with everything needed to read it honestly."""

    metric: MarketMetric
    interval: MarketInterval

    standing: EvidenceStanding

    value: float | None = None

    #: The universe it was computed over, where it is an aggregate.
    universe: MarketUniverse | None = None

    source: str | None = None
    observed_at: datetime | None = None

    #: The observations this one was computed from, where this platform
    #: computed it. Named so the arithmetic can be checked.
    derived_from: tuple[str, ...] = ()

    #: This platform's account of the standing or the absence.
    because: str | None = None

    @property
    def measure(self) -> MarketMeasure:
        return MEASURES[self.metric]

    @property
    def stated(self) -> str | None:
        """The figure as a surface prints it, worded here once."""

        if self.value is None or not self.standing.serves_value:
            return None

        unit = self.measure.unit

        if unit is MarketUnit.USD:
            return _money(self.value)

        if unit is MarketUnit.COUNT:
            return f"{self.value:,.0f}"

        if unit is MarketUnit.PERCENTAGE_POINTS:
            return f"{self.value:+,.2f} pp"

        if unit is MarketUnit.PERCENT_CHANGE:
            return f"{self.value:+,.2f}%"

        return f"{self.value:,.2f}%"

    @property
    def is_held(self) -> bool:
        return self.value is not None and self.standing.serves_value


def _money(value: float) -> str:
    """An amount at a unit that keeps it visible."""

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:,.2f}tn"

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    return f"${value:,.0f}"


@dataclass(frozen=True, slots=True)
class CryptoMarketSnapshot:
    """A dated observation of the crypto environment.

    Deliberately not per-security: this is the environment every token
    trades inside, read once per cycle. What one security did *relative*
    to it is `MarketContext`, computed on read.
    """

    observed_at: datetime | None
    source: str | None

    observations: tuple[MarketObservation, ...] = ()

    #: The universes any aggregate here was computed over.
    universes: tuple[MarketUniverse, ...] = ()

    #: Why nothing was read, where nothing was.
    unavailable_because: str | None = None

    def observation(
        self,
        metric: MarketMetric,
        interval: MarketInterval | None = None,
    ) -> MarketObservation | None:
        for item in self.observations:
            if item.metric is metric and (
                interval is None or item.interval is interval
            ):
                return item

        return None

    def value(
        self,
        metric: MarketMetric,
        interval: MarketInterval | None = None,
    ) -> float | None:
        """One figure, where the standing permits it to be served."""

        held = self.observation(metric, interval)

        return held.value if held is not None and held.is_held else None

    @property
    def is_read(self) -> bool:
        return bool(self.observations)


@dataclass(frozen=True, slots=True)
class RelativeReturn:
    """One asset's return against one comparator's, over the same interval.

    Arithmetic and nothing else. The wording is descriptive and
    threshold-free by construction: it states the difference in
    percentage points and stops. A word like *weak* or *outperforming
    materially* would be a verdict, and no rule on this platform has
    earned one yet.
    """

    interval: MarketInterval

    subject: str
    subject_return: float

    comparator: str
    comparator_return: float

    #: Subject minus comparator, in percentage points.
    delta: float

    #: The weakest standing of the two inputs. A difference cannot be
    #: firmer than the softer figure beneath it.
    standing: EvidenceStanding

    #: The arithmetic in one checkable line.
    stated: str

    #: What would make the reader misread it, where anything would.
    caveat: str | None = None


@dataclass(frozen=True, slots=True)
class Concentration:
    """How much of the comparator the subject itself is.

    The figure a relative measurement cannot be read without, and one no
    vendor supplies. Bitcoin is over half the market, so "BTC against the
    market" is substantially BTC against itself; Hyperliquid is
    three-quarters of its own peer group. It is stated as a plain
    measurement with its denominator named, and no threshold decides
    when it matters — that is the reader's judgment, and later an
    analyst's.
    """

    subject: str
    comparator: str

    #: The subject's share of the comparator's capitalisation, in percent.
    share: float

    standing: EvidenceStanding

    stated: str

    #: What the denominator actually was. A share of the market is a
    #: share of some named set of assets, and which set is part of the
    #: number.
    comparator_described: str | None = None


def relative_return(
    subject: str,
    subject_observation: MarketObservation,
    comparator: str,
    comparator_observation: MarketObservation,
    caveat: str | None = None,
) -> RelativeReturn | None:
    """The difference between two returns, or nothing.

    **Refuses unless the intervals match.** Not a convenience check: an
    asset's 7-day return minus a market's 24-hour move is a number with
    no meaning, and it would look exactly as authoritative as a real
    one. The corpus makes this live rather than theoretical — the
    provider publishes asset returns at four intervals and market and
    peer figures at one.
    """

    if subject_observation.interval is not comparator_observation.interval:
        return None

    if not subject_observation.is_held or not comparator_observation.is_held:
        return None

    subject_value = subject_observation.value
    comparator_value = comparator_observation.value

    if subject_value is None or comparator_value is None:
        return None

    delta = subject_value - comparator_value

    interval = subject_observation.interval

    direction = "more" if delta >= 0 else "less"

    return RelativeReturn(
        interval=interval,
        subject=subject,
        subject_return=subject_value,
        comparator=comparator,
        comparator_return=comparator_value,
        delta=delta,
        standing=_weakest(
            subject_observation.standing,
            comparator_observation.standing,
        ),
        stated=(
            f"{subject} returned {abs(delta):.2f} percentage points "
            f"{direction} than {comparator} {interval.stated} "
            f"({subject_value:+.2f}% against {comparator_value:+.2f}%) — "
            "MOVRvest's arithmetic over two figures read at the same "
            "interval."
        ),
        caveat=caveat,
    )


def concentration(
    subject: str,
    subject_market_cap: float | None,
    comparator: str,
    comparator_market_cap: float | None,
    standing: EvidenceStanding,
    comparator_described: str | None = None,
) -> Concentration | None:
    """The subject's share of its comparator — this platform's arithmetic.

    Both figures must come from the same provider's universe. A share
    whose numerator and denominator were counted by different vendors
    would not be a share of anything, which is the same rule that keeps
    an asset's volume and the market's apart.
    """

    if not subject_market_cap or not comparator_market_cap:
        return None

    if comparator_market_cap <= 0:
        return None

    share = 100.0 * subject_market_cap / comparator_market_cap

    # Two decimals below one percent, one above: a holding worth 0.02%
    # of the market and one worth nothing are different readings, and
    # "0.0%" reports them identically.
    figure = f"{share:.2f}%" if share < 1 else f"{share:.1f}%"

    return Concentration(
        subject=subject,
        comparator=comparator,
        share=share,
        standing=standing,
        stated=(
            f"{subject} is {figure} of {comparator} by market value"
            + (f" ({comparator_described})" if comparator_described else "")
            + "."
        ),
        comparator_described=comparator_described,
    )


_ORDER = (
    EvidenceStanding.ESTABLISHED,
    EvidenceStanding.CLAIMED,
    EvidenceStanding.CONFLICTED,
    EvidenceStanding.REJECTED,
    EvidenceStanding.ABSENT,
)


def _weakest(*standings: EvidenceStanding) -> EvidenceStanding:
    """The softest standing among several — a derivation's own ceiling."""

    return max(standings, key=_ORDER.index)
