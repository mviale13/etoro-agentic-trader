from app.domain.morning_brief import MorningBrief
from app.domain.portfolio_snapshot import PortfolioSnapshot


class MorningBriefService:
    def build(self, portfolio: PortfolioSnapshot) -> MorningBrief:
        if portfolio.allocation.cash >= 80:
            recommendation = "WAIT"
            confidence = 95
            health = "Healthy"

            summary = (
                "Your portfolio is mostly cash. "
                "There is no immediate action required."
            )
        else:
            recommendation = "REVIEW"
            confidence = 80
            health = "Balanced"

            summary = (
                "Your portfolio contains invested assets. "
                "Review your allocation before trading."
            )

        return MorningBrief(
            portfolio_health=health,
            portfolio_value=portfolio.total_value,
            cash_allocation=portfolio.allocation.cash,
            open_positions=portfolio.positions,
            recommendation=recommendation,
            confidence=confidence,
            summary=summary,
        )