from dataclasses import dataclass


@dataclass(frozen=True)
class CommitteeEvidence:
    title: str
    value: str
