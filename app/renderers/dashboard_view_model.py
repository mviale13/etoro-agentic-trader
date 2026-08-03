"""Presentation models for the MOVRvest executive dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardPriority:
    """A priority presented to the investor."""

    title: str
    description: str
    urgency: float


@dataclass(frozen=True, slots=True)
class DashboardInvestmentCase:
    """A simplified investment thesis for dashboard presentation."""

    symbol: str
    recommendation: str
    confidence: float | None
    summary: str
    previous_decisions: str | None = None


@dataclass(frozen=True, slots=True)
class DashboardChange:
    """A meaningful change since the investor's previous visit."""

    title: str
    description: str
    category: str
    severity: str
    action_required: bool


@dataclass(frozen=True, slots=True)
class DashboardViewModel:
    """Complete presentation model for the executive dashboard."""

    headline: str
    summary: str
    confidence: float | None
    portfolio_health: float
    priorities: tuple[DashboardPriority, ...]
    investment_cases: tuple[DashboardInvestmentCase, ...]
    changes: tuple[DashboardChange, ...] = ()
