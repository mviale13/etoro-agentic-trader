from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationDifference:
    asset: str
    current: float
    target: float
    difference: float


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
        if not self.allocations:
            return None

        return max(
            self.allocations,
            key=lambda item: abs(item.difference),
        )