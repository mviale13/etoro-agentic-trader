"""What this platform knew about an asset, and when it knew it.

Every slice so far answers a question about *now*. The journal is the
first thing here with a memory, and it exists because five sentences a
reader would treat completely differently are, to a point-in-time
system, the same sentence:

```text
ETF flows are positive today.
ETF flows have been positive for three weeks.
ETF flows turned positive today after three negative weeks.
ETF flows were positive but are weakening.
Nothing materially changed.
```

**It stores observations, never conclusions.** A journal entry is one
finding as one capture read it, with the value, the source, and the time
the source itself gave. Nothing in this module knows what any of it
means, and no model is ever asked to remember — *code establishes
history; the model explains grounded history*, and the moment those
swap, the platform's memory becomes something that can be argued with.

**Append-only means append-only.** A later run does not rewrite
yesterday because today's parser is better. The question the journal
answers is *what did MOVRvest actually know about BTC on 1 August* —
not *what would today's pipeline say about evidence dated 1 August*.
Those are different questions and only the first is a record. A
correction is therefore a new entry that names what it corrects, never
an edit.

**Three things can change, and conflating them would be the worst
defect this layer could ship:**

```text
the world changed          the source published a new figure for a new day
our evidence changed       the source revised a figure it had already given
our reading changed        we could not read what we read last time
```

The third is not an economic event. A provider outage that arrives as
*"institutional holdings fell to zero"* is a lie assembled out of true
parts, and `ObservationStatus` exists so that it cannot be assembled.

**And the hardest rule, which is about honesty rather than
correctness**: three observations across three weeks are not three weeks
of continuous conditions. The journal knows how many times it looked,
when it first and last looked, and the longest it went without looking.
Every temporal statement is worded from those and may never imply
monitoring this platform did not do.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.domain.crypto_intelligence import ClaimType, EventKind


class ObservationStatus(StrEnum):
    """Whether a finding was seen, and if not, why not.

    The distinction §6 turns on. A finding that is absent because the
    question does not arise, a finding absent because a surface broke,
    and a finding present with a value of zero are three different facts
    about the world, and exactly one of them is an economic observation.
    """

    #: Read, with whatever the source gave.
    OBSERVED = "observed"

    #: This platform asked and could not read it — a provider outage, a
    #: parse failure, a surface that changed shape. **Never an economic
    #: event**, and never comparable with a value.
    UNAVAILABLE = "unavailable"

    #: The question does not arise for this asset. Hyperliquid has no US
    #: spot ETF, so it has no flow reading — which is not a gap.
    NOT_APPLICABLE = "not_applicable"

    @property
    def stated(self) -> str:
        return {
            ObservationStatus.OBSERVED: "observed",
            ObservationStatus.UNAVAILABLE: "could not be read",
            ObservationStatus.NOT_APPLICABLE: "does not apply",
        }[self]

    @property
    def is_evidence(self) -> bool:
        """Whether this may be compared with another observation at all."""

        return self is ObservationStatus.OBSERVED


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """One finding, as one capture read it. Immutable, forever.

    `key` is what makes two entries comparable — the claim's own ref or
    an event's identity, both already stable across captures. Everything
    else describes that one reading.
    """

    #: The run that produced it. Every entry from one acquisition shares
    #: this, so a capture can be read back whole.
    capture_id: str

    asset: str

    #: When this platform looked.
    captured_at: datetime

    #: What was observed — stable across captures by construction.
    key: str

    family: EventKind
    claim_type: ClaimType

    status: ObservationStatus

    #: The sentence, as the deterministic layer worded it.
    stated: str

    #: The measurement, where one genuinely exists. **Left absent for
    #: qualitative findings rather than encoded**: inventing a number so
    #: that a regulatory action can be compared with a fee reading would
    #: make the comparison possible and meaningless.
    value: float | None = None
    unit: str | None = None

    source: str | None = None

    #: When the *source* says its figure is from, where it says. A flow
    #: settles days before it is published, and comparing two captures
    #: on the day this platform looked would call a re-read a change.
    source_observed_at: datetime | None = None

    #: Provenance from the claim itself — the refs a surface can follow.
    refs: tuple[str, ...] = ()

    #: The entry this one corrects, where it corrects one. History keeps
    #: both: a correction is a fact about this platform, and hiding it
    #: would make the record less true than the mistake was.
    corrects: str | None = None

    @property
    def entry_id(self) -> str:
        """A stable handle a temporal fact can cite."""

        return f"{self.capture_id}:{self.key}"

    def same_reading_as(self, other: JournalEntry) -> bool:
        """Whether two entries say the same thing about the same key.

        Value where there is one, wording otherwise. Both sides must be
        evidence: an unavailable reading is not equal to anything,
        including another unavailable reading.
        """

        if not (self.status.is_evidence and other.status.is_evidence):
            return False

        if self.value is not None and other.value is not None:
            return self.value == other.value and self.unit == other.unit

        if self.value is None and other.value is None:
            return self.stated == other.stated

        return False


class ChangeNature(StrEnum):
    """Which of the three things that can change, changed.

    §6, made structural. The distinction rests on the *source's* own
    timestamp rather than on ours: a new figure for a new day is the
    world moving, and a new figure for a day already reported is the
    source revising itself.
    """

    #: The source published a figure for a later moment.
    WORLD_MOVED = "world_moved"

    #: The source changed a figure it had already given for the same
    #: moment. Our evidence changed; the world did not.
    SOURCE_REVISED = "source_revised"

    #: We could read it before and cannot now, or the reverse. **Not an
    #: economic event.**
    READING_CHANGED = "reading_changed"

    #: The source gave no time, so the two cannot be told apart. Said
    #: rather than guessed.
    UNDETERMINED = "undetermined"

    @property
    def stated(self) -> str:
        return {
            ChangeNature.WORLD_MOVED: "the source reported a later reading",
            ChangeNature.SOURCE_REVISED: (
                "the source revised a figure it had already given"
            ),
            ChangeNature.READING_CHANGED: (
                "this platform's ability to read it changed, which is not an "
                "economic event"
            ),
            ChangeNature.UNDETERMINED: (
                "the source dates nothing, so a revision and a new reading "
                "cannot be told apart"
            ),
        }[self]


class TemporalStatus(StrEnum):
    """What the history of one key says, and nothing more.

    Deliberately a description of *observations*, not of the asset.
    `INCREASED` means a measured figure is larger than the one before
    it; it does not mean demand strengthened, and the layer that says so
    is downstream.
    """

    #: Seen for the first time in the window.
    FIRST_OBSERVED = "first_observed"

    #: Seen again, saying the same thing.
    STILL_PRESENT = "still_present"

    #: Seen again, saying something different, with no direction
    #: available — a qualitative finding, or one with no measurement.
    CHANGED = "changed"

    #: Measured, and larger than the previous measurement.
    INCREASED = "increased"

    #: Measured, and smaller than the previous measurement.
    DECREASED = "decreased"

    #: Present before and not in the latest capture at all.
    DISAPPEARED = "disappeared"

    #: Asked for and unreadable. Never comparable with a value.
    UNAVAILABLE = "unavailable"

    @property
    def stated(self) -> str:
        return _TEMPORAL[self]

    @property
    def is_change(self) -> bool:
        return self in (
            TemporalStatus.CHANGED,
            TemporalStatus.INCREASED,
            TemporalStatus.DECREASED,
        )


_TEMPORAL = {
    TemporalStatus.FIRST_OBSERVED: "first observed",
    TemporalStatus.STILL_PRESENT: "unchanged since the previous capture",
    TemporalStatus.CHANGED: "changed",
    TemporalStatus.INCREASED: "higher than the previous reading",
    TemporalStatus.DECREASED: "lower than the previous reading",
    TemporalStatus.DISAPPEARED: "not in the latest capture",
    TemporalStatus.UNAVAILABLE: "could not be read this time",
}


@dataclass(frozen=True, slots=True)
class ObservationSpan:
    """How often this platform looked, and how far apart.

    The object §5 exists for. *"For three weeks"* is a claim about
    coverage, and this platform almost never has coverage — it has
    captures. So every temporal statement is worded from these four
    numbers, and the wording says **captures**, never duration alone.

    `largest_gap` is the honest one: three captures spanning twenty-one
    days with a nineteen-day hole is not three weeks of observation, and
    it is the only field that can say so.
    """

    count: int
    first_at: datetime
    last_at: datetime
    largest_gap: timedelta

    @property
    def span(self) -> timedelta:
        return self.last_at - self.first_at

    @property
    def stated(self) -> str:
        """How this platform is allowed to describe its own coverage."""

        if self.count == 1:
            return "on one capture"

        days = max(self.span.days, 0)

        window = f" spanning {days} day(s)" if days else " on the same day"

        gap = self.largest_gap.days

        hole = f", the longest gap between them {gap} day(s)" if gap >= 2 else ""

        return f"on {self.count} captures{window}{hole}"


@dataclass(frozen=True, slots=True)
class TemporalFact:
    """What the record says about one key over time, and where to check.

    A deterministic reading of journal entries — no model, no
    interpretation, and no investment meaning. *"Positive on three
    consecutive captures"* is what this may say; *"demand is
    strengthening"* is not, and belongs to a layer that does not exist
    yet.
    """

    key: str
    asset: str

    status: TemporalStatus

    #: The sentence a surface prints and a synthesis may cite.
    stated: str

    span: ObservationSpan

    #: The journal entries this rests on. Never empty — a temporal fact
    #: that cannot be checked against the record is not one.
    entry_ids: tuple[str, ...]

    #: For a measured change, the two figures. Absent otherwise.
    previous_value: float | None = None
    current_value: float | None = None
    unit: str | None = None

    #: Which of the three kinds of change this was, where it changed.
    nature: ChangeNature | None = None

    #: How many consecutive most-recent captures agreed. Only ever a
    #: count of captures, never a duration.
    run_length: int = 1

    @property
    def is_grounded(self) -> bool:
        return bool(self.entry_ids)


@dataclass(frozen=True, slots=True)
class Capture:
    """One acquisition of one asset, whole."""

    capture_id: str
    asset: str
    captured_at: datetime
    entries: tuple[JournalEntry, ...] = ()

    @property
    def keys(self) -> frozenset[str]:
        return frozenset(entry.key for entry in self.entries)

    def entry(self, key: str) -> JournalEntry | None:
        for item in self.entries:
            if item.key == key:
                return item

        return None


def capture_id_for(asset: str, captured_at: datetime, payload: str) -> str:
    """A stable identity for one capture.

    Derived from what was captured rather than randomly assigned, so
    replaying an acquisition twice is visible as two captures of the
    same content rather than as two unrelated runs.
    """

    digest = hashlib.sha256(
        f"{asset}|{captured_at.isoformat()}|{payload}".encode()
    ).hexdigest()

    return f"{captured_at:%Y%m%dT%H%M%S}-{digest[:8]}"


# ── the projection ──────────────────────────────────────────────────


def project(
    asset: str,
    history: list[Capture],
    now: datetime | None = None,
) -> tuple[TemporalFact, ...]:
    """Read the record and state what it says. No interpretation.

    Ordered oldest first. The latest capture is the one being described;
    everything before it is what makes a description possible.

    Two rules the implementation turns on. **An unavailable reading is
    never compared with a value** — it produces its own status and stops,
    because a surface that broke is not a measurement that fell. And
    **direction requires a measurement on both sides**: a qualitative
    finding that changed is `CHANGED`, full stop, since inventing a
    number to order two sentences would make them comparable and not
    meaningful.
    """

    if not history:
        return ()

    ordered = sorted(history, key=lambda capture: capture.captured_at)

    latest = ordered[-1]

    facts: list[TemporalFact] = []

    seen_keys = {key for capture in ordered for key in capture.keys}

    for key in sorted(seen_keys):
        entries = [
            entry for capture in ordered if (entry := capture.entry(key)) is not None
        ]

        if not entries:
            continue

        fact = _fact_for(asset, key, entries, latest)

        if fact is not None:
            facts.append(fact)

    return tuple(facts)


def _span(entries: list[JournalEntry]) -> ObservationSpan:
    times = [entry.captured_at for entry in entries]

    gaps = [later - earlier for earlier, later in zip(times, times[1:], strict=False)]

    return ObservationSpan(
        count=len(entries),
        first_at=times[0],
        last_at=times[-1],
        largest_gap=max(gaps) if gaps else timedelta(0),
    )


def _fact_for(
    asset: str,
    key: str,
    entries: list[JournalEntry],
    latest: Capture,
) -> TemporalFact | None:
    span = _span(entries)

    current = entries[-1]

    ids = tuple(entry.entry_id for entry in entries)

    # Present before, and not in the latest capture at all. Distinct from
    # unavailable: nothing said it could not be read, it simply was not
    # produced this time.
    if current.capture_id != latest.capture_id:
        return TemporalFact(
            key=key,
            asset=asset,
            status=TemporalStatus.DISAPPEARED,
            stated=(
                f"{current.stated} — last seen {current.captured_at:%-d %B}, "
                f"and not produced by the latest capture. Observed "
                f"{span.stated}."
            ),
            span=span,
            entry_ids=ids,
        )

    if current.status is ObservationStatus.NOT_APPLICABLE:
        return None

    if current.status is ObservationStatus.UNAVAILABLE:
        return TemporalFact(
            key=key,
            asset=asset,
            status=TemporalStatus.UNAVAILABLE,
            stated=(
                f"{current.stated} This platform could not read it in the "
                "latest capture, which is a fact about the reading and not "
                "about the asset."
            ),
            span=span,
            entry_ids=ids,
            nature=ChangeNature.READING_CHANGED,
        )

    previous = next(
        (entry for entry in reversed(entries[:-1]) if entry.status.is_evidence),
        None,
    )

    if previous is None:
        return TemporalFact(
            key=key,
            asset=asset,
            status=TemporalStatus.FIRST_OBSERVED,
            stated=f"{current.stated} First observed {span.stated}.",
            span=span,
            entry_ids=ids,
            current_value=current.value,
            unit=current.unit,
        )

    if current.same_reading_as(previous):
        run = _run_length(entries)

        return TemporalFact(
            key=key,
            asset=asset,
            status=TemporalStatus.STILL_PRESENT,
            stated=(
                f"{current.stated} Unchanged across the last {run} "
                f"capture(s); observed {span.stated}."
            ),
            span=span,
            entry_ids=ids,
            current_value=current.value,
            unit=current.unit,
            run_length=run,
        )

    status = TemporalStatus.CHANGED

    movement = ""

    if current.value is not None and previous.value is not None:
        if current.value > previous.value:
            status = TemporalStatus.INCREASED
        elif current.value < previous.value:
            status = TemporalStatus.DECREASED

        movement = (
            f" The previous reading, on {previous.captured_at:%-d %B}, was "
            f"{_figure(previous.value, previous.unit)}."
        )

    nature = _nature(previous, current)

    return TemporalFact(
        key=key,
        asset=asset,
        status=status,
        stated=(
            f"{current.stated}{movement} Compared with the capture before "
            f"it, {nature.stated}. Observed {span.stated}."
        ),
        span=span,
        entry_ids=ids,
        previous_value=previous.value,
        current_value=current.value,
        unit=current.unit,
        nature=nature,
    )


def _nature(previous: JournalEntry, current: JournalEntry) -> ChangeNature:
    """Whether the world moved, the source revised, or we read differently."""

    if not (previous.status.is_evidence and current.status.is_evidence):
        return ChangeNature.READING_CHANGED

    if previous.source_observed_at is None or current.source_observed_at is None:
        return ChangeNature.UNDETERMINED

    if current.source_observed_at > previous.source_observed_at:
        return ChangeNature.WORLD_MOVED

    if current.source_observed_at == previous.source_observed_at:
        return ChangeNature.SOURCE_REVISED

    # The source's own clock went backwards, which is a fact about the
    # source rather than about the asset.
    return ChangeNature.UNDETERMINED


def _run_length(entries: list[JournalEntry]) -> int:
    """How many consecutive most-recent captures agreed.

    **A count of captures and never a duration.** The wording built from
    it says *"across the last 3 captures"* precisely so that a reader
    cannot take three weeks of monitoring from three weekly looks.
    """

    run = 1

    for earlier, later in zip(reversed(entries[:-1]), reversed(entries), strict=False):
        if not later.same_reading_as(earlier):
            break

        run += 1

    return run


def _figure(value: float | None, unit: str | None) -> str:
    if value is None:
        return "absent"

    if unit == "USD":
        return _money(value)

    if unit == "%":
        return f"{value:+.1f}%"

    return f"{value:,.0f}{f' {unit}' if unit else ''}"


def _money(value: float) -> str:
    sign = "-" if value < 0 else ""

    size = abs(value)

    if size >= 1_000_000_000:
        return f"{sign}${size / 1_000_000_000:,.1f}bn"

    if size >= 1_000_000:
        return f"{sign}${size / 1_000_000:,.0f}m"

    if size >= 1_000:
        return f"{sign}${size / 1_000:,.0f}k"

    return f"{sign}${size:,.0f}"


def utc(moment: datetime | None = None) -> datetime:
    return moment or datetime.now(UTC)
