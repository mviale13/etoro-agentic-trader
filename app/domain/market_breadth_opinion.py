from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class MarketBreadthVerdict(Verdict):
    STRONG = "strong"
    MIXED = "mixed"
    WEAK = "weak"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MarketBreadthOpinion(Opinion[MarketBreadthVerdict]):
    pass
