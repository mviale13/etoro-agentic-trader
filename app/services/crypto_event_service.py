"""One asset's material developments, from several surfaces, once.

Three jobs, in order, and each is a rule the ruling names.

**Collapse (§9).** Four sources reporting one exploit are one event.
Two accounts merge when they share an identity, and where they do not,
when they share the same subject, family and day *and* a figure. The
figure is what does the work: two outlets never choose the same words
and almost always quote the same number.

**Age (§10).** Intelligence is perishable, so every event carries a
relevance band and the stale ones leave the brief. The rule that matters
is the negative one: **a stale event is not kept merely because nothing
newer exists.** An empty section saying *no material current event* is
worth more than a fortnight-old headline presented as what is happening
now.

**Rank (§11).** A small set, chosen by ordered rules rather than by a
score. What kind of thing it is, then whether it is still running, then
how close the reporting gets, then whether anyone else carried it, then
how new it is. No weights, no thresholds, nothing to tune — this
platform has spent five slices declining to invent quality numbers, and
a materiality score for news would be exactly that.

**What this never does is decide.** An event may explain a durable fact
and may never rewrite one (§19), and nothing here reaches Asset Quality
in either direction (§18). Both are asserted by import test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.crypto_event import (
    CryptoEvent,
    EventFact,
    EventFamily,
    EventFeed,
    EventFeedHealth,
    EventStatus,
    Interpretation,
    SourceReport,
    SourceTier,
    anchors_in,
)
from app.domain.crypto_intelligence import Relevance, relevance_of
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.coin_insight_provider import CoinInsightProvider
from app.providers.press_corroboration_provider import (
    PressCorroborationProvider,
    corroborate,
)
from app.providers.primary_event_provider import PrimaryEventProvider

#: How many events a brief may carry. Small on purpose: the ruling asks
#: for *"a small number of material developments, not completeness"*,
#: and a list long enough to skim is a list nobody reads.
SHOWN = 5

#: How old an event may be and still be worth a reader's attention.
#: Longer than a flow reading's window because an exploit or a rule
#: change stays relevant after the day it happened, and far shorter than
#: a durable fact's, because none of this is durable.
LIVE_WITHIN_DAYS = 10


class CryptoEventService:
    """Material developments for one asset, deduplicated and ranked."""

    SCHEMA = 1

    def __init__(
        self,
        insights: CoinInsightProvider | None = None,
        primary: PrimaryEventProvider | None = None,
        press: PressCorroborationProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._insights = insights or CoinInsightProvider()
        self._primary = primary or PrimaryEventProvider()
        self._press = press or PressCorroborationProvider()
        self._cache = cache or JsonCache("data/cache/crypto_events", schema=self.SCHEMA)
        self._acquires = acquires

    @classmethod
    def stored(cls, cache: JsonCache | None = None) -> CryptoEventService:
        """What has already been read, and nothing else.

        The read-only door every surface goes through. A page view must
        never fetch, and this is what makes that checkable rather than
        promised.
        """

        return cls(cache=cache, acquires=False)

    # ── the read-only door ──────────────────────────────────────────

    def established(self, symbol: str, now: datetime | None = None) -> EventFeed:
        """Events already acquired for this asset. Never fetches."""

        entry = self._cache.read(f"events.{symbol.upper().strip()}")

        if entry is None:
            return EventFeed()

        feed = _decode(entry.value)

        return EventFeed(events=self._live(feed.events, now), health=feed.health)

    # ── acquisition ─────────────────────────────────────────────────

    def acquire(self, symbol: str, now: datetime | None = None) -> EventFeed:
        """Read every surface for this asset, collapse, and store."""

        if not self._acquires:
            return self.established(symbol, now)

        normalized = symbol.upper().strip()

        found: list[CryptoEvent] = []
        health: list[EventFeedHealth] = []

        for events, status in (
            self._insights.events(normalized, now),
            self._primary.incidents(normalized),
            self._primary.releases(normalized),
        ):
            found.extend(events)
            health.append(status)

        items, press_health = self._press.items()

        health.extend(press_health)

        collapsed = merge(found)

        # The press is asked only about events already found. It cannot
        # add one, which is what keeps this from being a news feed.
        witnessed = tuple(corroborate(event, items) for event in collapsed)

        feed = EventFeed(events=witnessed, health=tuple(health))

        self._cache.write(f"events.{normalized}", _encode(feed))

        return EventFeed(events=self._live(witnessed, now), health=feed.health)

    # ── age and rank ────────────────────────────────────────────────

    @staticmethod
    def _live(
        events: tuple[CryptoEvent, ...],
        now: datetime | None,
    ) -> tuple[CryptoEvent, ...]:
        """The events still worth reading, best first.

        Stale ones are dropped here rather than ranked last. Ranking
        them last would still show them once the list was short, which
        is precisely §10's *"do not keep a stale event because no newer
        event exists"*.
        """

        moment = now or datetime.now(UTC)

        fresh = [
            event
            for event in events
            if (age := event.age(moment)) is not None and age.days <= LIVE_WITHIN_DAYS
        ]

        fresh.sort(key=lambda event: event.rank(moment))

        return tuple(fresh)

    def material(
        self,
        symbol: str,
        now: datetime | None = None,
        limit: int = SHOWN,
    ) -> tuple[CryptoEvent, ...]:
        """The few developments worth putting in front of an investor."""

        return self.established(symbol, now).events[:limit]

    @staticmethod
    def relevance(event: CryptoEvent, now: datetime | None = None) -> Relevance:
        """Which band this event falls in, in slice 1's vocabulary."""

        return relevance_of(event.at, now)


