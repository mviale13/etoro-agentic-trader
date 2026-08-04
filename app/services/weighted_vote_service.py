from app.domain.committee_member_weight import CommitteeMemberWeight
from app.domain.committee_opinion import CommitteeOpinion


class WeightedVoteService:
    def score(
        self,
        opinions: list[CommitteeOpinion],
        weights: list[CommitteeMemberWeight],
    ) -> dict[str, float]:
        weight_map = {item.member: item.weight for item in weights}

        scores = {
            "BUY": 0.0,
            "HOLD": 0.0,
            "SELL": 0.0,
        }

        for opinion in opinions:
            scores[opinion.vote] += opinion.confidence * weight_map.get(
                opinion.member, 1.0
            )

        return scores
