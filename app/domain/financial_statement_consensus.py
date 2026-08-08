"""What repeated readings of one statement agree the filer printed.

The consensus architecture applied to the statement stream, unchanged
in every rule that matters: content-blind strict majority per claim
over the observations that addressed it, settled values verbatim an
observation's, ties and pluralities settling nothing, derived on every
read and never stored. `docs/architecture/KNOWLEDGE_CONSENSUS.md`
governs; this module only points it at a different claim set.

The comparable answer for a located fact is the **anchor** — the
printed value at its cell address, with the filer's row label. Two
readings that found the same figure in the same cell agree, whatever
the rest of the row held, because the row is read by the platform off
the anchored row and cannot vary independently of it.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.agreement import Agreement, agreement
from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.knowledge_consensus import QUORUM, ConsensusState
from app.domain.primary_source import PrimarySource
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import ReportedFigure

#: The comparable form of an absence. Content-blind: a worded absence
#: wins a majority exactly as a located figure does.
NO_FIGURE = "no figure located"


@dataclass(frozen=True, slots=True)
class ConsensusFact:
    """One concept, as the observations that addressed it agree.

    Field names mirror `StatementFact` deliberately: a settled claim
    reads exactly as an observed one, an unsettled claim reads as an
    absence whose reason carries the distribution, and a consumer
    reads either without knowing which it was given. Beside the claim
    sits its `Agreement`, so 3/5 and 5/5 never look identical.
    """

    concept: StatementConcept

    #: How many observations addressed this concept, of how many taken.
    addressed_in: int
    observations: int

    #: The settled anchor — verbatim the checked figure of an
    #: observation that gave the modal answer — or None with the
    #: reason worded.
    anchor: ReportedFigure | None

    #: That observation's platform-read row, travelling with its
    #: anchor. Empty where the anchor is absent.
    row: tuple[ReportedFigure, ...]

    unlocated_because: str | None

    agreement: Agreement

    @property
    def is_located(self) -> bool:
        """Whether the statement was settled to print this figure."""

        return self.anchor is not None


@dataclass(frozen=True, slots=True)
class FinancialStatementConsensus:
    """What this platform treats as knowledge of one primary statement.

    Derived from stored observations on every read and never stored
    itself. When a warranting assessment kind eventually consumes
    these figures, it consumes this object only — an observation
    reaches the decision path through the consensus function or not
    at all, the knowledge platform's standing rule.
    """

    symbol: str

    statement: StatementKind

    source: PrimarySource

    observation_count: int
    quorum: int
    state: ConsensusState

    #: How many places in the document could have opened this statement,
    #: as every observation of it recorded. Above one, these figures came
    #: from a section chosen among contenders: the figures are the
    #: filer's and checked, and the claim that they are *this statement*
    #: is an interpretation. Reported, never silently asserted.
    located_among: int

    facts: tuple[ConsensusFact, ...]

    #: The derivation, stated, dated to the newest observation.
    reading: Provenance

    @property
    def is_quorate(self) -> bool:
        return self.state is ConsensusState.QUORATE

    @property
    def provenance_uncertain(self) -> bool:
        """Whether more than one section could have been this statement."""

        return self.located_among > 1

    def provenance_caveat(self) -> str | None:
        """What a reader is owed about where these figures came from.

        Three states, and only one of them is silent. A statement whose
        title occurs once is located beyond doubt and says nothing. A
        statement with several contenders says the choice among them was
        an interpretation. And a reading taken before this platform
        counted says *that* — never nothing, because an unrecorded count
        is not evidence of a single contender, and letting it read as
        one would be the confident claim this measurement exists to
        stop being made.
        """

        if self.located_among == 0:
            return (
                "These readings were taken before this platform recorded how "
                "many sections of the filing could have been this statement, "
                "so how firmly it was located is unknown. The figures are the "
                "filer's and were checked against the cells they sit in; "
                "which section they were read from is not established. "
                "Observing this statement again records it."
            )

        if not self.provenance_uncertain:
            return None

        return (
            f"This filing prints this statement's title in "
            f"{self.located_among} structural positions, and this platform "
            "read the widest of them. The figures below are the filer's and "
            "were checked against the cells they sit in; that they are the "
            "audited statement rather than a discussion of it is an "
            "interpretation this platform has not established."
        )

    def fact(self, concept: StatementConcept) -> ConsensusFact | None:
        """The consensus on one concept, if any observation addressed it."""

        for fact in self.facts:
            if fact.concept is concept:
                return fact

        return None

    @property
    def located_facts(self) -> tuple[ConsensusFact, ...]:
        """The concepts whose figures settled."""

        return tuple(fact for fact in self.facts if fact.is_located)

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()


def statement_consensus_of(
    observations: tuple[FinancialStatementObservation, ...],
    quorum: int = QUORUM,
) -> FinancialStatementConsensus:
    """
    Derive what these statement readings agree on, concept by concept.

    Deterministic given the observation set, in stored order, with no
    reference anywhere to what any answer says. Raises `ValueError`
    for an empty set, a mixed-document set, or a mixed-statement set —
    each would compare readings of different strings and call the
    difference instability.
    """

    if not observations:
        raise ValueError("A consensus is derived over observations; none were given.")

    keys = {observation.source.key for observation in observations}

    if len(keys) > 1:
        raise ValueError(
            "A consensus is a property of one immutable document, and these "
            f"observations were read from {len(keys)}."
        )

    kinds = {observation.statement for observation in observations}

    if len(kinds) > 1:
        raise ValueError(
            "A consensus is a property of one statement, and these "
            f"observations were read from {len(kinds)}."
        )

    count = len(observations)

    facts = tuple(
        _fact_consensus(concept, observations, count)
        for concept in _addressed(observations)
    )

    return FinancialStatementConsensus(
        symbol=observations[0].symbol,
        statement=observations[0].statement,
        source=observations[0].source,
        observation_count=count,
        quorum=quorum,
        state=(
            ConsensusState.QUORATE
            if count >= quorum
            else ConsensusState.INSUFFICIENT_QUORUM
        ),
        located_among=max(observation.located_among for observation in observations),
        facts=facts,
        reading=_reading(observations, count, quorum),
    )


def _addressed(
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[StatementConcept, ...]:
    """Every concept any observation addressed, in the vocabulary's order.

    Read from the observations rather than from the current vocabulary,
    because a stored reading may predate a concept the vocabulary
    gained since — a consensus must never present a claim no
    observation was asked.
    """

    asked = {fact.concept for observation in observations for fact in observation.facts}

    return tuple(concept for concept in StatementConcept if concept in asked)


def _fact_consensus(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
    count: int,
) -> ConsensusFact:
    """One concept's claim, counted over the observations that addressed it."""

    addressed = tuple(
        fact
        for observation in observations
        if (fact := observation.fact(concept)) is not None
    )

    counted = agreement(
        f"where the statement prints {concept.value}",
        (_answer(fact) for fact in addressed),
    )

    anchor: ReportedFigure | None = None
    row: tuple[ReportedFigure, ...] = ()
    unlocated_because: str | None = None

    if not counted.by_majority or counted.modal is None:
        unlocated_because = (
            f"Where the statement prints this figure is unsettled across "
            f"{counted.readings} observations: {_distribution(counted)}."
        )
    elif counted.modal.stated == NO_FIGURE:
        unlocated_because = _modal_reason(
            tuple(fact.unlocated_because for fact in addressed if not fact.is_located),
            fallback="No observation located a figure for this concept.",
            counted=f"{counted.agreeing} of {counted.readings} observations",
        )
    else:
        anchor, row = _settled(counted.modal.stated, addressed)

    return ConsensusFact(
        concept=concept,
        addressed_in=len(addressed),
        observations=count,
        anchor=anchor,
        row=row,
        unlocated_because=unlocated_because,
        agreement=counted,
    )


