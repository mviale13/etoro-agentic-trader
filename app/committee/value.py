from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion
from app.domain.finding import statements
from app.domain.value_signal import ValueSignal


class ValueCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        if context.value_signal is not None:
            return self._from_signal(
                context.value_signal,
            )

        return self._from_legacy_valuation(
            context,
        )

    @staticmethod
    def _from_signal(
        signal: ValueSignal,
    ) -> CommitteeOpinion:
        rationale = " ".join(statements(signal.evidence))

        if signal.valuation == "CHEAP":
            vote = "BUY"
        else:
            vote = "HOLD"

        return CommitteeOpinion(
            member="Value",
            vote=vote,
            confidence=signal.confidence,
            rationale=rationale,
        )

    @staticmethod
    def _from_legacy_valuation(
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        if context.valuation is None:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=50,
                rationale="No valuation data available.",
            )

        pe = context.valuation.forward_pe

        if pe is None:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=50,
                rationale="Forward P/E unavailable.",
            )

        # The votes and thresholds are untouched legacy policy. What
        # changed is the account of them: "attractive", "elevated" and
        # "reasonable" were interpretations resting on no benchmark —
        # the same false-comparison shape VALUATION_AUTHORITY.md found
        # at the security level, in this package's own copy of the
        # P/E band (18/30 here, against pe-bands@1's 18/28).
        if pe < 18:
            return CommitteeOpinion(
                member="Value",
                vote="BUY",
                confidence=85,
                rationale=(
                    f"Forward P/E {pe:.1f} is below this committee's own "
                    "fixed band at 18 — legacy policy, not an evidenced "
                    "comparison."
                ),
            )

        if pe > 30:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=80,
                rationale=(
                    f"Forward P/E {pe:.1f} is above this committee's own "
                    "fixed band at 30 — legacy policy, not an evidenced "
                    "comparison."
                ),
            )

        return CommitteeOpinion(
            member="Value",
            vote="HOLD",
            confidence=70,
            rationale=(
                f"Forward P/E {pe:.1f} sits within this committee's own "
                "fixed bands (18-30) — legacy policy, not an evidenced "
                "comparison."
            ),
        )
