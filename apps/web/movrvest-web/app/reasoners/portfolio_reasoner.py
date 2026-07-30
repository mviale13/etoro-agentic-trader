"""Deterministic portfolio executive reasoning."""

from app.domain.portfolio import PortfolioSnapshot
from app.domain.portfolio_assessment import (
    AssessmentCategory,
    AssessmentItem,
    AssessmentStatus,
    PortfolioAssessment,
)


class PortfolioReasoner:
    """Produces an executive assessment from a portfolio snapshot."""

    def assess(self, portfolio: PortfolioSnapshot) -> PortfolioAssessment:
        strengths: list[AssessmentItem] = []
        concerns: list[AssessmentItem] = []
        opportunities: list[AssessmentItem] = []

        # -------------------------------------------------------------
        # Liquidity
        # -------------------------------------------------------------
        if portfolio.cash_allocation >= 80:
            strengths.append(
                AssessmentItem(
                    category=AssessmentCategory.LIQUIDITY,
                    status=AssessmentStatus.POSITIVE,
                    title="Strong liquidity position",
                    explanation=(
                        "Most capital is immediately available for deployment."
                    ),
                    implication=(
                        "The portfolio can react quickly when high-conviction "
                        "investment opportunities appear."
                    ),
                    confidence=0.99,
                    evidence=(f"Cash allocation: {portfolio.cash_allocation:.1f}%",),
                )
            )
        elif portfolio.cash_allocation >= 20:
            strengths.append(
                AssessmentItem(
                    category=AssessmentCategory.LIQUIDITY,
                    status=AssessmentStatus.NEUTRAL,
                    title="Balanced liquidity",
                    explanation=(
                        "The portfolio maintains a healthy balance between cash "
                        "and invested capital."
                    ),
                    implication=("There is flexibility without excessive idle cash."),
                    confidence=0.95,
                    evidence=(f"Cash allocation: {portfolio.cash_allocation:.1f}%",),
                )
            )
        else:
            concerns.append(
                AssessmentItem(
                    category=AssessmentCategory.LIQUIDITY,
                    status=AssessmentStatus.ATTENTION,
                    title="Limited liquidity",
                    explanation=(
                        "Only a small proportion of the portfolio remains in cash."
                    ),
                    implication=(
                        "New opportunities may require selling existing holdings."
                    ),
                    confidence=0.95,
                    evidence=(f"Cash allocation: {portfolio.cash_allocation:.1f}%",),
                )
            )

        # -------------------------------------------------------------
        # Diversification
        # -------------------------------------------------------------
        if portfolio.positions == 0:
            concerns.append(
                AssessmentItem(
                    category=AssessmentCategory.DIVERSIFICATION,
                    status=AssessmentStatus.CRITICAL,
                    title="No active diversification",
                    explanation=("The portfolio currently holds no investments."),
                    implication=("Capital is protected but not compounding."),
                    confidence=1.0,
                    evidence=("Open positions: 0",),
                )
            )
        elif portfolio.positions < 5:
            concerns.append(
                AssessmentItem(
                    category=AssessmentCategory.DIVERSIFICATION,
                    status=AssessmentStatus.ATTENTION,
                    title="Limited diversification",
                    explanation=("The portfolio contains only a few positions."),
                    implication=(
                        "Individual holdings may have a larger impact on returns."
                    ),
                    confidence=0.95,
                    evidence=(f"Open positions: {portfolio.positions}",),
                )
            )
        else:
            strengths.append(
                AssessmentItem(
                    category=AssessmentCategory.DIVERSIFICATION,
                    status=AssessmentStatus.POSITIVE,
                    title="Diversification established",
                    explanation=("Capital is spread across multiple holdings."),
                    implication=("Single-position risk is reduced."),
                    confidence=0.95,
                    evidence=(f"Open positions: {portfolio.positions}",),
                )
            )

        # -------------------------------------------------------------
        # Opportunity readiness
        # -------------------------------------------------------------
        if portfolio.cash_allocation >= 50:
            opportunities.append(
                AssessmentItem(
                    category=AssessmentCategory.OPPORTUNITY_READINESS,
                    status=AssessmentStatus.POSITIVE,
                    title="Ready to invest",
                    explanation=("The portfolio has significant deployable capital."),
                    implication=(
                        "The Investment Committee can act immediately when "
                        "high-quality opportunities are identified."
                    ),
                    confidence=0.99,
                    evidence=(f"Available cash: ${portfolio.available_cash:,.0f}",),
                )
            )

        summary = (
            "Portfolio is highly liquid and ready for deployment."
            if portfolio.cash_allocation >= 80
            else "Portfolio remains invested with moderate liquidity."
        )

        return PortfolioAssessment(
            executive_summary=summary,
            strengths=tuple(strengths),
            concerns=tuple(concerns),
            opportunities=tuple(opportunities),
            confidence=0.98,
        )
