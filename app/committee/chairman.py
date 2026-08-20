from collections import Counter

from app.domain.committee_decision import CommitteeDecision
from app.domain.committee_opinion import CommitteeOpinion


def abstained(opinion: CommitteeOpinion) -> bool:
    """Whether this member declined to take a position at all.

    **The legacy committee's abstention contract, stated in one place.**
    A member that could not reach its question expresses that as
    `confidence=0`; everything else is a vote, however cautious.

    Abstention is never inferred from the word HOLD. HOLD is a real
    position — "I looked, and the answer is do nothing" — and reading it
    as silence would delete the most common genuine verdict on the panel.
    """

    return opinion.confidence == 0


class CommitteeChairman:
    def decide(
        self,
        opinions: list[CommitteeOpinion],
        weights: dict[str, float] | None = None,
    ) -> CommitteeDecision:
        """Count the members that voted; carry the ones that did not.

        An abstaining member used to cast a full vote: `Counter` took
        every opinion, the weighted path added the member's whole regime
        weight, and the mean confidence was divided by a panel that
        included it. A committee that had said *"I cannot answer this"*
        was therefore recorded as having said HOLD, at its full weight,
        while dragging the panel's stated confidence down.

        Its wording is still carried in `opinions` — the investor should
        see that the member spoke and why it could not conclude — and it
        no longer counts as a position.
        """

        voting = [opinion for opinion in opinions if not abstained(opinion)]

        if not voting:
            # Never a manufactured HOLD. With every member abstaining
            # there is no committee position to report, and this type
            # has no way to say so: `recommendation` is a required
            # string and any value here would be a verdict nobody
            # reached. Unreachable from the live panel, where only Cash
            # can abstain.
            raise ValueError(
                "every committee member abstained; this decision type "
                "cannot express a panel that reached no position"
            )

        votes = Counter(opinion.vote for opinion in voting)

        if weights is None:
            recommendation = votes.most_common(1)[0][0]
        else:
            weighted_votes = {
                "BUY": 0.0,
                "HOLD": 0.0,
                "SELL": 0.0,
            }

            for opinion in voting:
                weighted_votes[opinion.vote] += weights.get(
                    opinion.member,
                    1.0,
                )

            recommendation = max(
                weighted_votes,
                key=lambda vote: weighted_votes[vote],
            )

        confidence = round(sum(opinion.confidence for opinion in voting) / len(voting))

        return CommitteeDecision(
            recommendation=recommendation,
            confidence=confidence,
            buy_votes=votes["BUY"],
            hold_votes=votes["HOLD"],
            sell_votes=votes["SELL"],
            # Every opinion, including the abstentions: they explain
            # themselves to the reader without counting as positions.
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
