from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class InvestmentThesis:
    symbol: str

    recommendation: str

    confidence: float

    summary: str

    strengths: tuple[str, ...]

    risks: tuple[str, ...]

    catalysts: tuple[str, ...]

    invalidation_conditions: tuple[str, ...]

    expected_holding_period: str

    created_at: datetime

    #: What the Artificial CIO decided about this symbol before, stated as
    #: fact. None when nothing was ever recorded — the CIO does not claim a
    #: history it does not have.
    previous_decisions: str | None = None
