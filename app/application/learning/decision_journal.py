"""The Artificial CIO's memory of its own decisions."""

from __future__ import annotations

from collections.abc import Iterable

from app.cio.decision_state import DecisionState
from app.cio.executive_decision import ExecutiveDecision
from app.domain.decision_history import DecisionHistory, DecisionRecord
from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.event_repository import EventRepository


class DecisionJournal:
    """
    Record what the Artificial CIO decided, and read it back.

    The journal stores decisions, not judgements about them. It never
    re-decides, never scores, and never infers an outcome.

    A decision is recorded once per symbol, per day, per state. Repeating an
    evaluation the same day — a second dashboard load, a second CLI run —
    therefore does not inflate the record. A state that changes during the
    day is recorded, because the change is what happened.
    """

    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def record(
        self,
        decision: ExecutiveDecision,
    ) -> bool:
        """Remember a decision. Returns False when it was already recorded."""

        symbol = self._normalize(decision.symbol)

        if self._already_recorded(decision, symbol):
            return False

        self._repository.save(
            Event(
                timestamp=decision.decided_at,
                event_type=EventType.EXECUTIVE_DECISION_RECORDED,
                symbol=symbol,
                payload={
                    "state": decision.state.value,
                    "conviction": decision.conviction,
                    "rationale": decision.rationale,
                },
            )
        )

        return True

    def history(
        self,
        symbol: str,
    ) -> DecisionHistory:
        """Return every recorded decision for one symbol, oldest first."""

        normalized = self._normalize(symbol)

        return DecisionHistory(
            symbol=normalized,
            records=tuple(
                record for record in self._records() if record.symbol == normalized
            ),
        )

    def histories(self) -> dict[str, DecisionHistory]:
        """Return the recorded history of every symbol the CIO has judged."""

        by_symbol: dict[str, list[DecisionRecord]] = {}

        for record in self._records():
            by_symbol.setdefault(record.symbol, []).append(record)

        return {
            symbol: DecisionHistory(
                symbol=symbol,
                records=tuple(records),
            )
            for symbol, records in by_symbol.items()
        }

    def _records(self) -> Iterable[DecisionRecord]:
        for event in self._repository.load_all():
            if event.event_type != EventType.EXECUTIVE_DECISION_RECORDED:
                continue

            record = self._to_record(event)

            if record is not None:
                yield record

    def _already_recorded(
        self,
        decision: ExecutiveDecision,
        symbol: str,
    ) -> bool:
        decided_on = decision.decided_at.date()

        return any(
            record.state is decision.state and record.decided_at.date() == decided_on
            for record in self.history(symbol).records
        )

    @staticmethod
    def _to_record(
        event: Event,
    ) -> DecisionRecord | None:
        """
        Rebuild a recorded decision, or report it as unreadable.

        A record whose state the current DecisionState no longer knows is
        skipped rather than guessed at.
        """

        if event.symbol is None:
            return None

        try:
            state = DecisionState(str(event.payload["state"]))
        except (KeyError, ValueError):
            return None

        return DecisionRecord(
            symbol=event.symbol,
            state=state,
            conviction=int(event.payload.get("conviction", 0)),
            rationale=str(event.payload.get("rationale", "")),
            decided_at=event.timestamp,
        )

    @staticmethod
    def _normalize(
        symbol: str,
    ) -> str:
        return symbol.upper().strip()
