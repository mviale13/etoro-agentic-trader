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

    #: The deepest fall the investor said they could sit through, as a
    #: percentage. None where they have not said — which is not the same
    #: as unlimited, and is why the platform's own default is applied
    #: somewhere that names itself as a default.
    max_drawdown: float | None = None


@dataclass(frozen=True, slots=True)
class InvestmentPolicy:
    risk_profile: str
    target: AllocationTarget
    constraints: InvestmentConstraints
