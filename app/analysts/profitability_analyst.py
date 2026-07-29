from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.company_facts import CompanyFacts
from app.domain.profitability_opinion import (
    ProfitabilityOpinion,
    ProfitabilityVerdict,
)


class ProfitabilityAnalyst(Analyst[CompanyFacts, ProfitabilityOpinion]):
    @property
    def expected_observation_count(self) -> int:
        return 3

    def observations(
        self,
        company: CompanyFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        if company.gross_margin is not None:
            observations.append(
                AnalystObservation(
                    key="gross_margin",
                    label="Gross margin",
                    value=company.gross_margin,
                )
            )

        if company.operating_margin is not None:
            observations.append(
                AnalystObservation(
                    key="operating_margin",
                    label="Operating margin",
                    value=company.operating_margin,
                )
            )

        if company.net_margin is not None:
            observations.append(
                AnalystObservation(
                    key="net_margin",
                    label="Net margin",
                    value=company.net_margin,
                )
            )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        return self._metric_score(
            observation.key,
            observation.value,
        )

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        return f"{observation.label} is {observation.value:.1%}."

    def uncertainty(
        self,
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

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> ProfitabilityOpinion:
        return ProfitabilityOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        company: CompanyFacts,
    ) -> ProfitabilityOpinion:
        return ProfitabilityOpinion(
            score=50,
            confidence=0.0,
            verdict=ProfitabilityVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(company),
        )

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

        try:
            metric_thresholds = thresholds[metric_name]
        except KeyError as error:
            raise ValueError(
                f"Unsupported profitability observation: {metric_name}"
            ) from error

        for threshold, score in metric_thresholds:
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
            return ProfitabilityVerdict.ADEQUATE

        return ProfitabilityVerdict.WEAK
