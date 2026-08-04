from dataclasses import dataclass

from app.domain.committee_opinion import CommitteeOpinion


@dataclass(frozen=True)
class CommitteeDecision:
    recommendation: str

    confidence: int

    buy_votes: int

    hold_votes: int

    sell_votes: int

    opinions: tuple[CommitteeOpinion, ...]
