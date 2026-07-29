"""Dashboard presentation models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardPriority:
    title: str

    description: str

    urgency: float


@dataclass(frozen=True, slots=True)
class DashboardInvestmentCase:
    symbol: str

    recommendation: str

    confidence: float

    summary: str


@dataclass(frozen=True, slots=True)
class DashboardViewModel:
    headline: str

    summary: str

    confidence: float

    portfolio_health: float

    priorities: tuple[DashboardPriority, ...]

    investment_cases: tuple[DashboardInvestmentCase, ...]
