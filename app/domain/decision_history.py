"""What the Artificial CIO decided before.

These are facts about decisions that were actually made and recorded. They
carry no judgement about whether those decisions were right: outcome
analysis is a separate concern, and nothing here estimates it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.cio.decision_state import DecisionState
from app.domain.score_basis import SCORE_LABELS


class TrendDirection(StrEnum):
    """Which way an investment case has been moving."""

    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"


@dataclass(frozen=True, slots=True)
class DecisionTrend:
    """
    Where this case has come from, in one reading.

    "PREPARE was also the previous decision, recorded on August 4" is
    accurate and asks the reader to do the comparison themselves. The
    direction is the thing they were computing — whether the case is
    getting better or worse — so it is computed once, here, from the
    lifecycle ranks the states already carry.

    It describes recorded decisions and nothing else. It is not a forecast
    and it is not a judgement about whether those decisions were right;
    what they were worth is the track record's question.
    """

    direction: TrendDirection

    #: The trend as the investor reads it, movement and figures included.
    stated: str


@dataclass(frozen=True, slots=True)
class RecordedScores:
    """
    The scores a decision was made on, as they stood when it was made.

    Every one of them runs the same way — higher is better for the case —
    so a rise is an improvement whichever it is, and the five can be
    compared against a later reading without one of them meaning the
    opposite of the others.

    A score the platform could not measure is None here too. It is never
    filled in, and a comparison against it is simply not made.
    """

    quality: int | None = None
    evidence: int | None = None
    valuation: int | None = None
    safety: int | None = None
    portfolio_fit: int | None = None

    @property
    def is_empty(self) -> bool:
        """Whether nothing at all was recorded — an older decision."""

        return all(getattr(self, name) is None for name in SCORE_LABELS)


@dataclass(frozen=True, slots=True)
class ConvictionChange:
    """
    How far the Artificial CIO's conviction moved, and what moved under it.

    The figure is arithmetic on two recorded numbers. The reasons are not
    inferred: each is a score that measurably differed between the two
    decisions, named and quoted. Where the earlier decision predates the
    scores being recorded there are no reasons to give, and this says so
    rather than presenting an empty list as "nothing changed".
    """

    #: What the conviction was when the CIO last judged this security.
    previous: int

    #: How far it moved, signed. Never zero: an unchanged conviction is
    #: no change, and is reported as the absence of this object.
    delta: int

    #: The scores that moved, worded. Empty when none did, and also when
    #: none could be compared — `unexplained` tells those apart.
    because: tuple[str, ...] = ()

    #: True when the earlier decision was recorded before this platform
    #: kept its scores, so what moved underneath cannot be said.
    unexplained: bool = False

    @property
    def stated(self) -> str:
        """The movement as the investor reads it, sign included."""

        return f"{'+' if self.delta > 0 else ''}{self.delta} conviction"


@dataclass(frozen=True, slots=True)
class RecordedTransition:
    """One time the Artificial CIO's decision changed, and what moved under it.

    Composed from two adjacent records and from nothing else. The
    rationale is the one the CIO recorded *at the time* — never a fresh
    sentence written now about a decision taken then — and what moved is
    arithmetic over the scores both records carry.
    """

    at: datetime

    from_state: str
    to_state: str

    #: Either side may be absent, and an absent conviction is not a low
    #: one. `stated` words the transition without it rather than printing
    #: a blank where a number belongs.
    from_conviction: int | None
    to_conviction: int | None

    #: The rationale recorded with the later decision, verbatim.
    rationale: str

    #: Each score that measurably differed, worded — including a score
    #: that stopped being measurable, which is not the same as one that
    #: fell.
    moved: tuple[str, ...] = ()

    #: True where the earlier record predates the journal keeping scores,
    #: so what moved underneath cannot be said at all.
    unexplained: bool = False

    @property
    def stated(self) -> str:
        """The change as the investor reads it.

        The state change is the fact; the conviction move is a detail
        beneath it, and is named only where both sides carry a number.
        """

        change = f"{self.from_state} → {self.to_state}"

        if self.from_conviction is None or self.to_conviction is None:
            return change

        return f"{change}, conviction {self.from_conviction} → {self.to_conviction}"


@dataclass(frozen=True, slots=True)
class DecisionCourse:
    """Every recorded change of mind about one security, and what moved.

    The journal has held this the whole time — it is what the home
    page's change feed is built from — and the dossier said only
    "Stable". This is that record composed for the case it belongs to.

    It judges nothing. Whether those decisions were *right* is the track
    record's question, and nothing here estimates it.
    """

    symbol: str

    #: How many decisions are recorded, and how many of them changed the
    #: state. Counted, never estimated.
    reviews: int
    changes: int

    first_recorded_at: datetime | None
    last_recorded_at: datetime | None

    #: Most recent first, so the investor reads the latest change first.
    transitions: tuple[RecordedTransition, ...] = ()

    #: The course in one sentence, worded here so no surface composes it.
    stated: str = ""

    #: Why there is no course to show. Set only where there is none.
    absent_because: str | None = None


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """One decision the Artificial CIO made, as it was recorded."""

    symbol: str
    state: DecisionState

    #: None where the CIO withheld one. Read back as it was written: a
    #: record that carried no conviction must not decode as a zero, or
    #: the next cycle reports a rise out of an absence.
    conviction: int | None
    rationale: str
    decided_at: datetime

    #: The scores it was decided on. Empty for decisions recorded before
    #: the journal kept them — an absence, never a set of zeroes.
    scores: RecordedScores = field(default_factory=RecordedScores)


@dataclass(frozen=True, slots=True)
class DecisionHistory:
    """Every recorded decision for one symbol, oldest first."""

    symbol: str
    records: tuple[DecisionRecord, ...] = field(default_factory=tuple)

    @property
    def is_empty(self) -> bool:
        return not self.records

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def first(self) -> DecisionRecord | None:
        return self.records[0] if self.records else None

    @property
    def latest(self) -> DecisionRecord | None:
        return self.records[-1] if self.records else None

    @property
    def current_state(self) -> DecisionState | None:
        latest = self.latest

        return latest.state if latest is not None else None

    @property
    def current_run(self) -> tuple[DecisionRecord, ...]:
        """The unbroken run of records ending in the current state."""

        state = self.current_state

        if state is None:
            return ()

        run: list[DecisionRecord] = []

        for record in reversed(self.records):
            if record.state is not state:
                break

            run.append(record)

        return tuple(reversed(run))

    @property
    def current_state_since(self) -> datetime | None:
        """When the current state was first recorded."""

        run = self.current_run

        return run[0].decided_at if run else None

    @property
    def previous_state(self) -> DecisionState | None:
        """The state held immediately before the current one."""

        run_length = len(self.current_run)

        if run_length == 0 or run_length == len(self.records):
            return None

        return self.records[-run_length - 1].state

    def trend_against(self, state: DecisionState) -> DecisionTrend | None:
        """
        How this case has moved, ending at the decision just taken.

        None where nothing was ever recorded. A symbol the Artificial CIO
        is judging for the first time has no trend, and calling that
        "stable" would report a run of one as a settled view.

        The decision passed in is today's, which is not yet in the record —
        the Brain perceived this history before the cycle began — so a run
        it continues is counted including it.

        **A run is not a period.** Volkswagen's run of six reviews began
        at 20:45 on 9 August, and earlier that same day the case had been
        PREPARE at 15:32 and INVESTIGATE at 17:36 — three states in five
        hours. "Stable — 6 consecutive reviews since 2026-08-09" was
        arithmetically right about the run and told the investor the case
        had been steady since a date on which it moved twice. So the
        "since" claim is made only where the run *is* the whole record;
        where the case changed before it, the run is stated as a run and
        the changes are counted rather than hidden behind a date.
        """

        recorded = self.current_state

        if recorded is None:
            return None

        if state is recorded:
            reviews = len(self.current_run) + 1
            changes = self.state_changes

            if changes:
                return DecisionTrend(
                    direction=TrendDirection.STABLE,
                    stated=(
                        f"{recorded.value} across the last {reviews} reviews — "
                        f"the case changed {changes} time{'s' if changes > 1 else ''} "
                        "before that"
                    ),
                )

            since = self.current_state_since

            when = f" since {since.date().isoformat()}" if since is not None else ""

            return DecisionTrend(
                direction=TrendDirection.STABLE,
                stated=f"Stable — {reviews} consecutive reviews{when}",
            )

        direction = (
            TrendDirection.IMPROVING
            if state.lifecycle_rank > recorded.lifecycle_rank
            else TrendDirection.DETERIORATING
        )

        return DecisionTrend(
            direction=direction,
            stated=(
                f"{direction.value.capitalize()} — {recorded.value} → {state.value}"
            ),
        )

    def conviction_change_against(
        self,
        conviction: int | None,
        scores: RecordedScores,
        labels: Mapping[str, str] = SCORE_LABELS,
    ) -> ConvictionChange | None:
        """
        How today's conviction differs from the last recorded one, and why.

        None where nothing was recorded, and none where the figure did not
        move: an unchanged conviction is not a change, and reporting it as
        one would put an arrow on every case every day.

        Each reason names a score that measurably differed. Nothing is
        attributed that cannot be shown, so a score missing on either side
        is passed over rather than guessed at, and an earlier decision
        recorded before the scores were produces the movement with an
        honest silence about its causes.

        The same rule now governs the conviction itself. A movement is
        arithmetic between two numbers, so where either side has none there
        is no movement to report — a case that gained or lost its *licence*
        to carry a conviction did not thereby gain or lose conviction, and
        subtracting against a withheld figure would publish the difference
        as a change of mind.

        `labels` is how the caller's dossier kind names the scores — a
        token's quality moving is an asset-quality move, not a business-
        quality one. The keys are the record's and never vary.
        """

        latest = self.latest

        if latest is None:
            return None

        if conviction is None or latest.conviction is None:
            return None

        delta = conviction - latest.conviction

        if delta == 0:
            return None

        if latest.scores.is_empty:
            return ConvictionChange(
                previous=latest.conviction,
                delta=delta,
                unexplained=True,
            )

        because = []

        for name, label in labels.items():
            before = getattr(latest.scores, name)
            after = getattr(scores, name)

            if before is None or after is None or before == after:
                continue

            # Every score runs the same way, so up is better whichever
            # one it is — the property the whole set was aligned for.
            moved = "improved" if after > before else "fell"

            because.append(f"{label} {moved}, {before} → {after}")

        return ConvictionChange(
            previous=latest.conviction,
            delta=delta,
            because=tuple(because),
        )

    @property
    def state_changes(self) -> int:
        """How many times the recorded state changed."""

        return sum(
            1
            for previous, current in zip(
                self.records,
                self.records[1:],
                strict=False,
            )
            if previous.state is not current.state
        )

    def course(
        self,
        labels: Mapping[str, str] = SCORE_LABELS,
    ) -> DecisionCourse:
        """Every recorded change of mind, worded, most recent first.

        `labels` names the scores the way the caller's dossier kind does,
        exactly as `conviction_change_against` takes them: a token's
        quality moving is an asset-quality move.

        A first review has no course. It is reported as an absence with
        the reason, because "Stable" over a run of one states a settled
        view the record does not hold.
        """

        if not self.records:
            return DecisionCourse(
                symbol=self.symbol,
                reviews=0,
                changes=0,
                first_recorded_at=None,
                last_recorded_at=None,
                absent_because=(
                    "The Artificial CIO has recorded no decision about this "
                    "security yet, so there is no history to compare against."
                ),
            )

        first, last = self.records[0], self.records[-1]

        if len(self.records) == 1:
            return DecisionCourse(
                symbol=self.symbol,
                reviews=1,
                changes=0,
                first_recorded_at=first.decided_at,
                last_recorded_at=last.decided_at,
                absent_because=(
                    "One review is recorded for this security, on "
                    f"{first.decided_at.date().isoformat()}. A first review "
                    "has nothing before it to have changed from."
                ),
            )

        transitions = tuple(
            reversed(
                [
                    self._transition(previous, current, labels)
                    for previous, current in zip(
                        self.records,
                        self.records[1:],
                        strict=False,
                    )
                    if previous.state is not current.state
                ]
            )
        )

        return DecisionCourse(
            symbol=self.symbol,
            reviews=len(self.records),
            changes=len(transitions),
            first_recorded_at=first.decided_at,
            last_recorded_at=last.decided_at,
            transitions=transitions,
            stated=self._course_stated(len(transitions), first, last),
        )

    @staticmethod
    def _course_stated(
        changes: int,
        first: DecisionRecord,
        last: DecisionRecord,
    ) -> str:
        """The course in one sentence, counting rather than characterising."""

        span = (
            f"between {first.decided_at.date().isoformat()} and "
            f"{last.decided_at.date().isoformat()}"
        )

        if not changes:
            return f"The decision has not changed across the reviews recorded {span}."

        return (
            f"The decision changed {changes} time{'s' if changes > 1 else ''} {span}."
        )

    @classmethod
    def _transition(
        cls,
        previous: DecisionRecord,
        current: DecisionRecord,
        labels: Mapping[str, str],
    ) -> RecordedTransition:
        """One change, with the rationale recorded at the time.

        Where either record carries no scores at all, nothing is said
        about what moved. A whole missing score set is one fact — this
        decision predates the journal keeping them — and enumerating it
        as five separate scores "measured again" would turn one silence
        into five findings.
        """

        unexplained = previous.scores.is_empty or current.scores.is_empty

        return RecordedTransition(
            at=current.decided_at,
            from_state=previous.state.value,
            to_state=current.state.value,
            from_conviction=previous.conviction,
            to_conviction=current.conviction,
            # Never reworded, and never written now: this is the sentence
            # the CIO recorded when it took the decision.
            rationale=current.rationale,
            moved=(
                ()
                if unexplained
                else cls._moved(previous.scores, current.scores, labels)
            ),
            unexplained=unexplained,
        )

    @staticmethod
    def _moved(
        before: RecordedScores,
        after: RecordedScores,
        labels: Mapping[str, str],
    ) -> tuple[str, ...]:
        """Which scores differed between two decisions, worded.

        Four outcomes per score, and the two involving an absence are the
        ones this exists for. A score that stopped being measurable is
        **not** a score that fell: Volkswagen went to INVESTIGATE on 9
        August with business quality and valuation both unmeasured, and
        reading those absences as deterioration would report a provider
        outage as a worse business.
        """

        moved: list[str] = []

        for name, label in labels.items():
            was = getattr(before, name)
            now = getattr(after, name)

            if was is None and now is None:
                continue

            if was is not None and now is None:
                moved.append(f"{label} could no longer be measured (it was {was})")
                continue

            if was is None and now is not None:
                moved.append(f"{label} could be measured again ({now})")
                continue

            if was == now:
                continue

            # Every score runs the same way, so up is better whichever
            # one it is — the property the whole set was aligned for.
            direction = "improved" if now > was else "fell"

            moved.append(f"{label} {direction}, {was} → {now}")

        return tuple(moved)
