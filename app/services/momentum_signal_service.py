from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
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
                evidence=(Finding.neutral("Daily price change is unavailable."),),
            )

        # The day's move is stated with the sense the trend was read with:
        # a rise is a point for the security, a fall a point against, and a
        # move too small to mean anything is neither.
        if change >= self.STRONG_POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                strength="STRONG",
                confidence=85,
                evidence=(
                    Finding.favourable(
                        f"{company.symbol} gained {change:+.2f}% today."
                    ),
                    Finding.favourable(
                        "Short-term price momentum is strongly positive."
                    ),
                ),
            )

        if change >= self.POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                strength="MODERATE",
                confidence=70,
                evidence=(
                    Finding.favourable(
                        f"{company.symbol} gained {change:+.2f}% today."
                    ),
                    Finding.favourable("Short-term price momentum is positive."),
                ),
            )

        if change <= self.STRONG_NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                strength="STRONG",
                confidence=85,
                evidence=(
                    Finding.adverse(f"{company.symbol} declined {change:+.2f}% today."),
                    Finding.adverse("Short-term price momentum is strongly negative."),
                ),
            )

        if change <= self.NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                strength="MODERATE",
                confidence=70,
                evidence=(
                    Finding.adverse(f"{company.symbol} declined {change:+.2f}% today."),
                    Finding.adverse("Short-term price momentum is negative."),
                ),
            )

        return MomentumSignal(
            trend="NEUTRAL",
            strength="WEAK",
            confidence=60,
            evidence=(
                Finding.neutral(f"{company.symbol} moved {change:+.2f}% today."),
                Finding.neutral("No meaningful short-term momentum is visible."),
            ),
        )
