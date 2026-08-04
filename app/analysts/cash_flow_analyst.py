from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.cash_flow_opinion import (
    CashFlowOpinion,
    CashFlowVerdict,
)
from app.domain.company_facts import CompanyFacts


class CashFlowAnalyst(Analyst[CompanyFacts, CashFlowOpinion]):
    @property
    def expected_observation_count(self) -> int:
        return 2

    def observations(
        self,
        company: CompanyFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        if company.operating_cash_flow is not None:
            observations.append(
                AnalystObservation(
                    key="operating_cash_flow",
                    label="Operating cash flow",
                    value=company.operating_cash_flow,
                )
            )

        if company.free_cash_flow is not None:
            observations.append(
                AnalystObservation(
                    key="free_cash_flow",
                    label="Free cash flow",
                    value=company.free_cash_flow,
                )
            )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        if observation.key == "operating_cash_flow":
            return self._cash_flow_score(observation.value)

        if observation.key == "free_cash_flow":
            return self._cash_flow_score(observation.value)

        raise ValueError(f"Unsupported cash-flow observation: {observation.key}")

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        """
        A cash flow reads in billions, not to the penny.

        The base formatter's two decimals turn a hundred-billion-dollar cash
        flow into a wall of digits. Cash flow is scored by its sign, so the
        magnitude is stated compactly rather than exactly.
        """

        return f"{observation.label} is {CashFlowAnalyst._money(observation.value)}."

    @staticmethod
    def _money(value: float) -> str:
        sign = "-" if value < 0 else ""
        magnitude = abs(value)

        for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
            if magnitude >= threshold:
                return f"{sign}${magnitude / threshold:.1f}{suffix}"

        return f"{sign}${magnitude:,.0f}"

    def uncertainty(
        self,
        company: CompanyFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        if company.operating_cash_flow is None:
            uncertainty.append("Operating cash flow data is unavailable.")

        if company.free_cash_flow is None:
            uncertainty.append("Free cash flow data is unavailable.")

        return tuple(uncertainty)

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> CashFlowOpinion:
        return CashFlowOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        company: CompanyFacts,
    ) -> CashFlowOpinion:
        return CashFlowOpinion(
            score=50,
            confidence=0.0,
            verdict=CashFlowVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(company),
        )

    @staticmethod
    def _cash_flow_score(
        value: float,
    ) -> int:
        if value > 0:
            return 100

        if value == 0:
            return 50

        return 0

    @staticmethod
    def _verdict(
        score: int,
    ) -> CashFlowVerdict:
        if score >= 90:
            return CashFlowVerdict.EXCELLENT

        if score >= 75:
            return CashFlowVerdict.STRONG

        if score >= 50:
            return CashFlowVerdict.ADEQUATE

        return CashFlowVerdict.WEAK
