from app.domain.market_facts import MarketFacts
from app.domain.portfolio_facts import PortfolioFacts
from app.domain.risk_assessment import RiskAssessment


class RiskAssessmentService:
    def assess(
        self,
        portfolio: PortfolioFacts,
        market: MarketFacts,
    ) -> RiskAssessment:
        rationale: list[str] = []

        concentration = "LOW"

        if portfolio.cash_allocation < 10:
            concentration = "HIGH"
            rationale.append("Low cash reserve increases portfolio risk.")

        market_risk = "LOW"

        if market.vix is not None and market.vix >= 25:
            market_risk = "HIGH"
            rationale.append("Market volatility is elevated.")

        overall = (
            "HIGH" if (concentration == "HIGH" or market_risk == "HIGH") else "LOW"
        )

        return RiskAssessment(
            overall=overall,
            market=market_risk,
            concentration=concentration,
            liquidity=("LOW" if portfolio.cash_allocation >= 20 else "HIGH"),
            policy="UNKNOWN",
            rationale=tuple(rationale),
        )
