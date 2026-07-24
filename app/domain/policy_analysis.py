from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationDifference:
    current: float
    target: float
    difference: float


@dataclass(frozen=True, slots=True)
class PolicyAnalysis:
    stocks: AllocationDifference
    etfs: AllocationDifference
    crypto: AllocationDifference
    cash: AllocationDifference
    compliant: bool