def merge(events: list[CryptoEvent]) -> tuple[CryptoEvent, ...]:
    """Collapse accounts of one event into one event (§9).

    Two passes, because identity is a strong test and a slightly loose
    one is needed underneath it. First, exact identity — the same
    subject, family, day and figure. Then, for what remains, the same
    subject, family and day *plus a shared figure anywhere in the
    account*, which catches two outlets that headlined different aspects
    of one development.

    **Interpretations are never averaged.** Both sources' readings are
    kept, each with its own name on it. A merged event with two opposite
    readings beneath it is telling the truth; one reading synthesised
    from two is a sentence nobody published.
    """

    by_identity: dict[str, CryptoEvent] = {}

    for event in events:
        held = by_identity.get(event.identity)

        by_identity[event.identity] = _combine(held, event) if held else event

    merged: list[CryptoEvent] = []

    for event in by_identity.values():
        target = _same_event(merged, event)

        if target is None:
            merged.append(event)
            continue

        merged[merged.index(target)] = _combine(target, event)

    return tuple(merged)


def _same_event(held: list[CryptoEvent], candidate: CryptoEvent) -> CryptoEvent | None:
    """An already-merged event this one is another account of, or None."""

    anchors = _all_anchors(candidate)

    for event in held:
        if event.family is not candidate.family:
            continue

        if set(event.symbols) != set(candidate.symbols):
            continue

        if not _same_day(event, candidate):
            continue

        if anchors and (_all_anchors(event) & anchors):
            return event

    return None


def _all_anchors(event: CryptoEvent) -> set[str]:
    return {anchor for fact in event.facts for anchor in fact.anchors} | set(
        anchors_in(event.headline)
    )


def _same_day(left: CryptoEvent, right: CryptoEvent) -> bool:
    if left.at is None or right.at is None:
        return False

    return left.at.astimezone(UTC).date() == right.at.astimezone(UTC).date()


def _combine(held: CryptoEvent, other: CryptoEvent) -> CryptoEvent:
    """One event from two accounts of it, losing neither.

    The headline kept is the one from the closest source: a register's
    own wording beats a summary's. Everything else accumulates, and each
    source's sentences keep that source's name.
    """

    closer = other if _closeness(other) < _closeness(held) else held

    facts = list(held.facts)

    for fact in other.facts:
        twin = next(
            (item for item in facts if _folded(item.stated) == _folded(fact.stated)),
            None,
        )

        if twin is None:
            facts.append(fact)
            continue

        facts[facts.index(twin)] = twin.also_reported_by(fact.corroborated_by)

    return CryptoEvent(
        identity=held.identity,
        symbols=tuple(dict.fromkeys(held.symbols + other.symbols)),
        family=held.family,
        headline=closer.headline,
        # The earliest time any account gives it: an event happened once,
        # and the first report of it is the closest to when.
        occurred_at=_earliest(held.occurred_at, other.occurred_at),
        published_at=_earliest(held.published_at, other.published_at),
        observed_at=max(held.observed_at, other.observed_at),
        reports=_unique_reports(held.reports + other.reports),
        facts=tuple(facts),
        interpretations=held.interpretations + other.interpretations,
        # An event either account leaves unresolved is unresolved.
        status=(
            EventStatus.UNRESOLVED
            if EventStatus.UNRESOLVED in (held.status, other.status)
            else (
                EventStatus.ONGOING
                if EventStatus.ONGOING in (held.status, other.status)
                else EventStatus.COMPLETED
            )
        ),
        entity=held.entity or other.entity,
    )


