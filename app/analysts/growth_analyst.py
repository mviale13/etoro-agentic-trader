from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.company_facts import CompanyFacts
from app.domain.growth_opinion import GrowthOpinion, GrowthVerdict


class GrowthAnalyst(Analyst[CompanyFacts, GrowthOpinion]):
    @property
    def expected_observation_count(self) -> int:
        return 2

    def observations(
        self,
        company: CompanyFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        if company.revenue_growth is not None:
            observations.append(
                AnalystObservation(
                    key="revenue_growth",
                    label="Revenue growth",
                    value=company.revenue_growth,
                )
            )

        if company.earnings_growth is not None:
            observations.append(
                AnalystObservation(
                    key="earnings_growth",
                    label="Earnings growth",
                    value=company.earnings_growth,
                )
            )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        return self._metric_score(observation.value)

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

        if company.revenue_growth is None:
            uncertainty.append("Revenue growth data is unavailable.")

        if company.earnings_growth is None:
            uncertainty.append("Earnings growth data is unavailable.")

        return tuple(uncertainty)

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> GrowthOpinion:
        return GrowthOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        company: CompanyFacts,
    ) -> GrowthOpinion:
        return GrowthOpinion(
            score=50,
            confidence=0.0,
            verdict=GrowthVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(company),
        )

    @staticmethod
    def _metric_score(
        value: float,
    ) -> int:
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
    def _verdict(
        score: int,
    ) -> GrowthVerdict:
        if score >= 80:
            return GrowthVerdict.STRONG

        if score >= 55:
            return GrowthVerdict.MODERATE

        if score >= 40:
            return GrowthVerdict.WEAK

        return GrowthVerdict.DECLINING
