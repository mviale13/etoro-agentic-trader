"""One token's playbook: which questions apply, and what could answer them.

The object a surface consumes. It joins three things that were built
apart and must stay apart:

```text
ArchetypeAssignment   what kind of economic object this is
Applicability         whether a question applies to that kind
EvidenceStanding      whether anything here can answer it
```

The join is derived on read and stores nothing new. That matters more
than it sounds: `QuestionCell` below is the *product* of applicability
and standing, so the two can never be confused at the source. A cell
reading **not applicable** was decided without consulting a single
figure, and a cell reading **evidence insufficient** was decided
without consulting the archetype's opinion of the question.

Nothing here is an answer. There is no verdict field, no score, no
band, and no ordering that implies one — a question with established
evidence sits beside one without it, and neither is better than the
other until something is allowed to conclude.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.crypto_archetype import ArchetypeAssignment
from app.domain.crypto_questions import (
    Applicability,
    CryptoQuestion,
    EvidenceDemand,
    QuestionApplicability,
)
from app.domain.evidence_standing import EvidenceStanding
from app.domain.token_value_flow import ValueChain


class ValueUnit(StrEnum):
    """How a figure is worded. Formatting, and nothing more."""

    MONEY = "money"
    COUNT = "count"
    RANK = "rank"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class DemandCoverage:
    """One evidence demand, met or unmet, with the standing of what met it."""

    demand: EvidenceDemand

    standing: EvidenceStanding

    #: The figure, where the standing permits one to be shown.
    value: float | None = None
    unit: ValueUnit = ValueUnit.NONE

    source: str | None = None
    observed_at: datetime | None = None

    #: Which economic entity supplied it, where a protocol metric did.
    #: Never omitted for a security with more than one: the whole S2
    #: identity discipline collapses the moment a figure loses its
    #: entity.
    entity: str | None = None

    #: The source's own definition, verbatim, where the demand asked for
    #: the definition rather than the figure.
    methodology: str | None = None

    #: The account of the standing, in the evidence family's own words.
    because: str | None = None

    @property
    def is_met(self) -> bool:
        """Whether something answers this demand at all, at any standing."""

        return self.standing is not EvidenceStanding.ABSENT

    @property
    def stated(self) -> str | None:
        """The figure as a surface prints it, worded here once."""

        if self.methodology is not None:
            return f"“{self.methodology}”"

        if self.value is None or not self.standing.serves_value:
            return None

        if self.unit is ValueUnit.RANK:
            return f"#{self.value:,.0f}"

        if self.unit is ValueUnit.COUNT:
            return f"{self.value:,.0f}"

        if self.unit is ValueUnit.MONEY:
            return _money(self.value)

        return f"{self.value:,.2f}"


def _money(value: float) -> str:
    """An amount at a unit that keeps it visible.

    Billions are the right unit for a network and the wrong one for a
    provider that has lost track of a token: $8,105 printed as "$0.00bn"
    reads as a rounding rather than as the nonsense it was.
    """

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    if value >= 1_000:
        return f"${value / 1_000:,.1f}k"

    return f"${value:,.0f}"


class QuestionCell(StrEnum):
    """Applicability and evidence, joined for one reading.

    Derived, never stored. The four states the ruling's matrix needs,
    and each is the product of two independent facts rather than a new
    judgment: *does this apply* comes from the archetype alone, *can it
    be answered* from the evidence alone.
    """

    #: Applies, and something established answers it.
    ASK = "ask"

    #: Applies, and nothing established answers it. The acquisition
    #: roadmap: the demands beneath it say exactly what is missing.
    ASK_EVIDENCE_INSUFFICIENT = "ask_evidence_insufficient"

    #: The wrong question for this kind of asset. Not a gap, and never
    #: a reason to go looking.
    NOT_APPLICABLE = "not_applicable"

    #: No archetype was established, so applicability is unknown.
    UNDETERMINED = "undetermined"

    @property
    def stated(self) -> str:
        return _CELLS[self]


_CELLS = {
    QuestionCell.ASK: "Ask",
    QuestionCell.ASK_EVIDENCE_INSUFFICIENT: "Ask — evidence insufficient",
    QuestionCell.NOT_APPLICABLE: "Not applicable",
    QuestionCell.UNDETERMINED: "Undetermined",
}


@dataclass(frozen=True, slots=True)
class QuestionCoverage:
    """One question against one security: does it apply, and what is held."""

    question: CryptoQuestion
    applicability: Applicability
    covered: tuple[DemandCoverage, ...] = ()

    @property
    def best_standing(self) -> EvidenceStanding:
        """The firmest standing anything answering this reaches."""

        for standing in (
            EvidenceStanding.ESTABLISHED,
            EvidenceStanding.CLAIMED,
            EvidenceStanding.CONFLICTED,
            EvidenceStanding.REJECTED,
        ):
            if any(item.standing is standing for item in self.covered):
                return standing

        return EvidenceStanding.ABSENT

    @property
    def cell(self) -> QuestionCell:
        """The joined reading. Two independent facts, multiplied here."""

        if self.applicability.state is QuestionApplicability.UNDETERMINED:
            return QuestionCell.UNDETERMINED

        if self.applicability.state is (
            QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE
        ):
            return QuestionCell.NOT_APPLICABLE

        if self.best_standing is EvidenceStanding.ESTABLISHED:
            return QuestionCell.ASK

        return QuestionCell.ASK_EVIDENCE_INSUFFICIENT

    @property
    def conflicts(self) -> tuple[DemandCoverage, ...]:
        """Demands two sources answer differently, and incompatibly.

        Kept visible rather than folded into the standing, because a
        question can read *answerable* on one established demand while
        the demand at the heart of it is contested — HYPE's supply
        question stands on an established cap and a circulating count
        the sources put 51% apart, and only one of those facts is the
        one an investor is actually asking about.
        """

        return tuple(
            item
            for item in self.covered
            if item.standing is EvidenceStanding.CONFLICTED
        )

    @property
    def unmet(self) -> tuple[EvidenceDemand, ...]:
        """What would answer this question and is not held.

        The acquisition demand, in the same currency every other demand
        on this platform is stated in. Empty for a question nothing is
        missing from; never consulted for one that does not apply.
        """

        return tuple(item.demand for item in self.covered if not item.is_met)


@dataclass(frozen=True, slots=True)
class CryptoPlaybook:
    """Everything this platform holds about how to read one token."""

    symbol: str

    assignment: ArchetypeAssignment

    #: Every question, asked or not — the full matrix row for this
    #: security. A question is never omitted for being inapplicable:
    #: an omitted question and a declined one look identical to a
    #: reader, and they are opposite statements.
    coverage: tuple[QuestionCoverage, ...]

    #: One value chain per mapped economic entity, never one per
    #: security. Empty where none is mapped.
    chains: tuple[ValueChain, ...] = ()

    #: Why no economic entity is mapped, where none is.
    unmapped_because: str | None = None

    def question(self, key: str) -> QuestionCoverage | None:
        for item in self.coverage:
            if item.question.key.value == key:
                return item

        return None

    @property
    def asked(self) -> tuple[QuestionCoverage, ...]:
        return tuple(
            item
            for item in self.coverage
            if item.cell in (QuestionCell.ASK, QuestionCell.ASK_EVIDENCE_INSUFFICIENT)
        )

    @property
    def declined(self) -> tuple[QuestionCoverage, ...]:
        return tuple(
            item for item in self.coverage if item.cell is QuestionCell.NOT_APPLICABLE
        )

    @property
    def answerable(self) -> tuple[QuestionCoverage, ...]:
        return tuple(item for item in self.coverage if item.cell is QuestionCell.ASK)
