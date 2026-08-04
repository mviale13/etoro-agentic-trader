from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.balance_sheet_opinion import (
    BalanceSheetOpinion,
    BalanceSheetVerdict,
)
from app.domain.company_facts import CompanyFacts


class BalanceSheetAnalyst(Analyst[CompanyFacts, BalanceSheetOpinion]):
    @property
    def expected_observation_count(self) -> int:
        return 2

    def observations(
        self,
        company: CompanyFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        if company.debt_to_equity is not None:
            observations.append(
                AnalystObservation(
                    key="debt_to_equity",
                    label="Debt-to-equity",
                    value=company.debt_to_equity,
                )
            )

        if company.current_ratio is not None:
            observations.append(
                AnalystObservation(
                    key="current_ratio",
                    label="Current ratio",
                    value=company.current_ratio,
                )
            )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        if observation.key == "debt_to_equity":
            return self._debt_to_equity_score(observation.value)

        if observation.key == "current_ratio":
            return self._current_ratio_score(observation.value)

        raise ValueError(f"Unsupported balance-sheet observation: {observation.key}")

    def uncertainty(
        self,
        company: CompanyFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        if company.debt_to_equity is None:
            uncertainty.append("Debt-to-equity data is unavailable.")

        if company.current_ratio is None:
            uncertainty.append("Current ratio data is unavailable.")

        return tuple(uncertainty)

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> BalanceSheetOpinion:
        return BalanceSheetOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        company: CompanyFacts,
    ) -> BalanceSheetOpinion:
        return BalanceSheetOpinion(
            score=50,
            confidence=0.0,
            verdict=BalanceSheetVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(company),
        )

    @staticmethod
    def _debt_to_equity_score(
        value: float,
    ) -> int:
        if value < 0.30:
            return 100
        if value < 0.60:
            return 85
        if value < 1.00:
            return 70
        if value < 2.00:
            return 40
        return 0

    @staticmethod
    def _current_ratio_score(
        value: float,
    ) -> int:
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
