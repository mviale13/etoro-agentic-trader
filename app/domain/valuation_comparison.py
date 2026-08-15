"""A multiple is an observation. A comparison needs a benchmark that exists.

The Valuation Authority investigation (`VALUATION_AUTHORITY.md`) found
the platform's one actively false evidence sentence: the CHEAP finding
read *"Forward P/E below historical market average"* while the only
thing compared against was the constant 18 inside `pe-bands@1`. A
benchmark this platform never held, quoted as evidence — Invariant 10
live on the dossier.

This module is the boundary that makes that sentence unproducible.
Three shapes, and the distances between them are the design:

- **`ValuationObservation`** — a measured fact: *forward P/E is 17.4×*.
  What the provider established, and nothing more.
- **`ValuationComparison`** — a relationship between that observation
  and a benchmark that *exists as evidence*: named, valued, provenanced,
  and established under a named, versioned rule. It cannot be
  constructed without one, and that is enforced in `__post_init__`
  rather than promised in prose.
- **`AbsentComparison`** — the honest third state: an observation held,
  and no benchmark to compare it against. **Not a neutral comparison.**
  Its stated form is the observation alone, because that is all the
  evidence layer may claim.

**A constant in code is not a benchmark in evidence.** `pe-bands@1`'s
18 and 28 are policy — they still band, still score and still gate,
exactly as before — but they cannot be dressed as a
`ValuationBenchmark`, because a benchmark demands provenance and
evidence and a threshold has neither. Nothing is grandfathered.

Interpretation and investment effect are deliberately not here. The
sequence this enables — Observation → Comparison → Interpretation →
Effect — stops at its first boundary in this slice, and the vocabulary
of the later layers (cheap, attractive, favourable) appears nowhere in
this module's output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.decision_rules import DecisionRule
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class ValuationObservation:
    """One measured valuation fact, exactly as strong as its source.

    The `stated` form is the whole claim the evidence layer may make
    from an absolute multiple: the metric and its value. No relation
    word, no band word, no benchmark.
    """

    #: The metric's internal name — "forward_pe".
    metric: str

    #: The metric as an investor reads it — "Forward P/E".
    label: str

    value: float

    #: How the value is written — "×" for a multiple.
    unit: str = "×"

    #: Where and when the reading was taken. None where a caller holds
    #: the provenance elsewhere; the observation is no stronger for it.
    reading: Provenance | None = None

    @property
    def stated(self) -> str:
        return f"{self.label} of {self.value:.1f}{self.unit}."


@dataclass(frozen=True, slots=True)
class ValuationBenchmark:
    """A comparison basis that exists as evidence, not as a constant.

    Construction is the gate: a benchmark must say what it is, what it
    measures, where it was read and what evidence supports it. A code
    threshold can supply none of these, which is precisely why it
    cannot become one.
    """

    #: What this benchmark is — "STOXX 600 median forward P/E".
    name: str

    value: float

    #: Where the benchmark reading was taken.
    reading: Provenance

    #: The evidence beneath it — refs a reader can follow. Never empty:
    #: a benchmark nobody can check is a constant wearing a name.
    evidence: tuple[str, ...]

    unit: str = "×"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a benchmark must say what it is")

        if not self.evidence:
            raise ValueError(
                "a benchmark with no evidence beneath it is a constant "
                "wearing a name, and a constant in code is not a benchmark "
                "in evidence"
            )


class ComparisonRelation(StrEnum):
    """What a comparison established. Descriptive, never evaluative.

    Deliberately three positions and no more: BELOW is not "cheap",
    ABOVE is not "expensive", and nothing here is favourable or
    adverse. What a relation *means* for an investment case belongs to
    the Interpretation layer, which does not exist.
    """

    BELOW = "below"
    WITHIN = "within"
    ABOVE = "above"

    @property
    def stated(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ValuationComparison:
    """An observation, related to a benchmark that exists.

    The only shape on this platform allowed to state a valuation
    relationship. It cannot be built without a benchmark, and the
    benchmark cannot be built without provenance and evidence — so a
    comparison claim carries its whole chain by construction.
    """

    observation: ValuationObservation
    benchmark: ValuationBenchmark
    relation: ComparisonRelation

    #: The named, versioned rule that established the relation.
    rule: DecisionRule

    #: Why this benchmark is the relevant one for this observation —
    #: the sentence a reader can argue with.
    because: str

    def __post_init__(self) -> None:
        if not isinstance(self.benchmark, ValuationBenchmark):
            raise TypeError(
                "a comparison requires a benchmark that exists as "
                "evidence; without one the observation stands alone as "
                "an AbsentComparison"
            )

        if not self.because.strip():
            raise ValueError(
                "a comparison must say why its benchmark is the relevant one"
            )

    @property
    def stated(self) -> str:
        return (
            f"{self.observation.stated[:-1]} — {self.relation.stated} "
            f"{self.benchmark.name} at {self.benchmark.value:.1f}"
            f"{self.benchmark.unit} ({self.rule.identity})."
        )


@dataclass(frozen=True, slots=True)
class AbsentComparison:
    """An observation with nothing evidenced to compare it against.

    The expected state for every live security today. **Not neutral,
    not FAIR, not a hedge** — a statement that the platform holds a
    multiple and no benchmark, whose stated form is the observation
    alone because that is all the evidence supports.
    """

    observation: ValuationObservation

    #: Why no comparison exists, in this platform's own words.
    because: str

    @property
    def stated(self) -> str:
        """The observation, and only the observation.

        The absence's reason is for surfaces that render gaps (the
        dossier's basis prose says it); the *finding* a committee may
        weigh is the measured fact alone.
        """

        return self.observation.stated
