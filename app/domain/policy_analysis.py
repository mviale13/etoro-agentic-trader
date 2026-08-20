from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationDifference:
    asset: str

    #: None where the allocation itself could not be read. A difference
    #: of None is not a difference of zero — the second would credit an
    #: unread allocation with sitting exactly on its target.
    current: float | None
    target: float
    difference: float | None


@dataclass(frozen=True, slots=True)
class PolicyAnalysis:
    allocations: tuple[AllocationDifference, ...]
    compliant: bool

    def allocation(self, asset: str) -> AllocationDifference | None:
        normalized = asset.strip().lower()

        for item in self.allocations:
            if item.asset.lower() == normalized:
                return item

        return None

    def largest_deviation(self) -> AllocationDifference | None:
        """The widest measured deviation, or nothing.

        An unmeasured difference cannot be the largest one and cannot
        be ranked against measured ones; it is left out of the
        comparison rather than sorted as a zero.
        """

        measured = [item for item in self.allocations if item.difference is not None]

        if not measured:
            return None

        return max(
            measured,
            key=lambda item: abs(item.difference or 0.0),
        )
