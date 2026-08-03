"""Risk reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)
from app.brain import Brain
from app.domain.brain_context import BrainContext
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.services.portfolio_drawdown_service import PortfolioDrawdownService


class RiskAnalyst:
    """Evaluate overall portfolio risk."""

    def assess(
        self,
        source: Brain | BrainContext,
    ) -> RiskAssessment:
        portfolio = source.portfolio
        policy = source.investment_policy

        liquidity = self._liquidity_risk(portfolio)
        concentration = self._concentration_risk(portfolio)

        tolerance = policy.constraints.max_drawdown if policy is not None else None
        drawdown = self._drawdown_risk(portfolio.drawdown, tolerance)

        # Market risk and drawdown risk were 0.50 each — two constants that
        # between them made up most of every risk score the investor saw.
        # Drawdown is now read off the account's own balance history;
        # market risk still needs a volatility series nothing supplies.
        #
        # Overall risk stays absent while any component is missing. Averaging
        # the components that are measured would report a low risk for an
        # account whose market exposure nobody has looked at — and a low
        # number flatters the case, because the Artificial CIO scores low
        # risk as conviction.
        overall = None

        risk_factors: list[str] = []
        mitigants: list[str] = []
        evidence: list[Evidence] = []

        if portfolio.drawdown is not None:
            evidence.append(self._drawdown_evidence(portfolio.drawdown))

        if drawdown is not None and drawdown >= 1.0:
            risk_factors.append(self._breach(tolerance))

        if portfolio.allocation.cash < 10:
            risk_factors.append("Low cash buffer")

            evidence.append(
                Evidence(
                    description=(
                        f"Cash allocation is only {portfolio.allocation.cash:.1f}%."
                    ),
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

        unmeasured = ["Market risk is not measured."]

        if drawdown is None:
            unmeasured.append("Drawdown risk is not measured.")

        return RiskAssessment(
            overall_risk_score=overall,
            market_risk_score=None,
            concentration_risk_score=concentration,
            liquidity_risk_score=liquidity,
            drawdown_risk_score=drawdown,
            confidence=0.80,
            risk_factors=tuple(risk_factors),
            mitigants=tuple(mitigants),
            evidence=tuple(evidence),
            unmeasured=tuple(unmeasured),
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
    ) -> float:
        return max(
            0.0,
            min(
                (10.0 - portfolio.allocation.cash) / 10.0,
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
