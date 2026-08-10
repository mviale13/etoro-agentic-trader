"""When a chain reading may stand as established without a second vendor.

The Model C gate, as the owner ruled it. It exists because of one
measurement: computed from canonical inputs, with the protocol constant
this platform *remembered*, Ethereum's blob base fee came out wrong by a
factor of about 850 million and nothing downstream could have noticed.
So the rule is emphatically **not**

> deterministic primary computation → ESTABLISHED

and is instead six requirements that all have to hold:

```text
1  identity     the canonical source confirms this is the asset
2  semantics    reconciled against the protocol's own components
3  constants    no remembered, unstated protocol constant
4  reproducible obtainable again without trusting this reading
5  perimeter    compared with another observation, differences exposed
6  versioned    rule, formula and the state it was read at, retained
```

Two of them are the ones that would have caught the blob fee. **Gate 3**
is the direct fix: the constant was this platform's memory of a protocol
parameter, and nothing stated or checked it. **Gate 2** is the deeper
one: a figure that must add up against the protocol's own components has
somewhere to fail loudly, and a figure standing alone has nowhere.

A gate that cannot be evaluated **fails**. Not knowing whether a
computation used a remembered constant is exactly the state the blob fee
was in, and treating an unknown as a pass would rebuild the hole this
gate was cut to close.

Nothing here interprets. An established emitted supply is a quantity,
not a judgment about a token's future.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.evidence_standing import EvidenceStanding
from app.domain.supply_semantics import (
    Comparison,
    SupplyComparison,
    SupplyConcept,
    SupplyFact,
)

__all__ = [
    "EstablishmentVerdict",
    "GateResult",
    "ModelCRequirement",
    "assess",
]


class ModelCRequirement(StrEnum):
    """One of the six. All must hold; none is weighted against another."""

    IDENTITY = "identity"
    SEMANTICS = "semantics"
    CONSTANTS = "constants"
    REPRODUCIBLE = "reproducible"
    PERIMETER = "perimeter"
    VERSIONED = "versioned"

    @property
    def stated(self) -> str:
        return _REQUIREMENTS[self]

    @property
    def asks(self) -> str:
        return _ASKS[self]


_REQUIREMENTS = {
    ModelCRequirement.IDENTITY: "Identity",
    ModelCRequirement.SEMANTICS: "Semantics",
    ModelCRequirement.CONSTANTS: "Constants",
    ModelCRequirement.REPRODUCIBLE: "Reproducibility",
    ModelCRequirement.PERIMETER: "Perimeter",
    ModelCRequirement.VERSIONED: "Versioning",
}


_ASKS = {
    ModelCRequirement.IDENTITY: (
        "does the canonical source confirm this figure is about this asset?"
    ),
    ModelCRequirement.SEMANTICS: (
        "does the figure reconcile against the protocol's own components?"
    ),
    ModelCRequirement.CONSTANTS: (
        "is every constant either stated by the source or independently checked?"
    ),
    ModelCRequirement.REPRODUCIBLE: (
        "could a stranger obtain this again without trusting this reading?"
    ),
    ModelCRequirement.PERIMETER: (
        "was it compared with another observation, and any difference exposed?"
    ),
    ModelCRequirement.VERSIONED: (
        "are the rule, the formula and the state it was read at recorded?"
    ),
}


@dataclass(frozen=True, slots=True)
class GateResult:
    """One requirement, and whether this reading met it."""

    requirement: ModelCRequirement
    passed: bool
    because: str


@dataclass(frozen=True, slots=True)
class EstablishmentVerdict:
    """Whether one primary reading may stand as established, and why.

    Carries every gate whether it passed or failed. A verdict that
    listed only the failure would hide how close a reading came, and
    which single acquisition would change it.
    """

    concept: SupplyConcept
    source: str

    gates: tuple[GateResult, ...]

    #: The standing this reading may be served at.
    standing: EvidenceStanding

    because: str

    @property
    def establishes(self) -> bool:
        return self.standing is EvidenceStanding.ESTABLISHED

    @property
    def failed(self) -> tuple[GateResult, ...]:
        return tuple(gate for gate in self.gates if not gate.passed)

    @property
    def blocking(self) -> ModelCRequirement | None:
        """The first gate that failed, where one did."""

        return self.failed[0].requirement if self.failed else None


def assess(
    fact: SupplyFact,
    comparisons: tuple[SupplyComparison, ...] = (),
) -> EstablishmentVerdict:
    """Whether this primary reading clears all six gates.

    Only a *primary* reading is a candidate. A vendor aggregate is
    judged by the ordinary corroboration rule and is not offered this
    route — Model C is about what canonical state may settle on its own,
    not a shortcut for anything single-sourced.
    """

    if not fact.authority.is_primary:
        return EstablishmentVerdict(
            concept=fact.concept,
            source=fact.source,
            gates=(),
            standing=fact.standing,
            because=(
                f"{fact.source} is a {fact.authority.stated.lower()} rather "
                "than a reading of canonical state, so the primary route "
                "does not apply. Its standing is whatever corroboration "
                "gave it."
            ),
        )

    gates = (
        _identity(fact),
        _semantics(fact),
        _constants(fact),
        _reproducible(fact),
        _perimeter(fact, comparisons),
        _versioned(fact),
    )

    failed = [gate for gate in gates if not gate.passed]

    if failed:
        return EstablishmentVerdict(
            concept=fact.concept,
            source=fact.source,
            gates=gates,
            standing=EvidenceStanding.CLAIMED,
            because=(
                f"{len(gates) - len(failed)} of {len(gates)} Model C "
                f"requirements hold. {failed[0].because} A primary "
                "reading that fails any gate is served as the source's "
                "claim, which is what it is."
            ),
        )

    return EstablishmentVerdict(
        concept=fact.concept,
        source=fact.source,
        gates=gates,
        standing=EvidenceStanding.ESTABLISHED,
        because=(
            "All six Model C requirements hold, so this reading of "
            "canonical state establishes without a second vendor. "
            "Establishment rests on the gate, never on the reading being "
            "primary — primary is not a synonym for true."
        ),
    )


# ── the six ──────────────────────────────────────────────────────────


def _identity(fact: SupplyFact) -> GateResult:
    provenance = fact.provenance

    if provenance is None or not provenance.identity_because:
        return GateResult(
            requirement=ModelCRequirement.IDENTITY,
            passed=False,
            because=(
                "Nothing records how the source ties this figure to this "
                "asset, so identity is unconfirmed."
            ),
        )

    return GateResult(
        requirement=ModelCRequirement.IDENTITY,
        passed=True,
        because=provenance.identity_because,
    )


def _semantics(fact: SupplyFact) -> GateResult:
    provenance = fact.provenance

    if provenance is None:
        return GateResult(
            requirement=ModelCRequirement.SEMANTICS,
            passed=False,
            because="No provenance was recorded, so nothing was reconciled.",
        )

    reconciliation = provenance.reconciliation

    if reconciliation is None:
        return GateResult(
            requirement=ModelCRequirement.SEMANTICS,
            passed=False,
            because=(
                provenance.unreconciled_because
                or (
                    "The protocol publishes this figure and no components "
                    "to check it against, so its meaning rests on a label."
                )
            ),
        )

    if not reconciliation.holds:
        return GateResult(
            requirement=ModelCRequirement.SEMANTICS,
            passed=False,
            because=(
                f"The protocol's own components do not add up: {reconciliation.stated}."
            ),
        )

    return GateResult(
        requirement=ModelCRequirement.SEMANTICS,
        passed=True,
        because=(
            f"Reconciled against the protocol's components: {reconciliation.stated}."
        ),
    )


def _constants(fact: SupplyFact) -> GateResult:
    provenance = fact.provenance

    if provenance is None:
        return GateResult(
            requirement=ModelCRequirement.CONSTANTS,
            passed=False,
            because=(
                "No provenance was recorded, so whether the computation "
                "leaned on a remembered constant is unknown — which is "
                "the state the blob-fee error was in."
            ),
        )

    unsafe = [constant for constant in provenance.constants if not constant.is_safe]

    if unsafe:
        names = ", ".join(constant.name for constant in unsafe)

        return GateResult(
            requirement=ModelCRequirement.CONSTANTS,
            passed=False,
            because=(
                f"The computation needs {names}, which this platform "
                "remembered rather than read, and nothing would catch a "
                "wrong value."
            ),
        )

    if not provenance.constants:
        return GateResult(
            requirement=ModelCRequirement.CONSTANTS,
            passed=True,
            because=(
                "The source publishes the figure in the token's own units, "
                "so the computation needs no constant at all."
            ),
        )

    return GateResult(
        requirement=ModelCRequirement.CONSTANTS,
        passed=True,
        because=" ".join(
            (
                f"{constant.name} is "
                + (
                    "published by the source in the same payload."
                    if constant.stated_by_source
                    else f"checked: {constant.cross_check}"
                )
            )
            for constant in provenance.constants
        ),
    )


def _reproducible(fact: SupplyFact) -> GateResult:
    provenance = fact.provenance

    if provenance is None or not provenance.surface_is_canonical:
        return GateResult(
            requirement=ModelCRequirement.REPRODUCIBLE,
            passed=False,
            because=(
                "The figure comes from a surface serving one party's "
                "computation rather than state anyone can verify, so "
                "repeating it is not checking it."
            ),
        )

    if not fact.components:
        return GateResult(
            requirement=ModelCRequirement.REPRODUCIBLE,
            passed=False,
            because=(
                "The inputs are not named, so a stranger has no way to "
                "fetch them again."
            ),
        )

    return GateResult(
        requirement=ModelCRequirement.REPRODUCIBLE,
        passed=True,
        because=(
            f"Read from canonical state via {', '.join(fact.components)}, "
            f"transformed by {provenance.formula}."
        ),
    )


def _perimeter(
    fact: SupplyFact,
    comparisons: tuple[SupplyComparison, ...],
) -> GateResult:
    """Gate 5 — compared where possible, and every difference exposed.

    Note what this does *not* require: agreement. A perimeter comparison
    that surfaces a real difference has done its job, and Hyperliquid is
    the case — its own emitted supply and CoinGecko's differ by 38.6%
    because the vendor is counting tokens the protocol says do not exist
    yet. Suppressing that to obtain a pass would be the opposite of the
    gate.
    """

    relevant = [
        comparison
        for comparison in comparisons
        if comparison.left.concept is fact.concept
        and fact.source in (comparison.left.source, comparison.right.source)
    ]

    if not relevant:
        return GateResult(
            requirement=ModelCRequirement.PERIMETER,
            passed=False,
            because=(
                "No other source reports this quantity, so the perimeter "
                "of the reading has not been tested against anything."
            ),
        )

    corroborated = [
        item for item in relevant if item.verdict is Comparison.CORROBORATED
    ]
    conflicted = [item for item in relevant if item.verdict is Comparison.CONFLICTED]

    if corroborated:
        return GateResult(
            requirement=ModelCRequirement.PERIMETER,
            passed=True,
            because=(
                f"Compared with {len(relevant)} other reading(s); "
                f"{corroborated[0].because}"
            ),
        )

    if conflicted:
        return GateResult(
            requirement=ModelCRequirement.PERIMETER,
            passed=True,
            because=(
                f"Compared and the difference is exposed rather than "
                f"resolved: {conflicted[0].because}"
            ),
        )

    return GateResult(
        requirement=ModelCRequirement.PERIMETER,
        passed=True,
        because=(
            f"Compared with {len(relevant)} other reading(s): {relevant[0].because}"
        ),
    )


def _versioned(fact: SupplyFact) -> GateResult:
    provenance = fact.provenance

    if provenance is None or not provenance.rule_version:
        return GateResult(
            requirement=ModelCRequirement.VERSIONED,
            passed=False,
            because=(
                "No rule version is recorded, so a later rule could only "
                "replace this figure rather than recompute it."
            ),
        )

    if fact.observed_at is None:
        return GateResult(
            requirement=ModelCRequirement.VERSIONED,
            passed=False,
            because="The state this was read at is not recorded.",
        )

    return GateResult(
        requirement=ModelCRequirement.VERSIONED,
        passed=True,
        because=(
            f"Rule {provenance.rule_version}, read at "
            f"{fact.observed_at:%Y-%m-%d %H:%M} UTC."
        ),
    )
