from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Opinion[VerdictT]:
    """Typed conclusion produced by an analyst or committee.

    An opinion represents an explainable judgment rather than raw data.

    Every opinion consists of:
    - a verdict (the conclusion),
    - a score (relative strength),
    - a confidence level,
    - supporting evidence,
    - remaining uncertainties.

    A conclusive opinion should normally contain evidence. An unknown
    opinion may instead be justified entirely by uncertainty about missing
    or insufficient data.
    """

    score: int
    confidence: float
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]
    verdict: VerdictT

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

        if not self.evidence and not self.uncertainty:
            raise ValueError(
                "opinion must contain at least one piece of evidence or uncertainty"
            )

        if any(not item.strip() for item in self.evidence):
            raise ValueError("evidence entries must not be blank")

        if any(not item.strip() for item in self.uncertainty):
            raise ValueError("uncertainty entries must not be blank")