def _closeness(event: CryptoEvent) -> int:
    return {SourceTier.PRIMARY: 0, SourceTier.SECONDARY: 1, SourceTier.AGGREGATOR: 2}[
        event.tier
    ]


def _unique_reports(reports: tuple[SourceReport, ...]) -> tuple[SourceReport, ...]:
    """One report per source, keeping the one that carries text."""

    best: dict[str, SourceReport] = {}

    for report in reports:
        held = best.get(report.source)

        if held is None or (not held.text and report.text):
            best[report.source] = report

    return tuple(best.values())


def _earliest(left: datetime | None, right: datetime | None) -> datetime | None:
    if left is None:
        return right

    if right is None:
        return left

    return min(left, right)


def _folded(text: str) -> str:
    return " ".join(text.lower().split())


# ── the store ───────────────────────────────────────────────────────


def _encode(feed: EventFeed) -> dict[str, Any]:
    return {
        "events": [_encode_event(event) for event in feed.events],
        "health": [
            {
                "source": item.source,
                "reached": item.reached,
                "entries_seen": item.entries_seen,
                "entries_parsed": item.entries_parsed,
                "declined": list(item.declined),
                "because": item.because,
            }
            for item in feed.health
        ],
    }


def _encode_event(event: CryptoEvent) -> dict[str, Any]:
    return {
        "identity": event.identity,
        "symbols": list(event.symbols),
        "family": event.family.value,
        "headline": event.headline,
        "occurred_at": _stamp(event.occurred_at),
        "published_at": _stamp(event.published_at),
        "observed_at": _stamp(event.observed_at),
        "status": event.status.value,
        "entity": event.entity,
        "reports": [
            {
                "source": report.source,
                "tier": report.tier.value,
                "text": report.text,
                "url": report.url,
                "published_at": _stamp(report.published_at),
            }
            for report in event.reports
        ],
        "facts": [
            {
                "stated": fact.stated,
                "anchors": list(fact.anchors),
                "corroborated_by": list(fact.corroborated_by),
            }
            for fact in event.facts
        ],
        "interpretations": [
            {
                "stated": item.stated,
                "source": item.source,
                "is_causal": item.is_causal,
            }
            for item in event.interpretations
        ],
    }


def _decode(row: Any) -> EventFeed:
    if not isinstance(row, dict):
        return EventFeed()

    events: list[CryptoEvent] = []

    for item in row.get("events") or []:
        event = _decode_event(item)

        if event is not None:
            events.append(event)

    health: list[EventFeedHealth] = []

    for item in row.get("health") or []:
        if not isinstance(item, dict):
            continue

        health.append(
            EventFeedHealth(
                source=str(item.get("source", "")),
                reached=bool(item.get("reached")),
                entries_seen=int(item.get("entries_seen") or 0),
                entries_parsed=int(item.get("entries_parsed") or 0),
                declined=tuple(item.get("declined") or ()),
                because=item.get("because"),
            )
        )

    return EventFeed(events=tuple(events), health=tuple(health))


def _decode_event(row: Any) -> CryptoEvent | None:
    if not isinstance(row, dict):
        return None

    try:
        return CryptoEvent(
            identity=str(row["identity"]),
            symbols=tuple(row["symbols"]),
            family=EventFamily(row["family"]),
            headline=str(row["headline"]),
            occurred_at=_time(row.get("occurred_at")),
            published_at=_time(row.get("published_at")),
            observed_at=_time(row["observed_at"]) or datetime.now(UTC),
            status=EventStatus(row.get("status", EventStatus.COMPLETED.value)),
            entity=row.get("entity"),
            reports=tuple(
                SourceReport(
                    source=str(item["source"]),
                    tier=SourceTier(item["tier"]),
                    text=str(item.get("text") or ""),
                    url=item.get("url"),
                    published_at=_time(item.get("published_at")),
                )
                for item in row.get("reports") or []
                if isinstance(item, dict)
            ),
            facts=tuple(
                EventFact(
                    stated=str(item["stated"]),
                    anchors=tuple(item.get("anchors") or ()),
                    corroborated_by=tuple(item.get("corroborated_by") or ()),
                )
                for item in row.get("facts") or []
                if isinstance(item, dict)
            ),
            interpretations=tuple(
                Interpretation(
                    stated=str(item["stated"]),
                    source=str(item["source"]),
                    is_causal=bool(item.get("is_causal")),
                )
                for item in row.get("interpretations") or []
                if isinstance(item, dict)
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _stamp(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
