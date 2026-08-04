from collections import Counter

from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion


class CommitteeChairman:
    def decide(
        self,
        opinions: list[CommitteeOpinion],
        weights: dict[str, float] | None = None,
    ) -> CommitteeDecision:
        votes = Counter(opinion.vote for opinion in opinions)

        if weights is None:
            recommendation = votes.most_common(1)[0][0]
        else:
            weighted_votes = {
                "BUY": 0.0,
                "HOLD": 0.0,
                "SELL": 0.0,
            }

            for opinion in opinions:
                weighted_votes[opinion.vote] += weights.get(
                    opinion.member,
                    1.0,
                )

            recommendation = max(
                weighted_votes,
                key=lambda vote: weighted_votes[vote],
            )

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

    def weighted_decide(
        self,
        opinions: list[CommitteeOpinion],
        weights: dict[str, float],
    ) -> CommitteeDecision:
        return self.decide(
            opinions,
            weights=weights,
        )
