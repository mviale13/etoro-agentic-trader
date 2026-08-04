from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheck:
    name: str
    score: int
    status: str
    message: str


@dataclass(frozen=True)
class PortfolioHealth:
    overall_score: int
    checks: list[HealthCheck]
    recommendation: str
