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
class SupplyPicture:
    """Everything held about one token's supply, and how the parts relate."""

    symbol: str

    facts: tuple[SupplyFact, ...] = ()

    #: Every pair worth comparing, judged. Pairs of different concepts
    #: are not listed: they were never candidates for a conflict.
    comparisons: tuple[SupplyComparison, ...] = ()

    #: What could not be settled, and exactly what is missing. Empty is
    #: a real answer and so is a full list.
    unresolved: tuple[str, ...] = ()

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
