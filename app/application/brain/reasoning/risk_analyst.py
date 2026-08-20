"""Risk reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)
from app.brain import Brain
from app.domain.market_risk import MarketRisk
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.services.market_risk_service import MarketRiskService
from app.services.portfolio_drawdown_service import PortfolioDrawdownService


class RiskAnalyst:
    """Evaluate overall portfolio risk."""

    #: One term of `cognitive-confidence@1`: this analyst's confidence
    #: is a constant. Named so the provenance guard can fingerprint it —
    #: the audit found it, and naming it endorses nothing.
    CONFIDENCE = 0.80

    def __init__(
        self,
        market_risk_service: MarketRiskService | None = None,
    ) -> None:
        self._market_risk_service = market_risk_service or MarketRiskService()

    def assess(
        self,
        source: Brain,
    ) -> RiskAssessment:
        portfolio = source.portfolio
        policy = source.investment_policy

        liquidity = self._liquidity_risk(portfolio)
        concentration = self._concentration_risk(portfolio)

        tolerance = policy.constraints.max_drawdown if policy is not None else None
        drawdown = self._drawdown_risk(portfolio.drawdown, tolerance)

        # Measured from the market this account is actually exposed to. None
        # where too little of the account could be assigned a benchmark, which
        # is reported as unmeasured rather than as calm.
        exposure = self._market_risk_service.measure(source.market, portfolio)

        market = (
            MarketRiskService.risk_score(exposure) if exposure is not None else None
        )

        # Market risk and drawdown risk were 0.50 each — two constants that
        # between them made up most of every risk score the investor saw.
        # Both are measurements now, so overall risk is one too.
        #
        # It stays absent while any component is missing. Averaging the
        # components that were measured would report a low risk for an
        # account whose exposure nobody had looked at, and a low number
        # flatters the case, because the Artificial CIO scores low risk as
        # conviction.
        overall = self._overall(
            market=market,
            concentration=concentration,
            liquidity=liquidity,
            drawdown=drawdown,
        )

        risk_factors: list[str] = []
        mitigants: list[str] = []
        evidence: list[Evidence] = []

        if exposure is not None:
            evidence.append(self._market_evidence(exposure))

        if portfolio.drawdown is not None:
            evidence.append(self._drawdown_evidence(portfolio.drawdown))

        if drawdown is not None and drawdown >= 1.0:
            risk_factors.append(self._breach(tolerance))

        # Three states. A guarded two-way branch would send the absent
        # case to the `else` and record "Healthy cash allocation" as a
        # mitigant — an unread figure arguing that the account is safe.
        cash = portfolio.allocation.cash

        if cash is None:
            pass
        elif cash < 10:
            risk_factors.append("Low cash buffer")

            evidence.append(
                Evidence(
                    description=f"Cash allocation is only {cash:.1f}%.",
                    source="PortfolioSnapshot",
                    strength=0.95,
                )
            )
        else:
            mitigants.append("Healthy cash allocation")

        if portfolio.largest_position_pct > 25:
            risk_factors.append("High portfolio concentration")

            evidence.append(
                Evidence(
                    description=(
                        "Largest holding represents "
                        f"{portfolio.largest_position_pct:.1f}% "
                        "of the portfolio."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.90,
                )
            )

        unmeasured: list[str] = []

        if cash is None:
            unmeasured.append(
                "Cash and liquidity risk are not measured: the broker "
                "stated no cash figure."
            )

        if market is None:
            unmeasured.append("Market risk is not measured.")

        if drawdown is None:
            unmeasured.append("Drawdown risk is not measured.")

        return RiskAssessment(
            overall_risk_score=overall,
            market_risk_score=market,
            concentration_risk_score=concentration,
            liquidity_risk_score=liquidity,
            drawdown_risk_score=drawdown,
            confidence=self.CONFIDENCE,
            risk_factors=tuple(risk_factors),
            mitigants=tuple(mitigants),
            evidence=tuple(evidence),
            unmeasured=tuple(unmeasured),
        )

    @staticmethod
    def _overall(
        market: float | None,
        concentration: float | None,
        liquidity: float | None,
        drawdown: float | None,
    ) -> float | None:
        """
        The four components together, or nothing while one is missing.

        Deliberately not an average of whatever happens to be available.
        Each component describes a different way this account can lose
        money, and a mean of three of them is not a smaller version of
        the answer — it is a different question, reported under the same
        name and read as complete.
        """

        components = (market, concentration, liquidity, drawdown)

        if any(component is None for component in components):
            return None

        measured = [component for component in components if component is not None]

        return sum(measured) / len(measured)

    def _market_evidence(
        self,
        exposure: MarketRisk,
    ) -> Evidence:
        """
        What the account is exposed to, slice by slice.

        The blend alone would hide the shape: 3% blended volatility reads
        as a calm market, when what it actually says here is that almost
        none of the account is in the market at all.
        """

        slices = ", ".join(
            f"{item.share * 100:.1f}% {item.exposure}"
            + (
                " (does not move with the market)"
                if not item.benchmarks
                else f" at {item.volatility * 100:.1f}% ({', '.join(item.benchmarks)})"
            )
            for item in exposure.exposures
        )

        statement = (
            "The market this account is exposed to has moved "
            f"{exposure.volatility * 100:.1f}% annualised: {slices}."
        )

        if exposure.uncovered_share > 0:
            statement += (
                f" {exposure.uncovered_share * 100:.1f}% of the account has no "
                "benchmark and is excluded."
            )

        return Evidence(
            description=statement,
            source=(
                exposure.reading.stated()
                if exposure.reading is not None
                else "MarketSnapshot"
            ),
            strength=0.90,
        )

    @staticmethod
    def _drawdown_risk(
        drawdown: PortfolioDrawdown | None,
        tolerance_pct: float | None,
    ) -> float | None:
        """
        How far the account fell, against how far the investor allowed.

        None where the balance history could not be read or was too short
        to measure. The account's positions cannot stand in for it: what
        each holding did separately is not what the account did.
        """

        if drawdown is None:
            return None

        return PortfolioDrawdownService.risk_score(drawdown, tolerance_pct)

    @staticmethod
    def _breach(
        tolerance_pct: float | None,
    ) -> str:
        """
        Which limit the account has reached, and whose limit it is.

        A default the platform chose and a figure the investor gave are
        not the same claim, and a risk factor that says "stated" when
        nobody stated anything invites an argument with a limit the
        investor never set.
        """

        if tolerance_pct is not None and tolerance_pct > 0:
            return (
                "Drawdown has reached the "
                f"{tolerance_pct:.0f}% the investor said they could accept"
            )

        return (
            "Drawdown has reached the "
            f"{PortfolioDrawdownService.DEFAULT_TOLERANCE_PCT:.0f}% this platform "
            "applies where the investor has stated no limit"
        )

    @staticmethod
    def _drawdown_evidence(
        drawdown: PortfolioDrawdown,
    ) -> Evidence:
        """
        The fall, the window it was measured over, and where it stands now.

        The window is named rather than implied. A year is asked for and
        as much of it as the account has lived through comes back, so the
        same sentence can describe twelve months or five weeks — and those
        are not the same claim about an account.
        """

        statement = (
            f"The account fell {drawdown.depth * 100:.1f}% from its peak on "
            f"{drawdown.peak_on:%d %b %Y} to its low on "
            f"{drawdown.trough_on:%d %b %Y}, "
            f"measured over {drawdown.observations} daily balances."
        )

        if drawdown.recovered:
            statement += " It has since recovered to a new high."
        else:
            statement += (
                f" It is still {drawdown.current_depth * 100:.1f}% below that peak."
            )

        return Evidence(
            description=statement,
            source=drawdown.reading.stated(),
            # The broker's own record of what the account was worth. There
            # is no more direct evidence of this available anywhere.
            strength=0.95,
        )

    def _liquidity_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float | None:
        cash = portfolio.allocation.cash

        if cash is None:
            # None, not 0.0: a zero here would say this account carries
            # no liquidity risk, and `_overall` would then average a
            # flattering number into a score the CIO reads.
            return None

        return max(
            0.0,
            min(
                (10.0 - cash) / 10.0,
                1.0,
            ),
        )

    def _concentration_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        return min(
            portfolio.largest_position_pct / 100.0,
            1.0,
        )
