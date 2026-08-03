from app.committee.base import CommitteeMember
from app.domain.committee_context import CommitteeContext
from app.domain.committee_evidence import CommitteeEvidence
from app.domain.committee_opinion import CommitteeOpinion
from app.domain.finding import statements
from app.domain.momentum_signal import MomentumSignal


class MomentumCommittee(CommitteeMember):
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        if context.momentum_signal is not None:
            return self._from_signal(
                context.momentum_signal,
            )

        return self._from_legacy_intelligence(
            context,
        )

    @staticmethod
    def _from_signal(
        signal: MomentumSignal,
    ) -> CommitteeOpinion:
        evidence = tuple(
            CommitteeEvidence(
                title="Momentum evidence",
                value=finding.statement,
            )
            for finding in signal.evidence
        )

        if signal.trend == "BULLISH":
            vote = "BUY"
        elif signal.trend == "BEARISH":
            vote = "SELL"
        else:
            vote = "HOLD"

        return CommitteeOpinion(
            member="Momentum",
            vote=vote,
            confidence=signal.confidence,
            rationale=" ".join(statements(signal.evidence)),
            evidence=evidence,
        )

    @staticmethod
    def _from_legacy_intelligence(
        context: CommitteeContext,
    ) -> CommitteeOpinion:
        intelligence = context.intelligence

        evidence = (
            CommitteeEvidence(
                title="Market outlook",
                value=intelligence.outlook,
            ),
            CommitteeEvidence(
                title="Confidence",
                value=str(intelligence.confidence),
            ),
        )

        if intelligence.outlook == "BULLISH":
            vote = "BUY"
        elif intelligence.outlook == "BEARISH":
            vote = "SELL"
        else:
            vote = "HOLD"

        return CommitteeOpinion(
            member="Momentum",
            vote=vote,
            confidence=intelligence.confidence,
            rationale=intelligence.summary,
            evidence=evidence,
        )
