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

    #: Whether this question applies to the security at all.
    #:
    #: False only where the platform positively knows it does not — a
    #: fund has no earnings to be priced against. Distinct from an
    #: UNKNOWN band, which means the question applies and the answer is
    #: not established: the first leaves the decision's expected set,
    #: the second stays in it and lowers coverage.
    applicable: bool = True
