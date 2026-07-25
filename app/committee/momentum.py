from app.domain.committee_opinion import CommitteeOpinion
from app.domain.market_intelligence import MarketIntelligence


class MomentumCommittee:
    def evaluate(
        self,
        intelligence: MarketIntelligence,
    ) -> CommitteeOpinion:
        if intelligence.outlook == "BULLISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="BUY",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
            )

        if intelligence.outlook == "BEARISH":
            return CommitteeOpinion(
                member="Momentum",
                vote="SELL",
                confidence=intelligence.confidence,
                rationale=intelligence.summary,
            )

        return CommitteeOpinion(
            member="Momentum",
            vote="HOLD",
            confidence=intelligence.confidence,
            rationale=intelligence.summary,
        )
