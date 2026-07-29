from enum import StrEnum


class DecisionState(StrEnum):
    """Lifecycle state of an investment case."""

    REJECT = "REJECT"
    MONITOR = "MONITOR"
    INVESTIGATE = "INVESTIGATE"
    PREPARE = "PREPARE"
    RECOMMEND = "RECOMMEND"

    @property
    def belongs_to_watchlist(self) -> bool:
        """Every active investment case except REJECT is watchlisted."""
        return self is not DecisionState.REJECT
