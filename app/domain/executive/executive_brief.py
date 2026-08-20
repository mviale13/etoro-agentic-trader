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

    #: None where the portfolio health score is unmeasured — see
    #: `PortfolioAssessment.health_score`. A brief may not invent a
    #: figure for a score its analyst refused.
    portfolio_health: float | None

    priorities: tuple[ExecutivePriority, ...]

    investment_cases: tuple[InvestmentThesis, ...]
