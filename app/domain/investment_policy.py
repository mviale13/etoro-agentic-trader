from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationTarget:
    stocks: float
    etfs: float
    crypto: float
    cash: float


@dataclass(frozen=True, slots=True)
class InvestmentConstraints:
    max_single_position: float
    max_crypto: float
    rebalance_threshold: float


@dataclass(frozen=True, slots=True)
class InvestmentPolicy:
    risk_profile: str
    target: AllocationTarget
    constraints: InvestmentConstraints
