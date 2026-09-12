"""Risk reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.models.assessment import (
    AssessmentLevel,
    Evidence,
    assessment_level,
)
from app.domain.market_risk import MarketRisk


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """
    Structured interpretation of portfolio downside.

    A component nothing measures is None, not a number. `overall_risk_score`
    averages the components that were measured, and `unmeasured` names the
    ones that were not, so a partial reading is never mistaken for a
    complete one.
    """

    overall_risk_score: float | None
    market_risk_score: float | None
    concentration_risk_score: float | None
    liquidity_risk_score: float | None
    drawdown_risk_score: float | None
    confidence: float
    risk_factors: tuple[str, ...] = field(default_factory=tuple)
    mitigants: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    #: Risks the platform cannot currently measure, named rather than scored.
    unmeasured: tuple[str, ...] = field(default_factory=tuple)

    #: The exposure measurement `market_risk_score` was derived from, or
    #: None where none could be taken.
    #:
    #: **Carried so a surface can state what the score is a score _of_.**
    #: The blended volatility, the share of the account it covers and the
    #: instruments it was read from all existed here and were discarded,
    #: leaving only a 0–1 number and a sentence — so a page wanting to
    #: say "18.0% annualised, describing 45.7% of the account" had to
    #: parse it back out of the sentence, which is how a presentation
    #: layer starts inventing facts.
    #:
    #: **Read by presentation only.** Nothing in the decision path
    #: consults it; the CIO reads the scores, and this changes none of
    #: them.
    market_exposure: MarketRisk | None = None

    #: The fall the investor said they could accept, where they said one
    #: — and **None where the platform's own default was applied**.
    #:
    #: Carried because `drawdown_risk_score` is a ratio against one or
    #: the other, and only this analyst knows which. A surface reaching
    #: for a policy of its own to answer that would sooner or later
    #: answer with a *different* policy's figure, and tell the investor
    #: they had set a limit they never set.
    drawdown_limit_pct: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "overall_risk_score",
            "market_risk_score",
            "concentration_risk_score",
            "liquidity_risk_score",
            "drawdown_risk_score",
            "confidence",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @property
    def risk_level(self) -> AssessmentLevel | None:
        """The band the measured risk falls in, or None if nothing was."""

        if self.overall_risk_score is None:
            return None

        return assessment_level(self.overall_risk_score)
