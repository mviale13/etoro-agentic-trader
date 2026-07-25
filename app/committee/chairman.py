from collections import Counter

from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion


class CommitteeChairman:
    def decide(
        self,
        opinions: list[CommitteeOpinion],
    ) -> CommitteeDecision:
        votes = Counter(opinion.vote for opinion in opinions)

        recommendation = votes.most_common(1)[0][0]

        confidence = round(
            sum(opinion.confidence for opinion in opinions) / len(opinions)
        )

        return CommitteeDecision(
            recommendation=recommendation,
            confidence=confidence,
            buy_votes=votes["BUY"],
            hold_votes=votes["HOLD"],
            sell_votes=votes["SELL"],
            opinions=tuple(opinions),
        )
