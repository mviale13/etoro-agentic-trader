from dataclasses import dataclass

from app.domain.decision_rules import DecisionRule
from app.domain.finding import Finding
from app.domain.valuation_comparison import (
    AbsentComparison,
    ValuationComparison,
    ValuationObservation,
)


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

    #: The measured fact itself, kept apart from the band. None where
    #: the provider held nothing.
    observation: ValuationObservation | None = None

    #: The comparison the evidence supports. `AbsentComparison` for
    #: every live security today: a multiple is held and no benchmark
    #: is, and the two must not blur. A `ValuationComparison` can only
    #: exist with an evidenced benchmark — its constructor enforces it.
    comparison: ValuationComparison | AbsentComparison | None = None
