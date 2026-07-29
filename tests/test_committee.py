from dataclasses import dataclass

from app.committees.committee import Committee


@dataclass(frozen=True, slots=True)
class StubOpinion:
    score: int
    confidence: float
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]


def test_committee_aggregates_specialist_opinions() -> None:
    opinions = (
        StubOpinion(
            score=80,
            confidence=0.8,
            evidence=("Growth is strong.",),
            uncertainty=("Revenue data is limited.",),
        ),
        StubOpinion(
            score=60,
            confidence=0.6,
            evidence=("Margins are stable.",),
            uncertainty=("Peer comparison is unavailable.",),
        ),
    )

    assert Committee.aggregate_score(opinions) == 70
    assert Committee.aggregate_confidence(opinions) == 0.7
    assert Committee.aggregate_evidence(opinions) == (
        "Growth is strong.",
        "Margins are stable.",
    )
    assert Committee.aggregate_uncertainty(opinions) == (
        "Revenue data is limited.",
        "Peer comparison is unavailable.",
    )
