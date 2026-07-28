from app.domain.balance_sheet_opinion import (
    BalanceSheetOpinion,
    BalanceSheetVerdict,
)
from app.domain.company_facts import CompanyFacts


class BalanceSheetAnalyst:
    def analyze(
        self,
        company: CompanyFacts,
    ) -> BalanceSheetOpinion:
        metrics = self._available_metrics(company)

        if not metrics:
            return BalanceSheetOpinion(
                score=None,
                confidence=0.0,
                verdict=BalanceSheetVerdict.UNKNOWN,
                evidence=(),
                uncertainty=(
                    "Debt-to-equity data is unavailable.",
                    "Current ratio data is unavailable.",
                ),
            )

        score = round(
            sum(
                self._metric_score(metric_name, value)
                for metric_name, _, value in metrics
            )
            / len(metrics)
        )

        confidence = len(metrics) / 2
        verdict = self._verdict(score)

        evidence = tuple(
            self._format_evidence(label, value) for _, label, value in metrics
        )

        uncertainty = self._uncertainty(company)

        return BalanceSheetOpinion(
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

        if company.debt_to_equity is not None:
            metrics.append(
                (
                    "debt_to_equity",
                    "Debt-to-equity",
                    company.debt_to_equity,
                )
            )

        if company.current_ratio is not None:
            metrics.append(
                (
                    "current_ratio",
                    "Current ratio",
                    company.current_ratio,
                )
            )

        return tuple(metrics)

    @staticmethod
    def _metric_score(
        metric_name: str,
        value: float,
    ) -> int:
        if metric_name == "debt_to_equity":
            if value < 0.30:
                return 100
            if value < 0.60:
                return 85
            if value < 1.00:
                return 70
            if value < 2.00:
                return 40
            return 0

        if value > 2.0:
            return 100
        if value > 1.5:
            return 85
        if value > 1.2:
            return 70
        if value > 1.0:
            return 40
        return 0

    @staticmethod
    def _verdict(
        score: int,
    ) -> BalanceSheetVerdict:
        if score >= 90:
            return BalanceSheetVerdict.EXCELLENT

        if score >= 75:
            return BalanceSheetVerdict.STRONG

        if score >= 50:
            return BalanceSheetVerdict.ADEQUATE

        return BalanceSheetVerdict.WEAK

    @staticmethod
    def _format_evidence(
        label: str,
        value: float,
    ) -> str:
        return f"{label} is {value:.2f}."

    @staticmethod
    def _uncertainty(
        company: CompanyFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        if company.debt_to_equity is None:
            uncertainty.append("Debt-to-equity data is unavailable.")

        if company.current_ratio is None:
            uncertainty.append("Current ratio data is unavailable.")

        return tuple(uncertainty)
