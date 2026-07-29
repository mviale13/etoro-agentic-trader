from collections import defaultdict

from app.domain.committee_vote import CommitteeVote
from app.domain.executive_board_decision import ExecutiveBoardDecision


class ExecutiveBoardService:
    """Aggregate committee votes into a weighted Executive Board decision."""

    def decide(
        self,
        votes: tuple[CommitteeVote, ...],
    ) -> ExecutiveBoardDecision:
        if not votes:
            return ExecutiveBoardDecision(
                recommendation="HOLD",
                confidence=0,
                votes=(),
                rationale="No committee votes were available.",
            )

        weights: dict[str, float] = defaultdict(float)

        for vote in votes:
            weights[vote.recommendation] += vote.weight

        highest_weight = max(weights.values())

        winning_recommendations = [
            recommendation
            for recommendation, weight in weights.items()
            if weight == highest_weight
        ]

        if len(winning_recommendations) > 1:
            recommendation = "HOLD"
            rationale = (
                "Committee weights were tied, so the Executive Board selected HOLD."
            )
        else:
            recommendation = winning_recommendations[0]
            rationale = (
                f"{recommendation} received the highest combined committee weight."
            )

        supporting_votes = tuple(
            vote for vote in votes if vote.recommendation == recommendation
        )

        supporting_weight = sum(vote.weight for vote in supporting_votes)

        confidence = (
            round(
                sum(vote.confidence * vote.weight for vote in supporting_votes)
                / supporting_weight
            )
            if supporting_weight > 0
            else 0
        )

        return ExecutiveBoardDecision(
            recommendation=recommendation,
            confidence=confidence,
            votes=votes,
            rationale=rationale,
        )
