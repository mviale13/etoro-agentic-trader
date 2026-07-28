from app.domain.company_facts import CompanyFacts
from app.domain.profitability_opinion import (
    ProfitabilityOpinion,
    ProfitabilityVerdict,
)


class ProfitabilityAnalyst:
    def analyze(
        self,
        company: CompanyFacts,
    ) -> ProfitabilityOpinion:
        metrics = self._available_metrics(company)

        if not metrics:
            return ProfitabilityOpinion(
                score=None,
                confidence=0.0,
                verdict=ProfitabilityVerdict.UNKNOWN,
                evidence=(),
                uncertainty=(
                    "Gross margin data is unavailable.",
                    "Operating margin data is unavailable.",
                    "Net margin data is unavailable.",
                ),
            )

        score = round(
            sum(
                self._metric_score(metric_name, value)
                for metric_name, _, value in metrics
            )
            / len(metrics)
        )

        confidence = len(metrics) / 3
        verdict = self._verdict(score)

        evidence = tuple(
            self._format_evidence(label, value) for _, label, value in metrics
        )

        uncertainty = self._uncertainty(company)

        return ProfitabilityOpinion(
            score=score,
            confidence=confidence,
            verdict=verdict,
            evidence=evidence,
            uncertainty=uncertainty,
        )

    @staticmethod
    def _available_metrics(
        company: CompanyFacts,
    ) -> tuple[tuple[str, str, float], ...]:
        metrics: list[tuple[str, str, float]] = []

        if company.gross_margin is not None:
            metrics.append(
                (
                    "gross_margin",
                    "Gross margin",
                    company.gross_margin,
                )
            )

        if company.operating_margin is not None:
            metrics.append(
                (
                    "operating_margin",
                    "Operating margin",
                    company.operating_margin,
                )
            )

        if company.net_margin is not None:
            metrics.append(
                (
                    "net_margin",
                    "Net margin",
                    company.net_margin,
                )
            )

        return tuple(metrics)

    @staticmethod
    def _metric_score(
        metric_name: str,
        value: float,
    ) -> int:
        thresholds = {
            "gross_margin": (
                (0.60, 100),
                (0.40, 85),
                (0.20, 70),
                (0.00, 40),
            ),
            "operating_margin": (
                (0.30, 100),
                (0.20, 85),
                (0.10, 70),
                (0.00, 40),
            ),
            "net_margin": (
                (0.20, 100),
                (0.10, 85),
                (0.05, 70),
                (0.00, 40),
            ),
        }

        for threshold, score in thresholds[metric_name]:
            if value >= threshold:
                return score

        return 0

    @staticmethod
    def _verdict(
        score: int,
    ) -> ProfitabilityVerdict:
        if score >= 90:
            return ProfitabilityVerdict.EXCELLENT

        if score >= 75:
            return ProfitabilityVerdict.STRONG

        if score >= 50:
            return ProfitabilityVerdict.AVERAGE

        return ProfitabilityVerdict.WEAK

    @staticmethod
    def _format_evidence(
        label: str,
        value: float,
    ) -> str:
        return f"{label} is {value:.1%}."

    @staticmethod
    def _uncertainty(
        company: CompanyFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        if company.gross_margin is None:
            uncertainty.append("Gross margin data is unavailable.")

        if company.operating_margin is None:
            uncertainty.append("Operating margin data is unavailable.")

        if company.net_margin is None:
            uncertainty.append("Net margin data is unavailable.")

        return tuple(uncertainty)
