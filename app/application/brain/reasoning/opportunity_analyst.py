"""Opportunity reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
)
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
)
from app.application.brain.reasoning.models.opportunity_assessment import (
    OpportunityAssessment,
)
from app.application.brain.reasoning.models.portfolio_assessment import (
    PortfolioAssessment,
)
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)


class OpportunityAnalyst:
    """Synthesizes specialist assessments into an investment opportunity."""

    def assess(
        self,
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
        behavior: BehaviorAssessment,
    ) -> OpportunityAssessment:
        expected_upside = market.momentum_score

        timing = (market.momentum_score + (1.0 - market.volatility_score)) / 2.0

        # How ready the account is to act. This says nothing about any
        # particular security, so it is not a fit score and no longer named
        # like one — it was serving as the CIO's per-security portfolio gate,
        # where an account marked down for holding cash was refused the one
        # action that would deploy it.
        #
        # Averages the terms that were measured. When risk could not be
        # measured its term is left out rather than assumed benign, which
        # averaging in a zero would quietly do.
        readiness_terms = [portfolio.diversification_score]

        # Left out rather than substituted, on the same rule the risk
        # term below already follows: neither zero, one nor a midpoint
        # stands in for a score that was never computed.
        readiness_missing: list[str] = []

        if behavior.policy_alignment_score is not None:
            readiness_terms.append(behavior.policy_alignment_score)
        else:
            readiness_missing.append("policy alignment")

        # The risk term keeps its existing behaviour exactly: left out
        # when unmeasured, and already disclosed by its own evidence
        # line below. Naming it here too would reword every measured
        # account's readiness sentence, which is not this slice's to do.
        if risk.overall_risk_score is not None:
            readiness_terms.append(1.0 - risk.overall_risk_score)

        readiness = sum(readiness_terms) / len(readiness_terms)

        opportunity = expected_upside * 0.40 + timing * 0.30 + readiness * 0.30

        if risk.overall_risk_score is not None:
            opportunity *= 1.0 - risk.overall_risk_score * 0.25

        opportunity = max(0.0, min(opportunity, 1.0))

        confidence = (
            portfolio.confidence
            + market.confidence
            + risk.confidence
            + behavior.confidence
        ) / 4.0

        opportunities: list[str] = []
        constraints: list[str] = []
        evidence: list[Evidence] = []

        if market.momentum_score > 0.70:
            opportunities.append("Strong market momentum")

        if portfolio.diversification_score > 0.80:
            opportunities.append("Well diversified portfolio")

        if (
            behavior.policy_alignment_score is not None
            and behavior.policy_alignment_score > 0.80
        ):
            opportunities.append("Portfolio aligns with investment policy")

        if risk.overall_risk_score is not None and risk.overall_risk_score > 0.60:
            constraints.append("Elevated portfolio risk")

        if market.volatility_score > 0.70:
            constraints.append("High market volatility")

        evidence.append(
            Evidence(
                description=(f"Market momentum score is {market.momentum_score:.2f}."),
                source="MarketAssessment",
                strength=market.confidence,
            )
        )

        evidence.append(
            Evidence(
                description=(
                    f"Overall portfolio risk score is {risk.overall_risk_score:.2f}."
                    if risk.overall_risk_score is not None
                    else "Portfolio risk could not be measured."
                ),
                source="RiskAssessment",
                strength=risk.confidence,
            )
        )

        evidence.append(
            Evidence(
                description=(
                    f"Portfolio readiness score is {readiness:.2f}."
                    if not readiness_missing
                    else f"Portfolio readiness score is {readiness:.2f}, "
                    "measured without "
                    f"{' and '.join(readiness_missing)}, which could not "
                    "be scored."
                ),
                source="PortfolioAssessment",
                strength=portfolio.confidence,
            )
        )

        return OpportunityAssessment(
            opportunity_score=opportunity,
            expected_upside_score=expected_upside,
            timing_score=timing,
            portfolio_readiness_score=readiness,
            confidence=confidence,
            opportunities=tuple(opportunities),
            constraints=tuple(constraints),
            evidence=tuple(evidence),
        )
