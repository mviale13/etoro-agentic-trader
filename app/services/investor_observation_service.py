from app.domain.observation import Observation
from app.domain.portfolio_snapshot import PortfolioSnapshot


class InvestorObservationService:
    def observe(self, portfolio: PortfolioSnapshot) -> Observation:
        if portfolio.allocation.cash >= 40:
            return Observation(
                title="Cash Position",
                message=(
                    "You currently hold a large cash position. "
                    "This gives you flexibility if new opportunities appear."
                ),
                category="cash",
            )

        if portfolio.positions <= 5:
            return Observation(
                title="Concentration",
                message=(
                    "Your portfolio is relatively concentrated. "
                    "Each investment will have a stronger impact on performance."
                ),
                category="risk",
            )

        if portfolio.positions >= 20:
            return Observation(
                title="Diversification",
                message=("Your portfolio is well diversified across many positions."),
                category="diversification",
            )

        return Observation(
            title="Steady Course",
            message=(
                "Your portfolio appears balanced. "
                "Staying disciplined is often an advantage."
            ),
            category="general",
        )
