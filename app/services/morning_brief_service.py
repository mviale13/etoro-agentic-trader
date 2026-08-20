from app.domain.morning_brief import MorningBrief
from app.domain.portfolio_snapshot import PortfolioSnapshot


class MorningBriefService:
    def build(self, portfolio: PortfolioSnapshot) -> MorningBrief:
        cash = portfolio.allocation.cash

        if cash is None:
            # Neither branch below is available: "mostly cash" and "contains
            # invested assets" are both claims about a figure nobody read.
            recommendation = "REVIEW"
            confidence = 50
            health = "Unavailable"

            summary = (
                "Your available cash could not be read, so this brief cannot "
                "describe your allocation. Nothing here says what your cash "
                "position is."
            )
        elif cash >= 80:
            recommendation = "WAIT"
            confidence = 95
            health = "Healthy"

            summary = (
                "Your portfolio is mostly cash. There is no immediate action required."
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
