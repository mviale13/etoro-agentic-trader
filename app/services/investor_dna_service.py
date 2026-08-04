from app.domain.investor_dna import InvestorDNA
from app.domain.pattern import Pattern


class InvestorDNAService:
    def analyze(
        self,
        patterns: list[Pattern],
    ) -> InvestorDNA:
        confidence = max(
            (pattern.confidence for pattern in patterns),
            default=0,
        )

        recurring_cash_strategy = any(
            pattern.title == "Recurring Cash Strategy" for pattern in patterns
        )

        return InvestorDNA(
            confidence=confidence,
            prefers_quality=False,
            prefers_diversification=False,
            prefers_value=False,
            avoids_high_volatility=recurring_cash_strategy,
        )
