from app.domain.committee_opinion import CommitteeOpinion
from app.domain.portfolio_health import HealthCheck, PortfolioHealth
from app.domain.recommendation import Recommendation


class DoctorService:
    def evaluate(
        self,
        recommendation: Recommendation,
    ) -> PortfolioHealth:
        opinions = {
            opinion.member: opinion for opinion in recommendation.decision.opinions
        }

        checks = [
            self._cash_check(opinions),
            self._diversification_check(opinions),
            self._risk_check(opinions),
            self._value_check(opinions),
            self._market_check(recommendation),
        ]

        overall_score = round(sum(check.score for check in checks) / len(checks))

        next_action = self._next_action(
            overall_score,
            checks,
        )

        return PortfolioHealth(
            overall_score=overall_score,
            checks=checks,
            recommendation=next_action,
        )

    @staticmethod
    def _cash_check(
        opinions: dict[str, CommitteeOpinion],
    ) -> HealthCheck:
        opinion = opinions.get("Cash")

        if opinion is None:
            return HealthCheck(
                name="Cash",
                score=50,
                status="UNKNOWN",
                message="Cash assessment unavailable.",
            )

        if "below" in opinion.rationale.lower():
            return HealthCheck(
                name="Cash",
                score=50,
                status="WARNING",
                message=opinion.rationale,
            )

        if opinion.vote == "BUY":
            return HealthCheck(
                name="Cash",
                score=80,
                status="ACTION",
                message=opinion.rationale,
            )

        return HealthCheck(
            name="Cash",
            score=90,
            status="HEALTHY",
            message=opinion.rationale,
        )

    @staticmethod
    def _diversification_check(
        opinions: dict[str, CommitteeOpinion],
    ) -> HealthCheck:
        opinion = opinions.get("Diversification")

        if opinion is None:
            return HealthCheck(
                name="Diversification",
                score=50,
                status="UNKNOWN",
                message="Diversification assessment unavailable.",
            )

        return HealthCheck(
            name="Diversification",
            score=90 if opinion.vote == "BUY" else 60,
            status="HEALTHY" if opinion.vote == "BUY" else "WARNING",
            message=opinion.rationale,
        )

    @staticmethod
    def _risk_check(
        opinions: dict[str, CommitteeOpinion],
    ) -> HealthCheck:
        opinion = opinions.get("Risk")

        if opinion is None:
            return HealthCheck(
                name="Risk",
                score=50,
                status="UNKNOWN",
                message="Risk assessment unavailable.",
            )

        return HealthCheck(
            name="Risk",
            score=90 if opinion.vote == "BUY" else 65,
            status="HEALTHY" if opinion.vote == "BUY" else "CAUTION",
            message=opinion.rationale,
        )

    @staticmethod
    def _value_check(
        opinions: dict[str, CommitteeOpinion],
    ) -> HealthCheck:
        opinion = opinions.get("Value")

        if opinion is None:
            return HealthCheck(
                name="Value",
                score=50,
                status="UNKNOWN",
                message="Valuation assessment unavailable.",
            )

        return HealthCheck(
            name="Value",
            score=90 if opinion.vote == "BUY" else 70,
            status="HEALTHY" if opinion.vote == "BUY" else "CAUTION",
            message=opinion.rationale,
        )

    @staticmethod
    def _market_check(
        recommendation: Recommendation,
    ) -> HealthCheck:
        outlook = recommendation.intelligence.outlook

        if outlook == "BULLISH":
            score = 90
            status = "SUPPORTIVE"
        elif outlook == "BEARISH":
            score = 45
            status = "WARNING"
        else:
            score = 70
            status = "NEUTRAL"

        return HealthCheck(
            name="Market",
            score=score,
            status=status,
            message=recommendation.intelligence.summary,
        )

    @staticmethod
    def _next_action(
        overall_score: int,
        checks: list[HealthCheck],
    ) -> str:
        for check in checks:
            if check.name == "Cash" and check.status == "ACTION":
                return (
                    "Deploy a portion of available cash into "
                    "high-conviction opportunities."
                )

        for check in checks:
            if check.name == "Diversification" and check.status == "WARNING":
                return "Improve diversification before opening additional positions."

        for check in checks:
            if check.name == "Market" and check.status == "WARNING":
                return (
                    "Wait for market conditions to improve before adding new positions."
                )

        if overall_score >= 85:
            return "No immediate action required."

        if overall_score >= 70:
            return "Monitor the portfolio and reassess after the next market update."

        return "Review your portfolio before making additional investments."
