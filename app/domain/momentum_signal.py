from dataclasses import dataclass

from app.domain.decision_rules import DecisionRule
from app.domain.finding import Finding


@dataclass(frozen=True, slots=True)
class MomentumSignal:
    trend: str
    strength: str
    confidence: int
    evidence: tuple[Finding, ...]
    #: The named, versioned rule that assigned this reading its meaning
    #: — identity, never endorsement. None where nothing was banded: an
    #: UNKNOWN produced by absence had no meaning assigned at all.
    rule: DecisionRule | None = None
