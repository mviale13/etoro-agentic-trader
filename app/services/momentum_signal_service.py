from app.domain.company_facts import CompanyFacts
from app.domain.momentum_signal import MomentumSignal


class MomentumSignalService:
    STRONG_POSITIVE_THRESHOLD = 2.0
    POSITIVE_THRESHOLD = 0.5
    NEGATIVE_THRESHOLD = -0.5
    STRONG_NEGATIVE_THRESHOLD = -2.0

    def build(
        self,
        company: CompanyFacts,
    ) -> MomentumSignal:
        change = company.daily_change_pct

        if change is None:
            return MomentumSignal(
                trend="UNKNOWN",
                strength="UNKNOWN",
                confidence=20,
                evidence=("Daily price change is unavailable.",),
            )

        if change >= self.STRONG_POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                strength="STRONG",
                confidence=85,
                evidence=(
                    f"{company.symbol} gained {change:+.2f}% today.",
                    "Short-term price momentum is strongly positive.",
                ),
            )

        if change >= self.POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                strength="MODERATE",
                confidence=70,
                evidence=(
                    f"{company.symbol} gained {change:+.2f}% today.",
                    "Short-term price momentum is positive.",
                ),
            )

        if change <= self.STRONG_NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                strength="STRONG",
                confidence=85,
                evidence=(
                    f"{company.symbol} declined {change:+.2f}% today.",
                    "Short-term price momentum is strongly negative.",
                ),
            )

        if change <= self.NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                strength="MODERATE",
                confidence=70,
                evidence=(
                    f"{company.symbol} declined {change:+.2f}% today.",
                    "Short-term price momentum is negative.",
                ),
            )

        return MomentumSignal(
            trend="NEUTRAL",
            strength="WEAK",
            confidence=60,
            evidence=(
                f"{company.symbol} moved {change:+.2f}% today.",
                "No meaningful short-term momentum is visible.",
            ),
        )
