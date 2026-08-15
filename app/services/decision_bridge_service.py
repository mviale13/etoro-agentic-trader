"""Project recorded committee judgments into investment considerations.

The service half of the bridge. It reads the committee matrix — which is
itself a projection of recorded judgments — and produces one
`InvestmentConsideration` per committee that has concluded anything.

**It consumes committee *output*, never committee *evidence*.** There is
no call to `committee.evidence()` here and no import of a committee
implementation; the deepest thing this service can reach is a recorded
judgment, which is a fact about what a committee said rather than the
material it said it from. A bridge that re-opened the evidence would be
a second judge wearing a projection's name.

**Nothing is stored.** A consideration is a deterministic function of an
immutable, versioned judgment and a versioned licensing table, so it can
always be recomputed and never needs a record of its own — the lighter
of the two models §7 asks between. What it must not do is lose the
version, and it does not: `policy_version` rides on every consideration,
so a projection quoted after a rule changes still says which rules made
it.
"""

from __future__ import annotations

from app.domain.committee_matrix import CommitteeAssessment
from app.domain.investment_consideration import (
    BRIDGE_POLICY_VERSION,
    AssetConsiderations,
    InvestmentConsideration,
    effect_for,
)
from app.services.committee_matrix_service import CommitteeMatrixService


class DecisionBridgeService:
    """What the committees establish, addressed to an investment layer."""

    def __init__(self, matrix: CommitteeMatrixService | None = None) -> None:
        self._matrix = matrix or CommitteeMatrixService()

    def considerations(self, symbol: str) -> AssetConsiderations:
        """Every committee's conclusion about one asset, projected.

        Read-only and free: the matrix opens a stored door, and this
        adds a dictionary lookup per committee. Nothing here fetches,
        judges, or asks a model.
        """

        asset = symbol.upper().strip()

        matrix = self._matrix.for_asset(asset)

        return AssetConsiderations(
            asset=asset,
            considerations=tuple(_from_assessment(cell) for cell in matrix.assessments),
            # A committee that has never run here concluded nothing, so it
            # produces no consideration — and is named, because an
            # investment layer that could not tell *nobody asked* from
            # *we asked and got nothing usable* would read a thin corpus
            # as a complete one.
            silent=tuple(missing.committee.name for missing in matrix.unjudged),
        )


def _from_assessment(cell: CommitteeAssessment) -> InvestmentConsideration:
    """One cell, projected. Every field copied or looked up.

    The one line that could have been a branch is `effect_for`, and it is
    a lookup: this function never asks *which* committee it is holding,
    so a third one arrives here needing no edit.
    """

    return InvestmentConsideration(
        asset=cell.asset,
        committee=cell.committee,
        question=cell.question,
        posture=cell.posture,
        applicability=cell.applicability,
        # Present exactly when the committee answered. `answer` falls
        # back to the bare token where a record predates the stored
        # sentence, and quoting a token is still quoting.
        conclusion=cell.verdict,
        conclusion_stated=cell.verdict_stated if cell.is_answered else None,
        because=cell.because or cell.unavailable_because,
        confidence=cell.confidence,
        effect=effect_for(cell.committee.key, cell.verdict),
        policy_version=BRIDGE_POLICY_VERSION,
        judgment_id=cell.record_id,
        comparability=cell.comparability,
        refs=cell.refs,
        evidence_count=cell.evidence_count,
        evidence_semantics=cell.evidence_semantics,
    )
