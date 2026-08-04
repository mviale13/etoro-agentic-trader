"""Investor-facing executive brief."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutiveBrief:
    """Human-readable communication of an executive recommendation."""

    title: str
    headline: str
    narrative: str
    confidence_label: str
    confidence: float
    priority: float
    opportunities: tuple[str, ...]
    risks: tuple[str, ...]
