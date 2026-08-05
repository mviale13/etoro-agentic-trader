from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.decision_history import DecisionTrend
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class InvestmentThesis:
    symbol: str

    recommendation: str

    #: How far the committees that spoke agreed. None where none could.
    confidence: float | None

    #: The Artificial CIO's own conviction in this decision, 0-100.
    #:
    #: It was never carried here, so a brief could show a RECOMMEND above
    #: the committees' agreement and nothing about how strongly the CIO
    #: held the view. The two answer different questions and are now both
    #: reported, each under its own name.
    conviction: int

    summary: str

    #: What the signals found for and against this security.
    strengths: tuple[str, ...]

    risks: tuple[str, ...]

    catalysts: tuple[str, ...]

    invalidation_conditions: tuple[str, ...]

    expected_holding_period: str

    created_at: datetime

    #: Every finding the signals read about this security itself,
    #: favourable or not. Without it an investment case says nothing that
    #: tells one security apart from another.
    evidence_weighed: tuple[str, ...] = ()

    #: What the portfolio and the market look like around this security.
    #:
    #: These describe the account and the conditions, not the security —
    #: "Healthy liquidity" is a fact about the investor's cash, and reads
    #: as a fact about the security only because of where it is printed.
    context_strengths: tuple[str, ...] = ()

    #: Risks of the account and the market, not of this security.
    context_risks: tuple[str, ...] = ()

    #: When the security's evidence was read. None where none was read.
    evidence_as_of: Provenance | None = None

    #: Which way this case has been moving across recorded decisions —
    #: stable, improving or deteriorating. None when nothing was ever
    #: recorded: the CIO does not claim a history it does not have, and a
    #: first review is not a stable one.
    trend: DecisionTrend | None = None
