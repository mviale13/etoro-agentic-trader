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

**A judgment is recorded with the evidence it was actually given, and
the judgment is the only thing that knows what that was.** It used to be
a second argument here, resolved by the caller — and a caller that
resolves its own evidence is a caller that can disagree with the
committee. It did: `judge()` returns before consulting anything when the
question does not apply, so a declined judgment was filed with findings
it had never seen. The parameter is gone for the same reason PR #113
removed the committee identity.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.committee_judgment import CommitteeJudgment
from app.domain.judgment_history import (
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
        now: datetime | None = None,
    ) -> JudgmentRecord | None:
        """Write one judgment event, or None if it was already held.

        Records every outcome, not only verdicts. An abstention and an
        unavailable judgment are the states §2 forbids collapsing, and a
        history that stored only answers could not tell *the question
        stopped applying* from *nobody asked*.
        """

        moment = now or datetime.now(UTC)

        # Both the identity and the evidence come from the judgment's own
        # contract. PR #113 took the identity as a second argument, which
        # meant a caller could file a judgment under a committee that did
        # not produce it; the evidence was the same shape and it went
        # wrong in the same way, so it left the signature too.
        record = record_from(judgment, recorded_at=moment)

        return record if self._store.append(record) else None

    # ── reading ─────────────────────────────────────────────────────

    def history(
        self,
        asset: str,
        committee: str,
        limit: int = WINDOW,
    ) -> list[JudgmentRecord]:
        return self._store.records(asset, committee=committee, limit=limit)

    def latest(
        self,
        asset: str,
        committee: str,
    ) -> JudgmentRecord | None:
        held = self.history(asset, committee)

        return held[-1] if held else None

    def transitions(
        self,
        asset: str,
        committee: str,
        limit: int = WINDOW,
    ) -> tuple[JudgmentTransition, ...]:
        """Every consecutive pair in the record. Deterministic, no model."""

        return transitions(self.history(asset, committee, limit))

    def against_history(self, current: JudgmentRecord) -> JudgmentTransition:
        """What a judgment in hand changed, against the last one stored.

        The previous record is the most recent one that is not this
        judgment itself, so calling this before or after recording gives
        the same answer — a projection that changed depending on write
        order would not be a projection.

        Which history to read comes from the record, not from the
        caller: a judgment compared against another committee's past
        would be a transition between two different questions.
        """

        earlier = [
            record
            for record in self.history(current.asset, current.committee.key)
            if record.record_id != current.record_id
        ]

        return compare(current, earlier[-1] if earlier else None)

    def standing(self, current: JudgmentRecord) -> JudgmentStanding:
        """What may be said today, given everything recorded before.

        Where today's committee reached no verdict, this returns the
        earlier one as history and never as a current finding.
        """

        return standing(current, self.history(current.asset, current.committee.key))

    def coverage(
        self,
        asset: str,
        committee: str,
    ) -> JudgmentCoverage:
        """How often this committee has judged this asset, worded honestly."""

        return coverage(
            asset.upper().strip(), committee, self.history(asset, committee)
        )
