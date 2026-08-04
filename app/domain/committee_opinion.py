from dataclasses import dataclass

from app.domain.committee_evidence import CommitteeEvidence


@dataclass(frozen=True)
class CommitteeOpinion:
    member: str
    vote: str
    confidence: int
    rationale: str
    evidence: tuple[CommitteeEvidence, ...] = ()
