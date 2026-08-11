"""Read what the registered committees have concluded. Nothing else.

**Read-only, and structurally so.** It reads the judgment record and the
registry, and it touches neither a committee nor a provider — so opening
this surface cannot run a model, cannot fetch, and cannot manufacture a
judgment event. `movrvest judge` remains the only thing that writes, and
that separation is why a count of judgments still means what it says.

**Committee N+1 appears without editing this file.** Every committee is
read from the registry, and the only committee-specific thing here is a
lookup by key. There is no branch on which committee it is, and there
could not be one usefully: this layer does not know what any verdict
means, so it has nothing to branch on.

**The past tense is deliberate.** *What have the committees concluded?*
is answered from the record, not by convening them — which is also what
makes the answer free and reproducible. A committee that has never run
for an asset is reported as exactly that, and never as an absence of
evidence.
"""

from __future__ import annotations

from app.domain.committee_matrix import (
    AssetCommitteeMatrix,
    CommitteeAssessment,
    UnjudgedCommittee,
    assessment_from,
)
from app.domain.committee_protocol import CommitteeContract
from app.services.crypto_committees import CONTRACTS
from app.services.judgment_history_service import JudgmentHistoryService


class CommitteeMatrixService:
    """The independent committee portfolio for one asset."""

    def __init__(self, history: JudgmentHistoryService | None = None) -> None:
        self._history = history or JudgmentHistoryService()

    def for_asset(
        self,
        symbol: str,
        contracts: tuple[CommitteeContract, ...] = CONTRACTS,
    ) -> AssetCommitteeMatrix:
        """Every registered committee's latest conclusion about this asset.

        `contracts` is injectable so a test can register a third
        committee without this module learning it exists — which is the
        core invariant of the slice, checked rather than asserted.
        """

        asset = symbol.upper().strip()

        assessments: list[CommitteeAssessment] = []
        unjudged: list[UnjudgedCommittee] = []

        for contract in contracts:
            records = self._history.history(asset, contract.key)

            if not records:
                unjudged.append(
                    UnjudgedCommittee(
                        asset=asset,
                        committee=contract.identity,
                        question=contract.question,
                    )
                )

                continue

            latest = records[-1]

            assessments.append(
                assessment_from(
                    latest,
                    question=self._question_for(latest.committee.key, contracts),
                    # Against today's contract, so a conclusion reached
                    # under an earlier one is visibly historical rather
                    # than quietly current.
                    comparability=contract.identity.comparability(latest.committee),
                    judgments_recorded=len(records),
                )
            )

        return AssetCommitteeMatrix(
            asset=asset,
            assessments=tuple(assessments),
            unjudged=tuple(unjudged),
        )

    @staticmethod
    def _question_for(
        key: str,
        contracts: tuple[CommitteeContract, ...],
    ) -> str | None:
        """The live question for this key, or None where none is live.

        `None` is a real answer: a record outlives the code that wrote
        it, and inventing a question for a committee that no longer
        exists would be worse than saying nothing.
        """

        for contract in contracts:
            if contract.key == key:
                return contract.question

        return None
