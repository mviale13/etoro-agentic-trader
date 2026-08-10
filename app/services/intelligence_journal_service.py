"""Record what a capture saw, and read back what the record says.

Two halves, deliberately apart, because §4 of the ruling is that the
journal must not be an analyst. `record` writes observations and knows
nothing about change; `history` reads them and states what the record
says without saying what it means.

**What gets recorded is the canonical snapshot, not the synthesis.** The
model's prose is a reading of evidence and is never evidence, so it is
not written here — storing it would make yesterday's synthesis into
today's history, and a mistake would become a fact.

**An absent finding is recorded as absent, with its reason.** That is
what lets the projection distinguish a provider outage from a
measurement that fell, and it is why the surfaces the snapshot could not
read are written as entries in their own right rather than dropped.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.crypto_intelligence import (
    ClaimType,
    CryptoIntelligenceSnapshot,
    EventKind,
)
from app.domain.intelligence_journal import (
    Capture,
    JournalEntry,
    ObservationStatus,
    TemporalFact,
    capture_id_for,
    project,
    utc,
)
from app.infrastructure.evidence.intelligence_journal_store import (
    IntelligenceJournalStore,
)

#: How many captures a projection reads back. Enough to describe a run
#: without turning a brief into an archive.
WINDOW = 12


class IntelligenceJournalService:
    """The platform's memory of one asset."""

    def __init__(self, store: IntelligenceJournalStore | None = None) -> None:
        self._store = store or IntelligenceJournalStore()

    # ── writing ─────────────────────────────────────────────────────

    def record(
        self,
        snapshot: CryptoIntelligenceSnapshot,
        now: datetime | None = None,
    ) -> Capture | None:
        """Write one capture of this snapshot, or None if already held.

        Every live claim becomes an entry, every development becomes an
        entry, and every surface that could not be read becomes an
        `UNAVAILABLE` entry — so the record says *we looked and failed*
        rather than falling silent, which is the only way the next run
        can tell an outage from a change.
        """

        moment = utc(now)

        entries = _entries_for(snapshot, moment)

        if not entries:
            return None

        # Derived from content, so replaying an unchanged acquisition
        # appends nothing rather than inventing a second observation.
        capture_id = capture_id_for(
            snapshot.symbol,
            moment,
            "|".join(f"{entry.key}={entry.stated}" for entry in entries),
        )

        capture = Capture(
            capture_id=capture_id,
            asset=snapshot.symbol,
            captured_at=moment,
            entries=tuple(
                JournalEntry(
                    capture_id=capture_id,
                    asset=snapshot.symbol,
                    captured_at=moment,
                    key=entry.key,
                    family=entry.family,
                    claim_type=entry.claim_type,
                    status=entry.status,
                    stated=entry.stated,
                    value=entry.value,
                    unit=entry.unit,
                    source=entry.source,
                    source_observed_at=entry.source_observed_at,
                    refs=entry.refs,
                )
                for entry in entries
            ),
        )

        return capture if self._store.append(capture) else None

    # ── reading ─────────────────────────────────────────────────────

    def captures(self, asset: str, limit: int = WINDOW) -> list[Capture]:
        return self._store.captures(asset, limit=limit)

    def history(
        self,
        asset: str,
        now: datetime | None = None,
        limit: int = WINDOW,
    ) -> tuple[TemporalFact, ...]:
        """What the record says about this asset. Deterministic."""

        return project(
            asset.upper().strip(),
            self._store.captures(asset, limit=limit),
            now,
        )

    def notable(
        self,
        asset: str,
        now: datetime | None = None,
        limit: int = 6,
    ) -> tuple[TemporalFact, ...]:
        """The temporal facts worth putting in front of a reader.

        Ranked by what a reader would notice, not scored: something that
        stopped being readable first, then something that changed, then
        something that has held. A key seen once and unchanged since is
        the least interesting thing the record contains.
        """

        facts = self.history(asset, now, limit=WINDOW)

        def rank(fact: TemporalFact) -> tuple[int, int]:
            order = {
                "unavailable": 0,
                "disappeared": 1,
                "increased": 2,
                "decreased": 2,
                "changed": 3,
                "first_observed": 4,
                "still_present": 5,
            }

            return (order.get(fact.status.value, 9), -fact.run_length)

        return tuple(sorted(facts, key=rank))[:limit]


# ── snapshot → observations ─────────────────────────────────────────


class _Observation:
    """One thing worth recording, flattened out of the snapshot."""

    __slots__ = (
        "claim_type",
        "family",
        "key",
        "refs",
        "source",
        "source_observed_at",
        "stated",
        "status",
        "unit",
        "value",
    )

    def __init__(
        self,
        key: str,
        family: EventKind,
        claim_type: ClaimType,
        status: ObservationStatus,
        stated: str,
        value: float | None = None,
        unit: str | None = None,
        source: str | None = None,
        source_observed_at: datetime | None = None,
        refs: tuple[str, ...] = (),
    ) -> None:
        self.key = key
        self.family = family
        self.claim_type = claim_type
        self.status = status
        self.stated = stated
        self.value = value
        self.unit = unit
        self.source = source
        self.source_observed_at = source_observed_at
        self.refs = refs


def _entries_for(
    snapshot: CryptoIntelligenceSnapshot,
    moment: datetime,
) -> list[_Observation]:
    observations: list[_Observation] = []

    events = {event.identity for event in snapshot.events}

    for claim in snapshot.live:
        if claim.ref in events:
            # A development is recorded from the event itself below,
            # which carries its sources and its own time.
            continue

        observations.append(
            _Observation(
                key=claim.ref,
                family=claim.kind,
                claim_type=claim.claim_type,
                status=ObservationStatus.OBSERVED,
                stated=claim.stated,
                value=claim.value,
                unit=claim.unit,
                source=claim.source,
                # The source's own moment, not ours: a flow settles days
                # before it is published, and comparing on the day this
                # platform looked would read a re-read as a change.
                source_observed_at=claim.event_at or claim.observed_at,
                refs=(claim.ref,),
            )
        )

    for event in snapshot.events:
        observations.append(
            _Observation(
                key=event.identity,
                family=EventKind.MARKET_NARRATIVE
                if event.tier.value == "aggregator"
                else EventKind.NETWORK_ACTIVITY,
                claim_type=ClaimType.REPORTED,
                status=ObservationStatus.OBSERVED,
                stated=f"{event.family.stated}: {event.headline}",
                source=", ".join(event.sources[:3]),
                source_observed_at=event.at,
                refs=(event.identity,),
            )
        )

    # Surfaces that were asked and could not be read. Recorded rather
    # than dropped: silence and failure look identical in a record that
    # only writes successes, and the next run needs to tell them apart.
    for index, unread in enumerate(snapshot.surfaces_unread, start=1):
        observations.append(
            _Observation(
                key=f"surface.{index}",
                family=EventKind.MARKET_BEHAVIOUR,
                claim_type=ClaimType.UNRESOLVED,
                status=ObservationStatus.UNAVAILABLE,
                stated=unread,
                source=None,
                source_observed_at=None,
            )
        )

    return observations
