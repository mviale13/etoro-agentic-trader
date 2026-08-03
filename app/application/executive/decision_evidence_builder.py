"""Build Executive DecisionEvidence from the cognitive layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.application.executive.portfolio_fit import PortfolioFit
from app.brain import Brain
from app.domain.asset_class import AssetClass
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.executive_decision import DecisionEvidence
from app.domain.finding import Finding, Sense, statements, statements_where


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

    portfolio_fit: PortfolioFit = field(default_factory=PortfolioFit)

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

        company = brain.security_evidence(symbol)

        investment = next(
            (
                opinion
                for opinion in committee_opinions
                if opinion.committee == "Investment Committee"
            ),
            None,
        )

        quality = self._quality_score(company)

        evidence_score = self._evidence_score(
            company,
            (portfolio.confidence + market.confidence + risk.confidence) / 3.0,
        )

        valuation = self._valuation_score(company)

        # Measured about this security and this account together. The
        # OpportunityAnalyst's number described only the account, so it was
        # the same for every candidate and could never say whether one of
        # them fitted better than another.
        asset_class = self._asset_class(brain, symbol)

        portfolio_fit = self.portfolio_fit.measure(
            symbol,
            brain.portfolio,
            brain.investment_policy,
            asset_class,
        )

        # Everything read about this security, each finding carrying the
        # sense the signal read it with. The full list is the record; the
        # split below is what an investment case can honestly state.
        #
        # The portfolio's strengths and the market's opportunities are not
        # in here. They are identical for every symbol, so they told the
        # reader nothing about the one in front of them. They are still
        # weighed — as scores, and as the context the case is set in — but
        # they are not evidence about a security.
        findings = tuple(dict.fromkeys(self._company_findings(company)))

        evidence_weighed = statements(findings)

        strengths = statements_where(findings, Sense.FAVOURABLE)

        risks = statements_where(findings, Sense.ADVERSE)

        context_risks = tuple(
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
            risk_score=self._risk_score(company),
            portfolio_fit_score=portfolio_fit,
            asset_class=asset_class,
            actionable_now=self._actionable_now(company, investment),
            hard_reject=False,
            analyst_veto=company is not None and company.recommendation == "SELL",
            evidence_weighed=evidence_weighed,
            strengths=strengths,
            risks=risks,
            context_risks=context_risks,
            missing_evidence=self._missing_evidence(company, symbol, asset_class),
            catalysts=catalysts,
        )

    @classmethod
    def _quality_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How good the business is, or nothing at all.

        This used to fall back to the portfolio's health score, so a company
        nobody could describe was scored with a number measured from the
        investor's account. Four unrelated companies would report the same
        quality, and that number moved their ranking.
        """

        if company is None:
            return None

        return cls.QUALITY_SCORES.get(company.signals.quality.quality)

    @classmethod
    def _risk_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How risky this security is, measured from its own price history.

        This used to be the portfolio's risk score, which was identical for
        every security and, before that, mostly two hardcoded constants. It
        is now the security's own volatility and drawdown, or nothing.
        """

        if company is None or company.signals.risk is None:
            return None

        severity = company.signals.risk.severity

        return None if severity is None else round(severity * 100)

    @classmethod
    def _valuation_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How attractive the price is, or nothing at all.

        The fallback here was market momentum, which says nothing about
        whether this company is cheap.
        """

        if company is None:
            return None

        return cls.VALUATION_SCORES.get(company.signals.value.valuation)

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
    def _asset_class(
        brain: Brain,
        symbol: str,
    ) -> AssetClass | None:
        """
        What kind of asset this is, from whichever side already knows.

        A holding carries its class; so does a watched candidate. A symbol
        that is neither returns nothing, and the policy limits that depend
        on the class are simply not applied.
        """

        normalized = symbol.upper().strip()

        for holding in brain.portfolio.holdings:
            if holding.symbol.upper().strip() == normalized and holding.asset_class:
                return AssetClass(holding.asset_class)

        for candidate in brain.candidates:
            if candidate.symbol.upper().strip() == normalized and candidate.asset_class:
                return AssetClass(candidate.asset_class)

        return None

    @staticmethod
    def _company_findings(
        company: CompanyRecommendation | None,
    ) -> tuple[Finding, ...]:
        """Everything the signals found about this security, with its sense."""

        if company is None:
            return ()

        risk = company.signals.risk

        return (
            *company.evidence,
            *(risk.evidence if risk is not None else ()),
        )

    @staticmethod
    def _missing_evidence(
        company: CompanyRecommendation | None,
        symbol: str,
        asset_class: AssetClass | None = None,
    ) -> tuple[str, ...]:
        """
        What this case is short of, and whether it can ever be supplied.

        "Valuation data is unavailable" reads as a gap a later cycle might
        close. For an asset with no company behind it there is nothing to
        become available, and saying otherwise sends the investor back to
        wait for evidence that does not exist.
        """

        if company is None:
            return (f"No security-level analysis is available for {symbol}.",)

        missing: list[str] = []

        # Only an asset positively known to have no company is told so.
        # An unclassified one is short of data, which may yet arrive.
        has_company = asset_class is None or not asset_class.has_no_company

        if company.signals.value.valuation == "UNKNOWN":
            missing.append(
                f"Valuation data is unavailable for {symbol}."
                if has_company
                else f"{symbol} has no earnings to be valued against."
            )

        if company.signals.quality.quality == "UNKNOWN":
            missing.append(
                f"Quality data is unavailable for {symbol}."
                if has_company
                else f"{symbol} has no business whose quality could be assessed."
            )

        if company.signals.risk is None or company.signals.risk.level == "UNKNOWN":
            missing.append(f"Price history for {symbol} is too short to measure risk.")

        return tuple(missing)
