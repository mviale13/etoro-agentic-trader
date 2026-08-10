"""What happened to a digital asset recently, and who says so.

The second half of the perishable layer. Slice 1 gave the intelligence
brief flows and holdings — quantities, published on a schedule, with a
date. This gives it **events**: things that happened, reported in
sentences, by sources of very different authority.

That difference in shape is the whole difficulty. A flow figure is a
number and a date. An event arrives as a paragraph that mixes what
happened with what the writer thinks it means:

> *"Bitcoin mining difficulty declined by 19% from its peak, marking the
> largest drop since China's 2021 ban. This highlights economic
> pressures on miners."*

Two sentences, two different kinds of statement. The first is checkable
and the second is the writer's reading. Stored as one blob, the second
borrows the first's authority — which is the failure this platform is
built against, and the reason §2 of the ruling separates them.

So an event is **never one canonical fact**. It is:

```text
CryptoEvent          the thing that happened, identified and dated
  ├─ SourceReport    one source's account of it, with that source's name
  ├─ EventFact       a checkable statement, REPORTED, with its anchor
  └─ Interpretation  a source's reading, ATTRIBUTED, never this platform's
```

**A hedge is what separates the two, and a number is what makes a fact
checkable.** Those are two different properties and the first draft of
this module conflated them — it required a quantity before a sentence
could be a fact, and duly filed *"AUSTRAC suspended Cryptolink's VASP
registration"* as an opinion. So: a sentence that hedges, grades or
claims a cause is an `Interpretation` carrying its author's name;
everything else is an `EventFact`; and `anchors` records the quantities
that make it comparable against another source's account.

Over-attributing costs a reader a label. Over-factualising is how
*"institutional interest remains strong"* ends up looking like a
measurement, so the gradings — *dominates*, *significant*, *robust* —
are markers too.

**Causal sentences are their own outcome.** *"ETF demand is supporting
price"* is not a fact, and it is not merely an opinion either — it is an
unresolved claim about cause, and §12 forbids this platform from
settling it. It is kept, marked, and never promoted.

**Identity is not the headline.** Three outlets writing three headlines
about one exploit are one event, and `identity` is what collapses them:
subject, family, day, and the numeric anchor the accounts share. Getting
this wrong produces the failure the ruling names — four copies of one
upgrade, read as four developments.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.domain.evidence_authority import EvidenceAuthority


class EventFamily(StrEnum):
    """What kind of development this is.

    Nine members, and every one of them was **observed in the live
    corpus before it was declared** — the measurement is in
    `docs/architecture/CRYPTO_EVENTS.md`. The ruling's own list offered
    more; the ones that no source produced for any of the eight assets
    this platform reads are not here, because a family with no instance
    is a category waiting to be filled rather than a distinction the
    evidence forced.

    Governance is the notable absence. Snapshot answers keylessly and
    the proposals are real, but every proposal for the two mapped
    governed assets is closed, and none of BTC, ETH or HYPE is governed
    that way at all. It is measured and declined, not overlooked.
    """

    #: A regulator, court or supervisor did something.
    REGULATORY = "regulatory"

    #: An exploit, a drain, a key compromise, a disclosed vulnerability.
    SECURITY = "security"

    #: The protocol itself changed, or a release that changes it shipped.
    PROTOCOL_UPGRADE = "protocol_upgrade"

    #: An identifiable balance sheet took or reduced a position, or a
    #: fund vehicle changed.
    INSTITUTIONAL_ADOPTION = "institutional_adoption"

    #: Money moving through an identifiable vehicle.
    CAPITAL_FLOW = "capital_flow"

    #: What the network did — issuance, difficulty, staking, addresses,
    #: fees. The chain's own operation.
    NETWORK_OPERATION = "network_operation"

    #: How the asset is traded: venues, listings, positioning, large
    #: transfers, derivative structure.
    MARKET_STRUCTURE = "market_structure"

    #: Something was built on it, or something started using it.
    ECOSYSTEM_ADOPTION = "ecosystem_adoption"

    #: The token's own economics changed — burns, unlocks, emissions,
    #: buybacks, treasury policy.
    TOKENOMICS = "tokenomics"

    @property
    def stated(self) -> str:
        return _FAMILIES[self]

    @property
    def changes_durable_facts(self) -> bool:
        """Whether an event of this family can change what the asset *is*.

        A separate question from whether it is interesting. An exploit,
        a rule change and a regulator's decision alter the durable case;
        a day's positioning does not. §11 uses this to rank, and §19
        forbids it from doing anything more — an event may *explain* a
        durable fact and never rewrite one.
        """

        return self in (
            EventFamily.REGULATORY,
            EventFamily.SECURITY,
            EventFamily.PROTOCOL_UPGRADE,
            EventFamily.TOKENOMICS,
        )


_FAMILIES = {
    EventFamily.REGULATORY: "Regulatory",
    EventFamily.SECURITY: "Security",
    EventFamily.PROTOCOL_UPGRADE: "Protocol change",
    EventFamily.INSTITUTIONAL_ADOPTION: "Institutional participation",
    EventFamily.CAPITAL_FLOW: "Capital flow",
    EventFamily.NETWORK_OPERATION: "Network operation",
    EventFamily.MARKET_STRUCTURE: "Market structure",
    EventFamily.ECOSYSTEM_ADOPTION: "Ecosystem adoption",
    EventFamily.TOKENOMICS: "Token economics",
}


#: Rank order for §11's materiality rules. Lower sorts first. Deliberately
#: a rank and not a weight: there is no arithmetic between families, and
#: a score would invite one.
_FAMILY_RANK = {
    EventFamily.SECURITY: 0,
    EventFamily.REGULATORY: 1,
    EventFamily.PROTOCOL_UPGRADE: 2,
    EventFamily.TOKENOMICS: 3,
    EventFamily.CAPITAL_FLOW: 4,
    EventFamily.INSTITUTIONAL_ADOPTION: 5,
    EventFamily.NETWORK_OPERATION: 6,
    EventFamily.MARKET_STRUCTURE: 7,
    EventFamily.ECOSYSTEM_ADOPTION: 8,
}


class EventStatus(StrEnum):
    """Whether the thing is finished, still running, or unsettled."""

    #: It happened and it is over.
    COMPLETED = "completed"

    #: It is still running, so the next reading may differ.
    ONGOING = "ongoing"

    #: Sources disagree about it, or its outcome is not settled.
    UNRESOLVED = "unresolved"

    @property
    def stated(self) -> str:
        return {
            EventStatus.COMPLETED: "completed",
            EventStatus.ONGOING: "ongoing",
            EventStatus.UNRESOLVED: "unresolved",
        }[self]


class SourceTier(StrEnum):
    """How close a source is to the thing it reports.

    §4's ruling in one word each. It is **not** a standing: a primary
    source can be wrong and a secondary one can be right. It says what
    kind of check would settle a disagreement, which is what a reader
    needs in order to weigh two accounts.
    """

    #: The party that did the thing, or the register that records it.
    #: A protocol's own release, a regulator's own notice, a chain's own
    #: state.
    PRIMARY = "primary"

    #: A publication reporting on it. Useful for discovery and for
    #: corroboration, never authoritative on its own.
    SECONDARY = "secondary"

    #: A provider's own editorial summary over other people's reporting.
    #: One step further out again, and the reason the whole insight
    #: surface is attributed rather than reported.
    AGGREGATOR = "aggregator"

    @property
    def stated(self) -> str:
        return {
            SourceTier.PRIMARY: "primary source",
            SourceTier.SECONDARY: "press report",
            SourceTier.AGGREGATOR: "aggregated summary",
        }[self]

    @property
    def authority(self) -> EvidenceAuthority:
        """The S4.5 axis this tier sits on."""

        return {
            SourceTier.PRIMARY: EvidenceAuthority.PRIMARY_OBSERVATION,
            SourceTier.SECONDARY: EvidenceAuthority.SECONDARY_AGGREGATE,
            SourceTier.AGGREGATOR: EvidenceAuthority.ATTRIBUTED_OPINION,
        }[self]


@dataclass(frozen=True, slots=True)
class SourceReport:
    """One source's account of an event, kept whole beneath the event.

    §9: *retain all useful source provenance beneath one event*. Three
    outlets on one exploit collapse into one `CryptoEvent` carrying
    three of these, so a reader can see who reported it — and nothing is
    averaged, because averaging two accounts produces a third that
    nobody published.
    """

    source: str
    tier: SourceTier

    #: What this source said. Its words, not this platform's.
    text: str

    url: str | None = None
    published_at: datetime | None = None

    @property
    def authority(self) -> EvidenceAuthority:
        return self.tier.authority


@dataclass(frozen=True, slots=True)
class EventFact:
    """A checkable statement inside an event.

    Checkable **in principle**: this platform did not check it, and
    `REPORTED` is exactly that standing. What earns a sentence this
    status is `anchor` — a measurable quantity. A sentence with no
    number is an impression, and an impression is an interpretation
    wearing a fact's clothes.
    """

    stated: str

    #: The quantities the sentence turns on, normalised for comparison.
    #: Also what lets two sources be recognised as reporting one event.
    anchors: tuple[str, ...] = ()

    #: Sources that independently carry this same anchor. Empty is the
    #: ordinary case and is not a defect.
    corroborated_by: tuple[str, ...] = ()

    @property
    def is_corroborated(self) -> bool:
        """Whether a second, independent source carries the same figure.

        Independence is the whole content of the word. S5's lesson —
        two sources agreeing to the last bit are one source — applies to
        provenance here rather than to precision: two outlets running
        one wire story are one account, so the service compares source
        *names* and never counts an event's own restatements.
        """

        return len(self.corroborated_by) >= 1

    def also_reported_by(self, sources: tuple[str, ...]) -> EventFact:
        """The same fact, with further independent sources recorded."""

        return EventFact(
            stated=self.stated,
            anchors=self.anchors,
            corroborated_by=tuple(dict.fromkeys(self.corroborated_by + sources)),
        )


@dataclass(frozen=True, slots=True)
class Interpretation:
    """A source's reading of what an event means. Always attributed.

    Never promoted, on any evidence. If this platform ever agrees with
    one of these, it says so in its own voice as an `INFERRED` claim
    with its own evidence — it does not upgrade somebody else's
    sentence.
    """

    stated: str
    source: str

    #: Whether the sentence asserts that one thing *caused* another.
    #: §12's guard: kept, marked, and never settled here.
    is_causal: bool = False


@dataclass(frozen=True, slots=True)
class CryptoEvent:
    """One development, however many sources reported it.

    Identity is the load-bearing field. Everything else describes the
    event; `identity` decides whether two accounts *are* one event, and
    it is derived from what the accounts share rather than from the
    words they chose.
    """

    identity: str

    #: The assets this bears on. Usually one; an exploit on a chain
    #: bears on the chain's asset.
    symbols: tuple[str, ...]

    family: EventFamily

    #: The sentence naming what happened. A headline, not a paragraph.
    headline: str

    #: When it happened, where a source dates it. Distinct from when it
    #: was published and from when this platform read it — a flow
    #: settles days before anyone reports it, and a brief that conflated
    #: the three would present old news as today's.
    occurred_at: datetime | None
    published_at: datetime | None
    observed_at: datetime

    reports: tuple[SourceReport, ...] = ()
    facts: tuple[EventFact, ...] = ()
    interpretations: tuple[Interpretation, ...] = ()

    status: EventStatus = EventStatus.COMPLETED

    #: The entity the event is about, where it is not the asset itself —
    #: a company, a venue, a regulator, an application.
    entity: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(report.source for report in self.reports))

    @property
    def tier(self) -> SourceTier:
        """The closest any of its accounts gets to the thing itself."""

        if any(r.tier is SourceTier.PRIMARY for r in self.reports):
            return SourceTier.PRIMARY

        if any(r.tier is SourceTier.SECONDARY for r in self.reports):
            return SourceTier.SECONDARY

        return SourceTier.AGGREGATOR

    @property
    def is_multi_source(self) -> bool:
        return len(self.sources) > 1

    @property
    def at(self) -> datetime | None:
        """The best time this platform has for it."""

        return self.occurred_at or self.published_at

    @property
    def causal_claims(self) -> tuple[Interpretation, ...]:
        return tuple(item for item in self.interpretations if item.is_causal)

    def age(self, now: datetime | None = None) -> timedelta | None:
        moment = now or datetime.now(UTC)
        when = self.at

        if when is None:
            return None

        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)

        return moment - when

    def rank(self, now: datetime | None = None) -> tuple[int, ...]:
        """§11's materiality, as ranked rules rather than a score.

        Read in order, and each term only breaks ties in the one before
        it: **what kind of thing it is**, then **whether it is still
        running**, then **how close the reporting gets**, then **whether
        anyone corroborated it**, then **how new it is**. There is no
        arithmetic between the terms and no threshold to tune, which is
        the point — a number here would be a quality score for news, and
        this platform has spent five slices declining to invent those.
        """

        age = self.age(now)

        return (
            _FAMILY_RANK[self.family],
            0 if self.status is not EventStatus.COMPLETED else 1,
            {SourceTier.PRIMARY: 0, SourceTier.SECONDARY: 1, SourceTier.AGGREGATOR: 2}[
                self.tier
            ],
            0 if self.is_multi_source else 1,
            int(age.total_seconds()) if age is not None else 1 << 40,
        )


# ── identity ────────────────────────────────────────────────────────


#: Words that carry no distinguishing weight in a headline. Kept short
#: on purpose: a long stop list starts deciding what an event is about.
_NOISE = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "and",
    "or",
    "as",
    "at",
    "by",
    "with",
    "from",
    "its",
    "it",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "has",
    "have",
    "had",
    "after",
    "over",
    "amid",
    "new",
    "more",
    "than",
    "this",
    "that",
    "up",
    "down",
    "into",
    "s",
    "t",
}

_NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*(%|percent|bps)?", re.I)

#: A magnitude word, and it must be a **whole word**.
#:
#: The boundary is not a nicety. Matched as a prefix, `b` for billion
#: reads *"23,093 BTC"* as twenty-three thousand billion, and `bn` reads
#: *"since China's 2021 ban"* as the year two thousand and twenty-one
#: billion. Both were produced by the first draft against live copy, and
#: both would have made two accounts of one event look like accounts of
#: different ones — which is the exact failure the anchor exists to
#: prevent.
_SCALE = re.compile(
    r"^(k|m|bn|b|mn|billion|million|thousand|trillion|tn)\b",
    re.I,
)

_FACTOR = {
    "k": 1e3,
    "thousand": 1e3,
    "m": 1e6,
    "mn": 1e6,
    "million": 1e6,
    "b": 1e9,
    "bn": 1e9,
    "billion": 1e9,
    "tn": 1e12,
    "trillion": 1e12,
}

#: Bare integers in this range are read as years rather than as
#: quantities. *"in First Half 2026"* is a date, and an identity built on
#: it would collapse every event of the year into one.
_YEARS = range(1990, 2101)


def anchors_in(text: str) -> tuple[str, ...]:
    """The measurable quantities a sentence turns on, normalised.

    An anchor is what lets two accounts be recognised as accounts of one
    event, and what makes a factual sentence *checkable* rather than
    merely asserted. Normalising matters more than it looks: *"$1.6
    billion"*, *"$1.6bn"* and *"1,600,000,000"* are one claim written
    three ways, and an identity rule that missed that would publish
    three copies of one sale.
    """

    found: list[str] = []

    lowered = _fold(text)

    for match in _NUMBER.finditer(lowered):
        raw = match.group(1).replace(",", "")

        try:
            value = float(raw)
        except ValueError:
            continue

        scaled = False

        tail = lowered[match.end() : match.end() + 14].lstrip()

        scale = _SCALE.match(tail)

        if scale is not None:
            value *= _FACTOR[scale.group(1).lower()]
            scaled = True

        if match.group(2):
            found.append(f"{_trim(value)}%")
            continue

        # A year is a date, not a size. Only where nothing else marks it
        # as a quantity: "$2,026" and "2026 million" are not years.
        if (
            not scaled
            and value == int(value)
            and int(value) in _YEARS
            and not lowered[: match.start()].rstrip().endswith("$")
        ):
            continue

        found.append(_trim(value))

    return tuple(dict.fromkeys(found))


def _trim(value: float) -> str:
    """A number as a comparison key, with float noise removed."""

    if value == int(value):
        return str(int(value))

    return f"{value:.4f}".rstrip("0").rstrip(".")


def _fold(text: str) -> str:
    """Lowercase, and with the typographic characters feeds vary on
    reduced to their plain equivalents.

    Curly apostrophes and non-breaking spaces have already cost this
    platform a section locator; two feeds writing *Hyperliquid's* two
    ways must not become two events.
    """

    folded = unicodedata.normalize("NFKD", text)

    return "".join(ch for ch in folded if not unicodedata.combining(ch)).lower()


def keywords_in(text: str, limit: int = 6) -> tuple[str, ...]:
    """The words a headline is actually about, in order of appearance."""

    words = [
        word
        for word in re.findall(r"[a-z0-9]+", _fold(text))
        if word not in _NOISE and len(word) > 2
    ]

    return tuple(dict.fromkeys(words))[:limit]


def identity_of(
    symbols: tuple[str, ...],
    family: EventFamily,
    headline: str,
    when: datetime | None,
) -> str:
    """The key two accounts of one event must agree on.

    Four terms, and each one earns its place by a way the others fail.
    **Subject** and **family** keep an Ethereum exploit apart from a
    Bitcoin one and a listing apart from a hack. **Day** keeps this
    month's upgrade apart from last month's. And the **anchor** — a
    figure both accounts carry — is what actually does the work, because
    two outlets never choose the same words and almost always quote the
    same number.

    Where an account carries no figure at all, the headline's own
    keywords stand in. That is weaker, and it is why the service treats
    a keyword-only match as a merge candidate to be confirmed rather
    than as an identity on its own.
    """

    day = when.astimezone(UTC).date().isoformat() if when else "undated"

    anchors = anchors_in(headline)

    tail = "+".join(sorted(anchors)) if anchors else "+".join(keywords_in(headline, 4))

    return f"{'/'.join(sorted(symbols))}|{family.value}|{day}|{tail}"


# ── decomposition ───────────────────────────────────────────────────


#: Verbs, hedges and gradings that mark a sentence as somebody's
#: reading. A sentence carrying one of these is attributed even when it
#: also carries a number: *"$245m of inflows indicates sustained
#: demand"* is an interpretation with a figure inside it, and the figure
#: belongs to whichever sentence stated it plainly.
_INTERPRETIVE = (
    "indicat",
    "highlight",
    "suggest",
    "signal",
    "reflect",
    "underscore",
    "demonstrat",
    "show that",
    "shows that",
    "means that",
    "point to",
    "points to",
    "may ",
    "might ",
    "could ",
    "should ",
    "likely",
    "potential",
    "expect",
    "anticipat",
    "appears",
    "seems",
    "bullish",
    "bearish",
    "sentiment",
    "confidence",
    "optimis",
    "suppress",
    "boost",
    "strengthen",
    "weaken",
    "improv",
    "worsen",
    "positive for",
    "negative for",
    "risk of",
    "concern",
    # Gradings. A sentence that scores what it reports is scoring it:
    # "dominates", "significant revenue" and "remains strong" are the
    # writer's assessment wearing a reported fact's clothes, and they
    # are the sentences most likely to be mistaken for measurements.
    "dominat",
    "remains strong",
    "leading position",
    "significant",
    "elevated",
    "impressive",
    "robust",
    "healthy",
    "notable",
    "substantial",
    "dwarf",
    "outperform",
    "underperform",
)

#: Sentences asserting that one thing produced another. Kept apart from
#: the merely interpretive because §12 names them specifically, and
#: because they are the sentences a reader is most likely to mistake for
#: findings.
_CAUSAL = (
    "due to",
    "because",
    "driven by",
    "caused",
    "led to",
    "leading to",
    "as a result",
    "resulting in",
    "prompting",
    "prompted",
    "supporting",
    "supported by",
    "fuel",
    "spark",
    "triggered",
    "thanks to",
    "amid",
    "following the",
    "in response to",
    "helped",
    "pushing",
    "sending",
)

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9$])")


def sentences_in(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in _SENTENCE.split(text.strip()) if part.strip())


def decompose(
    text: str,
    source: str,
) -> tuple[tuple[EventFact, ...], tuple[Interpretation, ...]]:
    """Split one account into what it asserts and what it reads into it.

    **The marker decides, not the number.** The first draft of this rule
    required a quantity for a sentence to count as a fact, and it filed
    *"AUSTRAC suspended Cryptolink's VASP registration for three
    months"* as somebody's opinion — a regulator's action, reported
    plainly, with its only figure spelled as a word. A fact is a
    sentence that asserts something happened; a quantity is what makes
    it *checkable*, which is a different property and is carried in
    `anchors`.

    So a sentence is an interpretation when it hedges, grades or claims
    a cause, and a fact otherwise. Both directions of error were weighed
    and this one is the safe direction: an unhedged sentence that turns
    out to be wrong is a source's error, honestly attributed to the
    source, while a hedged sentence promoted to a fact is this platform
    lending its own authority to somebody's opinion.

    The **headline is not passed here**. It is the aggregator's framing
    of the event and it is already the event's name; decomposing it too
    produced every claim twice and asked whether *"Ethereum Dominates
    RWA Lending Deposits"* is a measurement.
    """

    facts: list[EventFact] = []
    readings: list[Interpretation] = []

    seen: set[str] = set()

    for sentence in sentences_in(text):
        lowered = _fold(sentence)

        key = re.sub(r"[^a-z0-9]+", " ", lowered).strip()

        if key in seen:
            continue

        seen.add(key)

        causal = any(marker in lowered for marker in _CAUSAL)
        interpretive = causal or any(marker in lowered for marker in _INTERPRETIVE)

        if interpretive:
            readings.append(
                Interpretation(stated=sentence, source=source, is_causal=causal)
            )
        else:
            facts.append(EventFact(stated=sentence, anchors=anchors_in(sentence)))

    return tuple(facts), tuple(readings)


@dataclass(frozen=True, slots=True)
class EventFeedHealth:
    """Whether a surface answered, and what it gave up if not.

    Carried because the CoinGecko insight surface is parsed HTML with no
    API behind it, and the failure mode of a parser against a page that
    changed is **zero events and no error**. An empty brief that cannot
    say why it is empty is the honest-looking absence this platform has
    been caught by before, so the count of entries seen and the count
    parsed are both kept, and a surface that returned rows it could not
    read says so.
    """

    source: str
    reached: bool

    entries_seen: int = 0
    entries_parsed: int = 0

    #: Entries this platform read and deliberately did not keep, with
    #: the reason. Counted apart from the ones it *could not* read,
    #: because those are opposite failures: a decline is a judgement and
    #: a parse miss is a broken surface, and one number for both would
    #: hide the second behind the first.
    declined: tuple[str, ...] = ()

    because: str | None = None

    @property
    def entries_declined(self) -> int:
        return len(self.declined)

    @property
    def is_degraded(self) -> bool:
        return self.reached and self.entries_seen > (
            self.entries_parsed + self.entries_declined
        )

    @property
    def stated(self) -> str:
        if not self.reached:
            return f"{self.source} could not be read{_tail(self.because)}"

        if self.is_degraded:
            missed = self.entries_seen - self.entries_parsed - self.entries_declined

            return (
                f"{self.source} returned {self.entries_seen} entries and "
                f"{missed} could not be read — its page shape may have changed"
            )

        tail = f", {self.entries_declined} declined" if self.entries_declined else ""

        return f"{self.source}: {self.entries_parsed} kept{tail}"


def _tail(because: str | None) -> str:
    return f" — {because}" if because else "."


@dataclass(frozen=True, slots=True)
class EventFeed:
    """One acquisition's events, and the health of the surfaces it asked."""

    events: tuple[CryptoEvent, ...] = ()
    health: tuple[EventFeedHealth, ...] = field(default=())

    @property
    def is_read(self) -> bool:
        return any(item.reached for item in self.health)

    @property
    def degraded(self) -> tuple[EventFeedHealth, ...]:
        return tuple(
            item for item in self.health if item.is_degraded or not item.reached
        )