def _settled(
    modal: str,
    addressed: tuple[StatementFact, ...],
) -> tuple[ReportedFigure, tuple[ReportedFigure, ...]]:
    """The modal answer's figure, verbatim the first observation's that gave it."""

    for fact in addressed:
        if _answer(fact) == modal and fact.anchor is not None:
            return fact.anchor, fact.row

    # Unreachable while _answer is derived from the facts counted, and
    # checked rather than assumed because a consensus that silently
    # returned nothing here would report a settled claim as absent.
    raise AssertionError("The modal answer matches no observation.")


def _answer(fact: StatementFact) -> str:
    """The comparable form of one reading's answer: the checked anchor."""

    if fact.anchor is None:
        return NO_FIGURE

    return (
        f'"{fact.anchor.label}" = {fact.anchor.printed} at {fact.anchor.cell.stated()}'
    )


def _modal_reason(
    reasons: tuple[str | None, ...],
    fallback: str,
    counted: str,
) -> str:
    """The most common worded reason, chosen by frequency alone."""

    worded = agreement("why", (reason for reason in reasons if reason))

    stated = worded.modal.stated if worded.modal is not None else fallback

    return f"{stated} ({counted}.)"


def _distribution(measured: Agreement) -> str:
    """Every answer and its count, most given first."""

    return "; ".join(f"{answer.given}× {answer.stated}" for answer in measured.answers)


def _reading(
    observations: tuple[FinancialStatementObservation, ...],
    count: int,
    quorum: int,
) -> Provenance:
    """The derivation stated, dated to the newest observation."""

    readers = sorted({observation.reading.source for observation in observations})
    reader = readers[0] if len(readers) == 1 else " and ".join(readers)

    if count >= quorum:
        stated = f"{reader} — consensus of {count} statement readings"
    elif count == 1:
        stated = (
            f"{reader} — 1 statement reading, below the quorum of {quorum}: "
            "a single reading, not a consensus"
        )
    else:
        stated = (
            f"{reader} — {count} statement readings, below the quorum of "
            f"{quorum}: not yet a consensus"
        )

    return Provenance(
        source=stated,
        observed_at=max(
            observation.reading.observed_at for observation in observations
        ),
    )
