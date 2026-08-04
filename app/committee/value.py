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

        if pe < 18:
            return CommitteeOpinion(
                member="Value",
                vote="BUY",
                confidence=85,
                rationale="Forward P/E is attractive.",
            )

        if pe > 30:
            return CommitteeOpinion(
                member="Value",
                vote="HOLD",
                confidence=80,
                rationale="Forward P/E is elevated.",
            )

        return CommitteeOpinion(
            member="Value",
            vote="HOLD",
            confidence=70,
            rationale="Forward P/E is reasonable.",
        )
