from app.domain.portfolio_health import PortfolioHealth


class PortfolioHealthService:
    def build(self) -> PortfolioHealth:
        return PortfolioHealth(
            overall_score=75,
            recommendation="Invest 15% of cash into SPY.",
            checks=[],
        )
