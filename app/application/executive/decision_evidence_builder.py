"""Build Executive DecisionEvidence from the cognitive layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.brain import Brain
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.executive_decision import DecisionEvidence


@dataclass(slots=True)
class DecisionEvidenceBuilder:
    """
    Translate cognitive outputs into Executive DecisionEvidence.

    The symbol belongs to the investment case being evaluated,
    not to the portfolio snapshot.

    Portfolio reasoning describes the account as a whole and is therefore
    identical for every holding. Per-security evidence, when the Brain holds
    any, is what distinguishes one investment case from another. Where it is
    missing the evidence says so, rather than letting portfolio-level scores
    stand in for security-level judgement.
    """

    # Signal bands are aligned to DecisionPolicy's own gates so a qualitative
    # signal lands in the band it describes:
    #   below 35 -> rejected, 60 -> may prepare, 75 -> may recommend.
    #
    # LOW quality sits above the rejection floor deliberately: the security
    # committee rates such holdings HOLD, and the Artificial CIO must not
    # reject an investment case its own committee is content to hold. A
    # genuine sell opinion is expressed through analyst_veto instead.

    #: Quality of the security itself, by signal.
    QUALITY_SCORES = {
        "HIGH": 80,
        "MEDIUM": 62,
        "LOW": 40,
    }

    #: Attractiveness of the price paid, by signal.
    VALUATION_SCORES = {
        "CHEAP": 80,
        "FAIR": 55,
        "EXPENSIVE": 25,
    }

    def build(
        self,
        symbol: str,
        brain: Brain,
        reasoning: ReasoningSnapshot,
        committee_opinions: tuple[CommitteeOpinion, ...],
    ) -> DecisionEvidence:
        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        company = self._company_evidence(brain, symbol)

        investment = next(
            (
                opinion
                for opinion in committee_opinions
                if opinion.committee == "Investment Committee"
            ),
            None,
        )

        quality = self._quality_score(company, portfolio.health_score)

        evidence_score = self._evidence_score(
            company,
            (portfolio.confidence + market.confidence + risk.confidence) / 3.0,
        )

        valuation = self._valuation_score(company, market.momentum_score)

        # The OpportunityAnalyst already weighs diversification, policy
        # alignment and risk into a portfolio-fit score, so the CIO uses that
        # judgement rather than recomputing a cruder one of its own.
        portfolio_fit = int(reasoning.opportunity.portfolio_fit_score * 100)

        strengths = tuple(
            dict.fromkeys(
                (
                    *self._company_strengths(company),
                    *portfolio.strengths,
                    *market.opportunities,
                )
            )
        )

        risks = tuple(
            dict.fromkeys(
                (
                    *portfolio.weaknesses,
                    *market.risks,
                    *risk.risk_factors,
                    # Behavioural biases are risks to the decision, not to the
                    # security: acting against your own policy is a way to
                    # lose money regardless of what the asset does.
                    *reasoning.behavior.observed_biases,
                    *reasoning.opportunity.constraints,
                )
            )
        )

        catalysts = tuple(
            dict.fromkeys(
                (
                    *market.opportunities,
                    *reasoning.opportunity.opportunities,
                )
            )
        )

        return DecisionEvidence(
            symbol=symbol,
            quality_score=quality,
            evidence_score=evidence_score,
            valuation_score=valuation,
            risk_score=int(risk.overall_risk_score * 100),
            portfolio_fit_score=portfolio_fit,
            actionable_now=self._actionable_now(company, investment),
            hard_reject=False,
            analyst_veto=company is not None and company.recommendation == "SELL",
            strengths=strengths,
            risks=risks,
            missing_evidence=self._missing_evidence(company, symbol),
            catalysts=catalysts,
        )

    @staticmethod
    def _company_evidence(
        brain: Brain,
        symbol: str,
    ) -> CompanyRecommendation | None:
        """Return the Brain's evidence about this security, if it holds any."""

        return next(
            (
                item
                for item in brain.evidence_for(symbol)
                if isinstance(item, CompanyRecommendation)
            ),
            None,
        )

    @classmethod
    def _quality_score(
        cls,
        company: CompanyRecommendation | None,
        portfolio_health: float,
    ) -> int:
        if company is None:
            return int(portfolio_health * 100)

        return cls.QUALITY_SCORES.get(
            company.signals.quality.quality,
            int(portfolio_health * 100),
        )

    @classmethod
    def _valuation_score(
        cls,
        company: CompanyRecommendation | None,
        market_momentum: float,
    ) -> int:
        if company is None:
            return int(market_momentum * 100)

        return cls.VALUATION_SCORES.get(
            company.signals.value.valuation,
            int(market_momentum * 100),
        )

    @staticmethod
    def _evidence_score(
        company: CompanyRecommendation | None,
        cognitive_confidence: float,
    ) -> int:
        """
        How well evidenced this specific case is.

        Without security-level evidence the case rests on portfolio context
        alone, which is weaker ground for a single-name decision.
        """

        cognitive = int(cognitive_confidence * 100)

        if company is None:
            return int(cognitive * 0.6)

        return int((cognitive + company.confidence) / 2)

    @staticmethod
    def _actionable_now(
        company: CompanyRecommendation | None,
        investment: CommitteeOpinion | None,
    ) -> bool:
        if company is not None:
            return company.recommendation == "BUY"

        return investment is not None and investment.recommendation in (
            Recommendation.BUY,
            Recommendation.STRONG_BUY,
        )

    @staticmethod
    def _company_strengths(
        company: CompanyRecommendation | None,
    ) -> tuple[str, ...]:
        if company is None:
            return ()

        return company.evidence

    @staticmethod
    def _missing_evidence(
        company: CompanyRecommendation | None,
        symbol: str,
    ) -> tuple[str, ...]:
        if company is None:
            return (f"No security-level analysis is available for {symbol}.",)

        missing: list[str] = []

        if company.signals.value.valuation == "UNKNOWN":
            missing.append(f"Valuation data is unavailable for {symbol}.")

        if company.signals.quality.quality == "UNKNOWN":
            missing.append(f"Quality data is unavailable for {symbol}.")

        return tuple(missing)
