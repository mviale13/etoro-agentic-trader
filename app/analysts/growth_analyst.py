from app.domain.company_facts import CompanyFacts
from app.domain.growth_opinion import GrowthOpinion, GrowthVerdict


class GrowthAnalyst:
    def analyze(
        self,
        company: CompanyFacts,
    ) -> GrowthOpinion:
        metrics = self._available_metrics(company)

        if not metrics:
            return GrowthOpinion(
                score=None,
                confidence=0.0,
                verdict=GrowthVerdict.UNKNOWN,
                evidence=(),
                uncertainty=(
                    "Revenue growth data is unavailable.",
                    "Earnings growth data is unavailable.",
                ),
            )

        score = round(
            sum(self._metric_score(value) for _, value in metrics) / len(metrics)
        )

        confidence = len(metrics) / 2
        verdict = self._verdict(score)

        evidence = tuple(
            self._format_evidence(label, value) for label, value in metrics
        )

        uncertainty = self._uncertainty(company)

        return GrowthOpinion(
            score=score,
            confidence=confidence,
            verdict=verdict,
            evidence=evidence,
            uncertainty=uncertainty,
        )

    @staticmethod
    def _available_metrics(
        company: CompanyFacts,
    ) -> tuple[tuple[str, float], ...]:
        metrics: list[tuple[str, float]] = []

        if company.revenue_growth is not None:
            metrics.append(("Revenue", company.revenue_growth))

        if company.earnings_growth is not None:
            metrics.append(("Earnings", company.earnings_growth))

        return tuple(metrics)

    @staticmethod
    def _metric_score(value: float) -> int:
        if value >= 0.30:
            return 100

        if value >= 0.20:
            return 85

        if value >= 0.10:
            return 70

        if value >= 0.05:
            return 55

        if value >= 0.0:
            return 45

        if value >= -0.10:
            return 25

        return 0

    @staticmethod
    def _verdict(score: int) -> GrowthVerdict:
        if score >= 80:
            return GrowthVerdict.STRONG

        if score >= 55:
            return GrowthVerdict.MODERATE

        if score >= 40:
            return GrowthVerdict.WEAK

        return GrowthVerdict.DECLINING

    @staticmethod
    def _format_evidence(
        label: str,
        value: float,
    ) -> str:
        return f"{label} growth is {value:.1%}."

    @staticmethod
    def _uncertainty(
        company: CompanyFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        if company.revenue_growth is None:
            uncertainty.append("Revenue growth data is unavailable.")

        if company.earnings_growth is None:
            uncertainty.append("Earnings growth data is unavailable.")

        return tuple(uncertainty)
