from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RecommendationJournalEntry:
    timestamp: datetime
    symbol: str
    recommendation: str
    successful: bool
    reflection: str
