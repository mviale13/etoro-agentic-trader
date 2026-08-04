from abc import ABC, abstractmethod
from typing import Any

from app.domain.analyst_observation import AnalystObservation
from app.domain.opinion import Opinion


class Analyst[InputT, OpinionT: Opinion[Any]](ABC):
    """
    Common evaluation workflow for MOVRvest analysts.

    Concrete analysts define:
    - how observations are extracted;
    - how each observation is scored;
    - how the final opinion is constructed;
    - how missing information is represented.
    """

    def analyze(self, subject: InputT) -> OpinionT:
        observations = self.observations(subject)

        if not observations:
            return self.unknown_opinion(subject)

        expected_count = self.expected_observation_count

        if expected_count <= 0:
            raise ValueError("expected_observation_count must be greater than zero")

        score = round(
            sum(self.score_observation(observation) for observation in observations)
            / len(observations)
        )

        confidence = min(
            len(observations) / expected_count,
            1.0,
        )

        evidence = tuple(
            self.format_evidence(observation) for observation in observations
        )

        return self.build_opinion(
            score=score,
            confidence=confidence,
            evidence=evidence,
            uncertainty=self.uncertainty(subject),
        )

    @property
    @abstractmethod
    def expected_observation_count(self) -> int:
        """Number of observations required for full confidence."""

    @abstractmethod
    def observations(
        self,
        subject: InputT,
    ) -> tuple[AnalystObservation, ...]:
        """Extract available observations from the subject."""

    @abstractmethod
    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        """Evaluate one observation on a 0–100 scale."""

    @abstractmethod
    def uncertainty(
        self,
        subject: InputT,
    ) -> tuple[str, ...]:
        """Explain which relevant information is unavailable."""

    @abstractmethod
    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> OpinionT:
        """Construct the analyst-specific opinion."""

    @abstractmethod
    def unknown_opinion(
        self,
        subject: InputT,
    ) -> OpinionT:
        """Construct an opinion when no observations are available."""

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        return f"{observation.label} is {observation.value:.2f}."
