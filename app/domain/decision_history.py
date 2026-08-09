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
class DecisionRecord:
    """One decision the Artificial CIO made, as it was recorded."""

    symbol: str
    state: DecisionState
    conviction: int
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
        """

        recorded = self.current_state

        if recorded is None:
            return None

        if state is recorded:
            reviews = len(self.current_run) + 1
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
        conviction: int,
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

        `labels` is how the caller's dossier kind names the scores — a
        token's quality moving is an asset-quality move, not a business-
        quality one. The keys are the record's and never vary.
        """

        latest = self.latest

        if latest is None:
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
