from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.signal import Signal


class SignalService:
    def analyze(
        self,
        current: PortfolioSnapshot,
        previous: PortfolioSnapshot | None,
    ) -> list[Signal]:
        signals: list[Signal] = []

        if current.allocation.cash >= 40:
            signals.append(
                Signal(
                    type="cash",
                    severity="info",
                    title="High Cash Position",
                    message="You currently hold a significant cash allocation.",
                )
            )

        if current.positions <= 5:
            signals.append(
                Signal(
                    type="concentration",
                    severity="warning",
                    title="Concentrated Portfolio",
                    message="Your portfolio contains only a few positions.",
                )
            )

        return signals
