"""Record what a committee concluded, and read back what changed.

Two halves, deliberately apart, on the intelligence journal's own
division: `record` writes a judgment and knows nothing about change,
`transition` and `standing` read the record and state what it says
without saying what it means.

**Recording is an explicit act.** A read-only surface calls
`committee.judge()` to render, and if judging also wrote history then
opening a page would manufacture a judgment event — the record would
say the committee convened whenever somebody looked, and
`JudgmentCoverage` would count page views as reviews. So the write
lives here and is called by `movrvest judge`, which is the same
separation `observe` has from `knowledge`.

**A judgment is recorded with the evidence it was actually given.**
Both are captured in the same breath, because a digest computed later
would be a digest of different evidence — and the whole of §4 rests on
knowing which evidence produced which answer.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.committee_judgment import CommitteeJudgment, EligibleFinding, Remit
from app.domain.judgment_history import (
    CommitteeVersion,
    JudgmentCoverage,
    JudgmentRecord,
    JudgmentStanding,
    JudgmentTransition,
    compare,
    coverage,
    record_from,
    standing,
    transitions,
)
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore

#: How many judgments a projection reads back. Enough to describe how a
#: view moved without turning a surface into an archive.
WINDOW = 24


class JudgmentHistoryService:
    """This platform's memory of its own bounded judgments."""

    def __init__(self, store: JudgmentHistoryStore | None = None) -> None:
        self._store = store or JudgmentHistoryStore()

    # ── writing ─────────────────────────────────────────────────────

    def record(
        self,
        judgment: CommitteeJudgment,
        committee: CommitteeVersion,
        evidence: tuple[EligibleFinding, ...] = (),
        now: datetime | None = None,
    ) -> JudgmentRecord | None:
        """Write one judgment event, or None if it was already held.

        Records every outcome, not only verdicts. An abstention and an
        unavailable judgment are the states §2 forbids collapsing, and a
        history that stored only answers could not tell *the question
        stopped applying* from *nobody asked*.
        """

        moment = now or datetime.now(UTC)

        record = record_from(judgment, committee, evidence, recorded_at=moment)

        return record if self._store.append(record) else None

    # ── reading ─────────────────────────────────────────────────────

    def history(
        self,
        asset: str,
        remit: Remit = Remit.VALUE_CAPTURE,
        limit: int = WINDOW,
    ) -> list[JudgmentRecord]:
        return self._store.records(asset, remit=remit, limit=limit)

    def latest(
        self,
        asset: str,
        remit: Remit = Remit.VALUE_CAPTURE,
    ) -> JudgmentRecord | None:
        held = self.history(asset, remit)

        return held[-1] if held else None

    def transitions(
        self,
        asset: str,
        remit: Remit = Remit.VALUE_CAPTURE,
        limit: int = WINDOW,
    ) -> tuple[JudgmentTransition, ...]:
        """Every consecutive pair in the record. Deterministic, no model."""

        return transitions(self.history(asset, remit, limit))

    def against_history(
        self,
        current: JudgmentRecord,
        remit: Remit = Remit.VALUE_CAPTURE,
    ) -> JudgmentTransition:
        """What a judgment in hand changed, against the last one stored.

        The previous record is the most recent one that is not this
        judgment itself, so calling this before or after recording gives
        the same answer — a projection that changed depending on write
        order would not be a projection.
        """

        earlier = [
            record
            for record in self.history(current.asset, remit)
            if record.record_id != current.record_id
        ]

        return compare(current, earlier[-1] if earlier else None)

    def standing(
        self,
        current: JudgmentRecord,
        remit: Remit = Remit.VALUE_CAPTURE,
    ) -> JudgmentStanding:
        """What may be said today, given everything recorded before.

        §5 lives here: where today's committee reached no verdict, this
        returns the earlier one as history and never as a current
        finding.
        """

        return standing(current, self.history(current.asset, remit))

    def coverage(
        self,
        asset: str,
        remit: Remit = Remit.VALUE_CAPTURE,
    ) -> JudgmentCoverage:
        """How often this committee has judged this asset, worded honestly."""

        return coverage(asset.upper().strip(), remit, self.history(asset, remit))
