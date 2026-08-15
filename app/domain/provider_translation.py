"""What must be true before a provider's field becomes a domain fact.

The Provider Semantics Audit (`PROVIDER_SEMANTICS_AUDIT.md`) measured
the equity/broker boundary and found there was none: a provider field
became a domain fact in a single assignment expression, and the three
seed failures — `dividendYield` arriving at two scales under one name,
`forwardPE` accepted with an undisclosed definition, eToro's
`asset_type_id` adopted as an economic asset class — were one defect
wearing three faces.

This module is the vocabulary that makes the crossing declarable.
Four questions, asked separately because they fail separately and are
answered by different evidence:

- **Identity** — what economic instrument does this record describe?
- **Vocabulary** — what does the provider's category or token mean?
- **Unit** — what representation is the number expressed in?
- **Semantic** — what concept does the field actually measure?

And one axis beside them: the **warrant** — the authority under which
the translation is performed. A warrant is *not* a confidence score.
A numerically plausible field stays ASSUMED; a reputable provider can
supply an UNKNOWN semantic interpretation. Nothing here is numeric,
and nothing here ranks: `TranslationWarrant` deliberately supports no
ordering, because "more warranted" is not a quantity and a comparison
operator would invite exactly the generic confidence score this
boundary exists to refuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TranslationKind(StrEnum):
    """Which of the four questions a translation answers.

    One provider field may need more than one. `^TNX` is the corpus
    specimen: its value is a yield under a ×10 convention entering a
    field named `price` (a semantic translation *and* a unit one),
    while the currency beside it is invented (an assumed vocabulary
    translation). A design that allowed one kind per field could not
    have described it.
    """

    #: What economic instrument this record describes.
    IDENTITY = "identity"

    #: What the provider's category, enum or token means.
    VOCABULARY = "vocabulary"

    #: What representation the number is expressed in.
    UNIT = "unit"

    #: What concept the field actually measures.
    SEMANTIC = "semantic"

    @property
    def stated(self) -> str:
        return _KIND_LABELS[self]

    @property
    def question(self) -> str:
        """The question this kind asks, worded once."""

        return _KIND_QUESTIONS[self]


_KIND_LABELS = {
    TranslationKind.IDENTITY: "Identity",
    TranslationKind.VOCABULARY: "Vocabulary",
    TranslationKind.UNIT: "Unit",
    TranslationKind.SEMANTIC: "Semantic",
}

_KIND_QUESTIONS = {
    TranslationKind.IDENTITY: "What economic instrument does this record describe?",
    TranslationKind.VOCABULARY: "What does the provider's category or token mean?",
    TranslationKind.UNIT: "What representation is the value expressed in?",
    TranslationKind.SEMANTIC: "What concept does this field actually measure?",
}


class TranslationWarrant(StrEnum):
    """The authority under which a translation is performed.

    **Authority for a translation, never confidence in a value.** The
    distinction is the whole point: Yahoo's `dividendYield` values look
    entirely plausible and the field is UNKNOWN, because two provider
    schemas share the name at two scales and no interpretation of the
    merged field can be justified. Conversely a field can be perfectly
    ordinary and still only ASSUMED — most of this boundary is.

    Deliberately unordered. There is no `>` between DECLARED and
    ASSUMED, no numeric weight, and no arithmetic: a warrant answers
    *why are we allowed to read it this way*, and that question has no
    scale.
    """

    #: Checked against the provider by hand or by an independent
    #: source, and recorded with what was checked. The strongest thing
    #: this boundary holds.
    VERIFIED = "verified"

    #: The semantics are not independently established, but the value
    #: is checked against a domain invariant or corroborating evidence
    #: before it is accepted.
    VALIDATED = "validated"

    #: Relies on documented provider semantics — the provider states
    #: what the field means, and we hold that statement.
    DECLARED = "declared"

    #: The interpretation exists only in this platform's adapter code.
    #: A mapping that happens to be right is still ASSUMED until
    #: something outside our own source establishes it.
    ASSUMED = "assumed"

    #: Provenance is insufficient to say why the mapping would be
    #: valid at all — including where two provider schemas disagree
    #: about what the field carries.
    UNKNOWN = "unknown"

    @property
    def stated(self) -> str:
        return _WARRANT_LABELS[self]

    @property
    def because(self) -> str:
        """What this warrant asserts, worded once for every surface."""

        return _WARRANT_MEANINGS[self]

    @property
    def establishes_domain_fact(self) -> bool:
        """Whether the translation may be presented as established.

        The consumption door, and the reason this enum exists. A
        DECLARED translation is honest and still not established: the
        provider's own word is evidence about the provider, not a
        checked fact about the instrument.
        """

        return self in (TranslationWarrant.VERIFIED, TranslationWarrant.VALIDATED)


_WARRANT_LABELS = {
    TranslationWarrant.VERIFIED: "Verified",
    TranslationWarrant.VALIDATED: "Validated",
    TranslationWarrant.DECLARED: "Provider-declared",
    TranslationWarrant.ASSUMED: "Assumed",
    TranslationWarrant.UNKNOWN: "Unknown",
}

_WARRANT_MEANINGS = {
    TranslationWarrant.VERIFIED: (
        "checked against the provider or an independent source, and "
        "recorded with what was checked"
    ),
    TranslationWarrant.VALIDATED: (
        "not independently established, but checked against a domain "
        "invariant or corroborating evidence before acceptance"
    ),
    TranslationWarrant.DECLARED: (
        "relies on the provider's own documented statement of what this field means"
    ),
    TranslationWarrant.ASSUMED: (
        "the interpretation exists only in this platform's adapter code"
    ),
    TranslationWarrant.UNKNOWN: (
        "provenance is insufficient to say why this mapping would be valid"
    ),
}


class DomainRepresentation(StrEnum):
    """What a promoted number is expressed in, where that is decidable.

    Named on the translation so a unit claim can be checked rather
    than assumed. A representation is what *this platform* requires
    downstream — it never asserts what the provider intended, which is
    the standing rule the `dividendYield` measurement forced: a domain
    invariant may reject a representation; it may not invent provider
    semantics.
    """

    #: 0.12 is 12%. The convention every company fundamental on this
    #: platform is documented to use.
    DECIMAL_RATIO = "decimal_ratio"

    #: 12.0 is 12%. What several provider surfaces actually serve.
    PERCENT_POINTS = "percent_points"

    #: A bare multiple — 17.4×.
    MULTIPLE = "multiple"

    #: An amount in some currency. Which currency is a separate
    #: translation, and on this path usually an assumed one.
    CURRENCY_AMOUNT = "currency_amount"

    #: A count of things: shares, tokens, units traded.
    COUNT = "count"

    #: A point in time.
    TIMESTAMP = "timestamp"

    #: An identifier or label carrying no magnitude.
    IDENTIFIER = "identifier"

    @property
    def stated(self) -> str:
        return _REPRESENTATION_LABELS[self]


_REPRESENTATION_LABELS = {
    DomainRepresentation.DECIMAL_RATIO: "decimal ratio (0.12 is 12%)",
    DomainRepresentation.PERCENT_POINTS: "percentage points (12.0 is 12%)",
    DomainRepresentation.MULTIPLE: "multiple",
    DomainRepresentation.CURRENCY_AMOUNT: "currency amount",
    DomainRepresentation.COUNT: "count",
    DomainRepresentation.TIMESTAMP: "timestamp",
    DomainRepresentation.IDENTIFIER: "identifier",
}


class DecisionRelevance(StrEnum):
    """How far a translated field reaches, measured in #133.

    Carried on the translation because the ranked remediation list is
    a product of *warrant × reach*, and a boundary that could not say
    which unwarranted translations touch a decision would rank its own
    repairs by taste.
    """

    #: Moves a named decision rule: a band, a score, a gate or a veto.
    GATES_A_DECISION = "gates_a_decision"

    #: Reaches `decide()` as a research finding with a sense, but
    #: crosses no gate.
    SHAPES_RESEARCH = "shapes_research"

    #: Chooses which analysts run at all, and therefore which findings
    #: can exist.
    SELECTS_ANALYSIS = "selects_analysis"

    #: Rendered to the investor, consumed by no score.
    DISPLAY_ONLY = "display_only"

    #: Written and read by nothing.
    UNCONSUMED = "unconsumed"

    @property
    def stated(self) -> str:
        return _RELEVANCE_LABELS[self]

    @property
    def reaches_a_decision(self) -> bool:
        return self in (
            DecisionRelevance.GATES_A_DECISION,
            DecisionRelevance.SHAPES_RESEARCH,
            DecisionRelevance.SELECTS_ANALYSIS,
        )


_RELEVANCE_LABELS = {
    DecisionRelevance.GATES_A_DECISION: "gates a decision",
    DecisionRelevance.SHAPES_RESEARCH: "shapes research findings",
    DecisionRelevance.SELECTS_ANALYSIS: "selects which analysis runs",
    DecisionRelevance.DISPLAY_ONLY: "display only",
    DecisionRelevance.UNCONSUMED: "consumed by nothing",
}


#: How loudly an unwarranted translation should be repaired, given how
#: far it reaches. Ordering is over *reach*, which is a measured fact,
#: never over warrant, which is not a quantity.
_RELEVANCE_RANK = {
    DecisionRelevance.GATES_A_DECISION: 0,
    DecisionRelevance.SELECTS_ANALYSIS: 1,
    DecisionRelevance.SHAPES_RESEARCH: 2,
    DecisionRelevance.DISPLAY_ONLY: 3,
    DecisionRelevance.UNCONSUMED: 4,
}


@dataclass(frozen=True, slots=True)
class ProviderTranslation:
    """One governed crossing from a provider's field to a domain concept.

    The declarative unit of this boundary. Construction is the gate:
    a translation must say which questions it answers and under what
    authority, and a warrant claiming to have checked something must
    name what was checked — a VERIFIED translation with no evidence
    behind it is an assumption wearing a better word, which is the
    same failure `ValuationBenchmark` refuses in #132.
    """

    #: The service, named as the investor would see it.
    provider: str

    #: The provider's own field name, spelled exactly as it arrives.
    provider_field: str

    #: Which endpoint or schema serves it. Not decoration: Yahoo's
    #: `dividendYield` arrives from two endpoints at two scales, and
    #: without this the two claims are indistinguishable.
    endpoint: str

    #: The domain concept it becomes — "ValuationSnapshot.forward_pe".
    domain_concept: str

    #: Which of the four questions this crossing answers. Never empty,
    #: and more than one where the field needs more than one.
    kinds: tuple[TranslationKind, ...]

    warrant: TranslationWarrant

    decision_relevance: DecisionRelevance

    #: What the promoted value is expressed in, where that is
    #: decidable. Absent for identifiers and for fields whose
    #: representation is exactly what is in dispute.
    representation: DomainRepresentation | None = None

    #: The provider's own declared unit or vocabulary, where the
    #: provider actually declares one. Never inferred.
    provider_declares: str | None = None

    #: What was checked, or why nothing could be. Required for every
    #: warrant except ASSUMED, whose whole meaning is that nothing
    #: outside our code supports it.
    because: str | None = None

    def __post_init__(self) -> None:
        if not self.kinds:
            raise ValueError(
                "a translation must say which question it answers; "
                "a crossing that answers none is not a translation"
            )

        if len(set(self.kinds)) != len(self.kinds):
            raise ValueError("a translation names each kind once")

        if (
            self.warrant is not TranslationWarrant.ASSUMED
            and not (self.because or "").strip()
        ):
            raise ValueError(
                f"a {self.warrant.value} translation must say what was "
                "checked or why nothing could be; without it the warrant "
                "is an assumption wearing a better word"
            )

        if (
            self.warrant is TranslationWarrant.DECLARED
            and not (self.provider_declares or "").strip()
        ):
            raise ValueError(
                "a declared translation must name what the provider "
                "declares; a declaration nobody can point at is an "
                "assumption"
            )

    @property
    def answers(self) -> str:
        """The kinds as a surface lists them."""

        return ", ".join(kind.stated for kind in self.kinds)

    @property
    def key(self) -> tuple[str, str, str]:
        """What makes this translation unique: provider, endpoint, field."""

        return (self.provider, self.endpoint, self.provider_field)

    @property
    def establishes_domain_fact(self) -> bool:
        return self.warrant.establishes_domain_fact

    @property
    def repair_rank(self) -> tuple[int, str]:
        """Where this sits in the remediation order, by reach then name.

        Only meaningful for an unwarranted translation; a warranted one
        is not awaiting repair. Ties break on the domain concept so the
        ranked list is stable rather than dependent on registry order.
        """

        return (_RELEVANCE_RANK[self.decision_relevance], self.domain_concept)

    @property
    def stated(self) -> str:
        """The whole crossing in one sentence, worded here once."""

        representation = (
            f" as {self.representation.stated}"
            if self.representation is not None
            else ""
        )

        return (
            f"{self.provider}'s {self.provider_field} "
            f"({self.endpoint}) becomes {self.domain_concept}"
            f"{representation} — {self.warrant.stated.lower()}: "
            f"{self.warrant.because}."
        )
