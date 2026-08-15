from dataclasses import dataclass

from app.domain.decision_rules import DecisionRule
from app.domain.finding import Finding


@dataclass(frozen=True, slots=True)
class ValueSignal:
    valuation: str

    confidence: int

    evidence: tuple[Finding, ...]

    #: The signal's own account of why it reads as it does, where it has
    #: one. The same field `QualitySignal` grew, for the same failure:
    #: asked to explain an UNKNOWN, the executive builder said "the
    #: figures a price is judged against could not be read" — about
    #: assets that have no earnings to be priced against, where nothing
    #: is going to become readable. Absent here, that wording still
    #: stands for the company path, where it is true.
    basis: str | None = None
    #: The named, versioned rule that assigned this reading its meaning
    #: — identity, never endorsement. None where nothing was banded: an
    #: UNKNOWN produced by absence had no meaning assigned at all.
    rule: DecisionRule | None = None
