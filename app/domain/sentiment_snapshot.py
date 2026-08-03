from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SentimentSnapshot:
    """One published reading of market sentiment, and who published it."""

    score: int
    label: str

    #: The service this was read from. It is printed to the investor, so it
    #: must name where the number actually came from.
    source: str

    #: When the source published it. None only where the reading carried no
    #: timestamp of its own.
    observed_at: datetime | None = None
