from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    overall: str

    market: str

    concentration: str

    liquidity: str

    policy: str

    rationale: tuple[str, ...]
