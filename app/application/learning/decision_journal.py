"""The Artificial CIO's memory of its own decisions."""

from __future__ import annotations

from collections.abc import Iterable

from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.decision_history import (
    DecisionHistory,
    DecisionRecord,
    RecordedScores,
)
from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.score_basis import SCORE_LABELS
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
        evidence: DecisionEvidence | None = None,
    ) -> bool:
        """
        Remember a decision. Returns False when it was already recorded.

        The scores it was decided on are recorded beside it, where the
        caller has them. Without them a later cycle can say the conviction
        moved but not what moved underneath — which is exactly what every
        decision recorded before this said, and why it is stored now.
        """

        symbol = self._normalize(decision.symbol)

        if self._already_recorded(decision, symbol):
            return False

        payload: dict[str, object] = {
            "state": decision.state.value,
            "conviction": decision.conviction,
            "rationale": decision.rationale,
        }

        if evidence is not None:
            payload["scores"] = {
                "quality": evidence.quality_score,
                "evidence": evidence.evidence_score,
                "valuation": evidence.valuation_score,
                # Stored the way every surface shows it, so a later
                # comparison does not have to remember which one runs
                # backwards.
                "safety": evidence.safety_score,
                "portfolio_fit": evidence.portfolio_fit_score,
            }

        self._repository.save(
            Event(
                timestamp=decision.decided_at,
                event_type=EventType.EXECUTIVE_DECISION_RECORDED,
                symbol=symbol,
                payload=payload,
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
            # Absent stays absent. `int(..., 0)` read a withheld conviction
            # — and a record written before the field existed — as a
            # decision taken at zero conviction, which is the strongest
            # negative judgment on the scale rather than the absence of
            # one. The next cycle would then report a rise out of nothing.
            conviction=DecisionJournal._to_conviction(
                event.payload.get("conviction"),
            ),
            rationale=str(event.payload.get("rationale", "")),
            decided_at=event.timestamp,
            scores=DecisionJournal._to_scores(event.payload.get("scores")),
        )

    @staticmethod
    def _to_conviction(raw: object) -> int | None:
        """The conviction as recorded, or nothing where none was."""

        if raw is None:
            return None

        if isinstance(raw, bool) or not isinstance(raw, int | float | str):
            return None

        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_scores(raw: object) -> RecordedScores:
        """
        The scores as recorded, or an empty set for an older decision.

        A record written before the journal kept them carries no scores at
        all, which is why the absence is a distinct state rather than five
        zeroes: a decision made at zero conviction in every dimension is a
        thing that could happen, and this is not it.
        """

        if not isinstance(raw, dict):
            return RecordedScores()

        def value(name: str) -> int | None:
            recorded = raw.get(name)

            return int(recorded) if isinstance(recorded, int | float) else None

        return RecordedScores(**{name: value(name) for name in SCORE_LABELS})

    @staticmethod
    def _normalize(
        symbol: str,
    ) -> str:
        return symbol.upper().strip()
