"""What the Artificial CIO decided before.

These are facts about decisions that were actually made and recorded. They
carry no judgement about whether those decisions were right: outcome
analysis is a separate concern, and nothing here estimates it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.cio.decision_state import DecisionState


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
class DecisionRecord:
    """One decision the Artificial CIO made, as it was recorded."""

    symbol: str
    state: DecisionState
    conviction: int
    rationale: str
    decided_at: datetime


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
