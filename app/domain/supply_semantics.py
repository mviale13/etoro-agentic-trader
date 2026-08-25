"""What a supply number actually counts — and when two of them conflict.

The rule this module exists to enforce:

> **Two numbers only conflict if they claim to represent the same thing.**

Crypto supply is an accounting vocabulary rather than a single fact, and
treating it as one figure is what made three internally-correct vendors
look like a data-quality failure. Cardano's ledger publishes four
distinguishable quantities; TokenInsight reported one, CoinGecko a
second and Yahoo a third, each to within a rounding error of the
quantity it was actually measuring. Nothing was wrong except the label
they shared.

```text
concept       what is being counted
methodology   whose definition decided what is in and out
value         the number, under that concept and that definition
```

Five concepts, and each is here because the corpus forced it — not
because a tokenomics ontology wanted completeness. `MAX_SUPPLY` exists
because four assets have a protocol-enforced cap and two have none.
`FUTURE_EMISSIONS` exists because Hyperliquid's own `totalSupply`
counts 412 million tokens that do not exist yet. `EXCLUDED_BALANCE`
exists because a circulating figure is a subtraction, and the thing
subtracted is a choice.

**`CIRCULATING_ESTIMATE` is never "the" circulating supply.** It is
always somebody's estimate under somebody's methodology, including when
the somebody is the protocol itself.

Nothing here bands, scores or interprets. Dilution is not a word this
module knows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding


class SupplyConcept(StrEnum):
    """What a supply figure counts. Five, and every one is earned."""

    #: The most that can ever exist, where the protocol enforces a cap.
    #: Absent is a real answer: Ethereum and Solana have no maximum, and
    #: inferring one from today's issuance policy would invent a
    #: constraint the protocol does not impose.
    MAX_SUPPLY = "max_supply"

    #: Tokens that exist now — minted, issued, in the ledger. The
    #: quantity a chain can usually answer without a policy, and the one
    #: closest to a primitive.
    EMITTED_SUPPLY = "emitted_supply"

    #: Tokens the protocol will issue and has not. Kept visible because
    #: a protocol-native total that silently includes them reads as
    #: tokens in existence and is wrong by exactly this amount.
    FUTURE_EMISSIONS = "future_emissions"

    #: A balance some methodology removes from circulating — a treasury,
    #: a foundation address, a fund, a burn address. Held as its own
    #: fact so the subtraction can be seen rather than assumed.
    EXCLUDED_BALANCE = "excluded_balance"

    #: What is held to be economically available, under a stated
    #: methodology. Never a primitive, never universal, and never
    #: printed without whose methodology produced it.
    CIRCULATING_ESTIMATE = "circulating_estimate"

    @property
    def stated(self) -> str:
        return _CONCEPTS[self]

    @property
    def described(self) -> str:
        return _DESCRIBED[self]

    @property
    def is_methodology_dependent(self) -> bool:
        """Whether the number depends on somebody's definition.

        The two that do are the two that made the corpus look broken.
        """

        return self in (
            SupplyConcept.CIRCULATING_ESTIMATE,
            SupplyConcept.EXCLUDED_BALANCE,
        )


_CONCEPTS = {
    SupplyConcept.MAX_SUPPLY: "Protocol maximum",
    SupplyConcept.EMITTED_SUPPLY: "Tokens currently emitted",
    SupplyConcept.FUTURE_EMISSIONS: "Future, unissued supply",
    SupplyConcept.EXCLUDED_BALANCE: "Excluded from circulating",
    SupplyConcept.CIRCULATING_ESTIMATE: "Circulating estimate",
}


_DESCRIBED = {
    SupplyConcept.MAX_SUPPLY: (
        "the most that can ever exist, where the protocol enforces a cap"
    ),
    SupplyConcept.EMITTED_SUPPLY: "tokens that exist today",
    SupplyConcept.FUTURE_EMISSIONS: (
        "tokens the protocol will issue and has not issued yet"
    ),
    SupplyConcept.EXCLUDED_BALANCE: (
        "a balance some methodology removes when it counts circulating supply"
    ),
    SupplyConcept.CIRCULATING_ESTIMATE: (
        "what one party holds to be economically available, under its "
        "own definition of what to leave out"
    ),
}


@dataclass(frozen=True, slots=True)
class SupplyMethodology:
    """Whose definition decided what is in the number, and what it leaves out.

    **The methodology is part of the fact.** A circulating figure without
    it is not a measurement anyone can check or compare — which is
    precisely how a 51% gap between two vendors became indistinguishable
    from an error.

    `disclosed` is the load-bearing field. An undisclosed methodology is
    *not* evidence of a different methodology: two vendors publishing the
    same label with unknown exclusions are presumed to be claiming the
    same fact, and they conflict if they disagree. Only a **known**
    difference lets two numbers coexist.
    """

    key: str

    #: Who defined it — a ledger, a protocol, a vendor.
    defined_by: str

    #: The definition in one sentence.
    stated: str

    #: Whether this platform knows what the definition includes and
    #: excludes. False is common and is never treated as "different".
    disclosed: bool

    includes: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()

    #: The version of the rule that produced a figure under it. Bumped
    #: when the definition changes, so a later reading is comparable
    #: with an earlier one or knowably is not.
    version: str = "1"

    @property
    def is_comparable_with(self) -> str:
        """What another figure must share to be compared with this one."""

        return f"{self.key}@{self.version}"


@dataclass(frozen=True, slots=True)
class UnitConstant:
    """A number a computation needed that was not in the data.

    Ethereum's blob base fee is why this is a first-class field rather
    than an implementation detail: computed from canonical inputs with
    the protocol constant this platform *remembered*, it came out wrong
    by a factor of about 850 million, and nothing downstream could have
    noticed.

    A constant is safe when the source states it — Hyperliquid publishes
    `weiDecimals` beside the figures — or when a wrong value would have
    produced something another source visibly contradicts. It is unsafe
    when this platform simply knew it.
    """

    name: str
    value: float

    #: Whether the source published it in the same payload.
    stated_by_source: bool

    #: How a wrong value would have been caught, where it would. None
    #: means nothing would have caught it.
    cross_check: str | None = None

    @property
    def is_safe(self) -> bool:
        return self.stated_by_source or self.cross_check is not None


@dataclass(frozen=True, slots=True)
class ComponentReconciliation:
    """The protocol's own parts, added up and checked against its total.

    Arithmetic rather than a promise. Cardano's ledger publishes seven
    quantities that must sum to its `supply`, and they do — to the
    lovelace. A figure with such an identity behind it cannot drift
    quietly; one without has nowhere to fail.
    """

    #: The identity in one checkable line.
    identity: str

    #: Each named part and its raw integer value, in the chain's own base
    #: unit. Integers, so the check is exact rather than floating.
    components: tuple[tuple[str, int], ...]

    #: What the parts sum to, and what the protocol says the total is.
    total: int
    against: int

    #: The chain's base unit — lovelace, rao, wei, or the token itself.
    base_unit: str

    #: How far apart they may be and still be the same statement. Zero
    #: for an integer ledger identity, which is the point: Cardano's
    #: residual is not "small", it is nothing.
    tolerance: int = 0

    @property
    def residual(self) -> int:
        return self.total - self.against

    @property
    def holds(self) -> bool:
        return abs(self.residual) <= self.tolerance

    @property
    def stated(self) -> str:
        if self.holds and self.residual == 0:
            return f"{self.identity} — exact, to the {self.base_unit}"

        if self.holds:
            return (
                f"{self.identity} — {self.residual:+,} {self.base_unit}, "
                "within tolerance"
            )

        return f"{self.identity} — {self.residual:+,} {self.base_unit}, unexplained"


@dataclass(frozen=True, slots=True)
class PrimaryProvenance:
    """What the establishment gate needs and a value cannot carry alone.

    Attached by the reader that took the reading, because that is the
    only place the facts are known. Absent, every gate that depends on it
    fails — which is the correct reading of a figure nobody recorded this
    much about.
    """

    #: Whether the surface serves state anyone can verify, rather than a
    #: figure only its operator computed.
    surface_is_canonical: bool

    #: How the source ties the figure to *this* asset. A chain endpoint
    #: is the asset; a contract call needs an address; a shared name
    #: never is.
    identity_because: str

    #: The rule that produced it, versioned.
    rule_version: str

    #: The transformation in one checkable line.
    formula: str

    reconciliation: ComponentReconciliation | None = None

    constants: tuple[UnitConstant, ...] = ()

    #: Why no reconciliation is available, where none is. Stated rather
    #: than left blank, because "the protocol publishes one number" and
    #: "nobody checked" look identical in an empty field.
    unreconciled_because: str | None = None


@dataclass(frozen=True, slots=True)
class SupplyFact:
    """One supply quantity, under one concept and one methodology."""

    concept: SupplyConcept
    methodology: SupplyMethodology

    value: float
    unit: str

    authority: EvidenceAuthority
    standing: EvidenceStanding

    source: str
    observed_at: datetime | None = None

    #: The label this figure arrived under, where the source used one.
    #: Kept because the label is what caused the confusion and a reader
    #: comparing with the vendor's own page needs to find it.
    reported_as: str | None = None

    #: The quantities it was computed from, where this platform computed
    #: it. Named so the subtraction can be re-run.
    components: tuple[str, ...] = ()

    #: This platform's account of what this number is.
    because: str | None = None

    #: What would make a reader misread it.
    caveats: tuple[str, ...] = ()

    #: Everything the establishment gate needs, where a chain reader
    #: recorded it. None on every vendor figure, which is correct: a
    #: vendor aggregate is judged by corroboration and is not offered
    #: the primary route at all.
    provenance: PrimaryProvenance | None = None

    @property
    def comparable_key(self) -> str:
        """What this fact claims to be. Two facts compare only if equal.

        Concept **and** methodology. Same concept under different stated
        methodologies are different facts about the same asset, and both
        can be right.
        """

        return f"{self.concept.value}/{self.methodology.is_comparable_with}"

    @property
    def stated(self) -> str:
        return f"{self.value:,.4f}".rstrip("0").rstrip(".") + f" {self.unit}"


class Comparison(StrEnum):
    """What two supply figures are to each other."""

    #: Same concept, same methodology, materially the same number.
    CORROBORATED = "corroborated"

    #: Same concept, same methodology, materially different. A real
    #: disagreement, and the only kind this module calls a conflict.
    CONFLICTED = "conflicted"

    #: Different concepts, or the same concept under stated and
    #: genuinely different methodologies. Both can be right, and the
    #: numbers differing is not evidence that either is wrong.
    COEXIST = "coexist"

    @property
    def stated(self) -> str:
        return _COMPARISONS[self]


_COMPARISONS = {
    Comparison.CORROBORATED: "Agree",
    Comparison.CONFLICTED: "Conflict",
    Comparison.COEXIST: "Measure different things",
}


#: How far two figures may differ and still be the same reading. The
#: tolerance the token-fact gate already uses for a corroboration, kept
#: identical so "agrees" means one thing on this platform.
AGREEMENT_TOLERANCE = 0.05


@dataclass(frozen=True, slots=True)
class SupplyComparison:
    """Two figures, and what they are to each other — with the reason."""

    left: SupplyFact
    right: SupplyFact

    verdict: Comparison

    #: Why they compare or do not, in words a reader can check.
    because: str

    #: The relative gap, where they were comparable at all.
    gap: float | None = None


def compare(left: SupplyFact, right: SupplyFact) -> SupplyComparison:
    """What two supply figures are to each other.

    The rule the whole slice exists for. Two numbers conflict only when
    they claim the same concept under the same methodology and disagree.
    A difference between two *different* claims is information, not a
    contradiction — and reporting it as a conflict is what suppressed
    three correct readings of Cardano.

    **An undisclosed methodology never earns coexistence.** Not knowing
    what a vendor excluded is a gap in this platform, and reading it as
    evidence that the vendor measured something else would let any two
    numbers avoid conflicting by being equally unexplained.
    """

    if left.concept is not right.concept:
        return SupplyComparison(
            left=left,
            right=right,
            verdict=Comparison.COEXIST,
            because=(
                f"{left.source} reports {left.concept.stated.lower()} and "
                f"{right.source} reports {right.concept.stated.lower()}. "
                "Different quantities, both able to be right."
            ),
        )

    gap = _gap(left.value, right.value)

    if left.methodology.key != right.methodology.key:
        if left.methodology.disclosed and right.methodology.disclosed:
            return SupplyComparison(
                left=left,
                right=right,
                verdict=Comparison.COEXIST,
                because=(
                    "Both count "
                    f"{left.concept.stated.lower()}, under stated and "
                    f"different definitions: {left.methodology.stated} "
                    f"against {right.methodology.stated}."
                ),
                gap=gap,
            )

        undisclosed = [
            fact.source for fact in (left, right) if not fact.methodology.disclosed
        ]

        if gap is not None and gap <= AGREEMENT_TOLERANCE:
            verdict = Comparison.CORROBORATED
            because = (
                "Both claim "
                f"{left.concept.stated.lower()} and agree to within "
                f"{gap * 100:.1f}%, so the undisclosed definitions did "
                "not matter here."
            )
        else:
            verdict = Comparison.CONFLICTED
            because = (
                "Both claim "
                f"{left.concept.stated.lower()} and differ by "
                f"{(gap or 0) * 100:.1f}%, and "
                f"{' and '.join(undisclosed)} do not publish what they "
                "exclude. An unexplained definition is not evidence of a "
                "different one, so this stands as a disagreement."
            )

        return SupplyComparison(
            left=left,
            right=right,
            verdict=verdict,
            because=because,
            gap=gap,
        )

    if gap is not None and gap <= AGREEMENT_TOLERANCE:
        return SupplyComparison(
            left=left,
            right=right,
            verdict=Comparison.CORROBORATED,
            because=(
                f"The same quantity under the same definition, {gap * 100:.2f}% apart."
            ),
            gap=gap,
        )

    return SupplyComparison(
        left=left,
        right=right,
        verdict=Comparison.CONFLICTED,
        because=(
            "The same quantity under the same definition, and "
            f"{(gap or 0) * 100:.1f}% apart. Nothing explains the "
            "difference."
        ),
        gap=gap,
    )


def _gap(left: float, right: float) -> float | None:
    reference = max(abs(left), abs(right))

    if reference <= 0:
        return None

    return abs(left - right) / reference


@dataclass(frozen=True, slots=True)
class UnresolvedSupply:
    """One thing this platform could not settle, and what it is about.

    The sentence was always here; the concept was not, so a surface had
    no way to tell an account of *circulating supply* apart from an
    account of the token's evidence as a whole. Without it a page
    reporting "circulating supply is not settled" printed the exclusion
    -set sentence beside it as a second, separate finding — two
    statements about one quantity.

    `concept` is None where the gap is about the whole picture rather
    than one quantity: "no chain reading for this token" is not a
    statement about circulating supply.
    """

    stated: str
    concept: SupplyConcept | None = None


@dataclass(frozen=True, slots=True)
class SupplyPicture:
    """Everything held about one token's supply, and how the parts relate."""

    symbol: str

    facts: tuple[SupplyFact, ...] = ()

    #: Every pair worth comparing, judged. Pairs of different concepts
    #: are not listed: they were never candidates for a conflict.
    comparisons: tuple[SupplyComparison, ...] = ()

    #: What could not be settled, and exactly what is missing. Empty is
    #: a real answer and so is a full list. Each item names the concept
    #: it is about, or None where it is about the whole picture.
    unresolved: tuple[UnresolvedSupply, ...] = ()

    #: Why nothing is held, where nothing is.
    unavailable_because: str | None = None

    def of(self, concept: SupplyConcept) -> tuple[SupplyFact, ...]:
        return tuple(fact for fact in self.facts if fact.concept is concept)

    @property
    def conflicts(self) -> tuple[SupplyComparison, ...]:
        return tuple(
            item for item in self.comparisons if item.verdict is Comparison.CONFLICTED
        )

    @property
    def coexisting(self) -> tuple[SupplyComparison, ...]:
        return tuple(
            item for item in self.comparisons if item.verdict is Comparison.COEXIST
        )

    @property
    def is_read(self) -> bool:
        return bool(self.facts)

    @property
    def has_methodology_disagreement(self) -> bool:
        """Whether the *circulating* estimates differ unexplained.

        Scoped to circulating estimates on purpose. Cardano has a real
        conflict — a vendor publishing the protocol maximum under the
        label "total supply", which the ledger contradicts — and its
        circulating figures nonetheless coexist. Reporting one as the
        other would tell an investor that ADA's circulating supply is
        disputed when the slice has just shown that it is not.
        """

        return any(
            item.left.concept is SupplyConcept.CIRCULATING_ESTIMATE
            for item in self.conflicts
        )
