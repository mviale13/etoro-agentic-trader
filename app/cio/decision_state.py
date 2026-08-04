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

    @property
    def asks_for_action(self) -> bool:
        """Whether this state puts something in front of the investor."""
        return self in (DecisionState.PREPARE, DecisionState.RECOMMEND)

    @property
    def lifecycle_rank(self) -> int:
        """
        Position in the investment-case lifecycle, REJECT lowest.

        The distance between two ranks is how far a decision moved, which is
        measured rather than judged.
        """
        return LIFECYCLE.index(self)


#: The lifecycle, from abandoned to actionable.
LIFECYCLE: tuple[DecisionState, ...] = (
    DecisionState.REJECT,
    DecisionState.MONITOR,
    DecisionState.INVESTIGATE,
    DecisionState.PREPARE,
    DecisionState.RECOMMEND,
)
