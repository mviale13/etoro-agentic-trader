from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.signal import Signal

CASH_CHANGE_THRESHOLD = 10.0


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
                    message=(
                        "You currently hold a significant cash allocation. "
                        "This gives you flexibility if new opportunities appear."
                    ),
                )
            )

        if current.positions <= 5:
            signals.append(
                Signal(
                    type="concentration",
                    severity="warning",
                    title="Concentrated Portfolio",
                    message=(
                        "Your portfolio contains only a few positions. "
                        "Each investment will have a stronger impact on performance."
                    ),
                )
            )

        if current.positions >= 20:
            signals.append(
                Signal(
                    type="diversification",
                    severity="info",
                    title="Diversified Portfolio",
                    message="Your portfolio is diversified across many positions.",
                )
            )

        if previous is not None:
            cash_delta = current.allocation.cash - previous.allocation.cash

            if cash_delta >= CASH_CHANGE_THRESHOLD:
                signals.append(
                    Signal(
                        type="cash_increase",
                        severity="info",
                        title="Cash Increased",
                        message=(
                            "Cash allocation increased by "
                            f"{cash_delta:.1f} percentage points."
                        ),
                    )
                )
            elif cash_delta <= -CASH_CHANGE_THRESHOLD:
                signals.append(
                    Signal(
                        type="cash_deployed",
                        severity="info",
                        title="Cash Deployed",
                        message=(
                            "Cash allocation decreased by "
                            f"{abs(cash_delta):.1f} percentage points."
                        ),
                    )
                )

        return signals
