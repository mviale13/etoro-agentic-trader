from collections.abc import Sequence
from typing import Protocol


class CommitteeOpinionInput(Protocol):
    """Minimum read-only contract required for committee aggregation."""

    @property
    def score(self) -> int: ...

    @property
    def confidence(self) -> float: ...

    @property
    def evidence(self) -> tuple[str, ...]: ...

    @property
    def uncertainty(self) -> tuple[str, ...]: ...


class Committee:
    """Shared aggregation behavior for research committees."""

    @staticmethod
    def aggregate_score(
        opinions: Sequence[CommitteeOpinionInput],
    ) -> int:
        if not opinions:
            return 50

        return round(sum(opinion.score for opinion in opinions) / len(opinions))

    @staticmethod
    def aggregate_confidence(
        opinions: Sequence[CommitteeOpinionInput],
    ) -> float:
        if not opinions:
            return 0.0

        return round(
            sum(opinion.confidence for opinion in opinions) / len(opinions),
            2,
        )

    @staticmethod
    def aggregate_evidence(
        opinions: Sequence[CommitteeOpinionInput],
    ) -> tuple[str, ...]:
        return tuple(item for opinion in opinions for item in opinion.evidence)

    @staticmethod
    def aggregate_uncertainty(
        opinions: Sequence[CommitteeOpinionInput],
    ) -> tuple[str, ...]:
        return tuple(item for opinion in opinions for item in opinion.uncertainty)
