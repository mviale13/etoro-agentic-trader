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

    **Where a decision names the records it rests on, sameness is checked
    rather than assumed.** A decision reached from scores has no stable
    identity behind it, so the day is the finest resolution at which two
    of them can honestly be called the same, and that rule is unchanged.
    A decision reached from recorded judgments carries their ids: an
    unchanged set is positive evidence that the same evidence produced
    the same answer, and a changed set is evidence that it did not —
    which is #113's *evidence moved under a steady answer*, the ordinary
    case, and the one a day-and-state rule silently drops. Such a
    decision is therefore compared against the last one recorded rather
    than against today's, so a page view can append only when something
    actually moved, and re-reading a page all day appends nothing.
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

        # The rules this decision was reached under, and the records it
        # rested on. Written only where the decision carries them, so no
        # existing record shape changes and an absent key keeps meaning
        # *this predates the stamp* rather than *no rule applied*.
        if decision.decided_under:
            payload["decided_under"] = [
                rule.identity for rule in decision.decided_under
            ]

        if decision.evidence_records:
            payload["evidence_records"] = list(decision.evidence_records)

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
        """Whether this decision is one the record already holds.

        Two questions, and which one applies depends on what the decision
        can prove about itself rather than on what kind of asset it is.
        """

        history = self.history(symbol)

        if decision.evidence_records:
            latest = history.latest

            # Same answer, same rules, same records beneath it: nothing
            # has happened since the last one. Compared against the
            # latest rather than against today's, because *nothing
            # changed* is here a checkable fact rather than a convention
            # about how often to write.
            return (
                latest is not None
                and latest.state is decision.state
                and latest.evidence_records == decision.evidence_records
                and latest.decided_under
                == tuple(rule.identity for rule in decision.decided_under)
            )

        decided_on = decision.decided_at.date()

        return any(
            record.state is decision.state and record.decided_at.date() == decided_on
            for record in history.records
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
            decided_under=DecisionJournal._to_strings(
                event.payload.get("decided_under"),
            ),
            evidence_records=DecisionJournal._to_strings(
                event.payload.get("evidence_records"),
            ),
        )

    @staticmethod
    def _to_strings(raw: object) -> tuple[str, ...]:
        """A recorded list of identities, or an honest empty one.

        Absent for every record written before the field existed, which
        is the truth about them: the rule was not noted, not that none
        applied.
        """

        if not isinstance(raw, list):
            return ()

        return tuple(str(item) for item in raw)

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
