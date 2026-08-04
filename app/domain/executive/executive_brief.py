from __future__ import annotations

from dataclasses import dataclass

from app.domain.thesis import InvestmentThesis


@dataclass(frozen=True, slots=True)
class ExecutivePriority:
    title: str

    description: str

    urgency: float


@dataclass(frozen=True, slots=True)
class ExecutiveBrief:
    headline: str

    summary: str

    confidence: float | None

    portfolio_health: float

    priorities: tuple[ExecutivePriority, ...]

    investment_cases: tuple[InvestmentThesis, ...]
