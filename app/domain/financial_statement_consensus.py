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

from dataclasses import dataclass, replace

from app.domain.absence_supersession import rule_absences
from app.domain.agreement import Agreement, agreement
from app.domain.assignment_supersession import rule_assignments
from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.financing_cost_refusal import GOVERNED, FactRefusal, refusal_for
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

    #: How many readings recorded an absence for this concept that a
    #: later vocabulary provably invalidated, and which therefore did
    #: not vote.
    #:
    #: Reported rather than subtracted in silence, for the reason
    #: `superseded_count` is: a claim settled by five of five where five
    #: more were withdrawn is a different fact from one settled by five
    #: of five outright, and the reader is owed the difference. The
    #: withdrawn readings remain stored, unaltered, and still say what
    #: they said.
    withdrawn_absences: int = 0

    #: How many readings' positive assignment of a figure to this concept
    #: a later native reading superseded, and which therefore did not
    #: vote.
    #:
    #: The mirror of `withdrawn_absences`, reported on the same terms: a
    #: claim settled with five assignments withdrawn is a different fact
    #: from one settled outright, and the reader is owed the difference.
    #: The withdrawn readings remain stored, unaltered, and still say
    #: what they said — including the figure, which stays historical
    #: evidence.
    withdrawn_assignments: int = 0

    #: A figure the readings settled on and this statement's own
    #: structure disproved for this concept.
    #:
    #: Kept beside the claim rather than turned into an absence: the
    #: filer printed the figure, and reporting *no figure located* about
    #: a document that prints one would be false. The refused figure and
    #: the figure that disproved it both travel here, so a surface can
    #: say what was declined and why without re-deriving anything.
    refused: FactRefusal | None = None

    @property
    def is_located(self) -> bool:
        """Whether the statement was settled to print this figure.

        `False` for a refused figure. The concept is unanswered — which
        is the whole of the refusal — and `refused` is where a reader
        finds out that the answer was declined rather than missing.
        """

        return self.anchor is not None

    @property
    def absent_because(self) -> str | None:
        """Why this concept has no figure, whichever kind of absence it is.

        The one door a consumer should read. A refusal and an absence are
        different facts and are worded apart, but every consumer that
        reports *why there is no number* wants whichever applies, and
        asking for `unlocated_because` alone would report a refusal as
        nothing at all.
        """

        if self.refused is not None:
            return self.refused.because

        return self.unlocated_because


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

    #: How many stored readings an offline audit found the filing itself
    #: refutes, and which this consensus therefore did not count.
    #:
    #: Reported rather than subtracted in silence. A statement that
    #: holds ten readings and counts five is a different fact from one
    #: that only ever had five, and an investor reading "5 of 5" is
    #: owed the difference. They are **superseded, not deleted**: every
    #: one is still in the store, still dated, still attributable.
    superseded_count: int = 0

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

    def supersession_caveat(self) -> str | None:
        """What a reader is owed about readings this consensus did not count.

        Silent where nothing was superseded, because most statements
        have nothing to say here. Where something was, it is said in
        full: how many readings are held, how many were counted, and
        that the rest were withdrawn rather than lost.
        """

        if not self.superseded_count:
            return None

        held = self.observation_count + self.superseded_count

        return (
            f"This filing holds {held} stored readings of this statement "
            f"and {self.observation_count} of them carry authority. An "
            f"offline audit found the filing itself refutes the other "
            f"{self.superseded_count} — the figures were read from cells "
            "the filer heads differently, or from rows it no longer "
            "prints that way. Those readings are superseded rather than "
            "deleted: each is still stored, still dated and still "
            "attributable, and none of them is counted below."
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

    @property
    def refused_facts(self) -> tuple[ConsensusFact, ...]:
        """The concepts whose settled figure this statement's structure refused.

        Beside `located_facts` rather than inside it, and never subtracted
        from anything: a concept the filer printed and this platform
        declined is a third state, and a surface that could only see
        located-or-absent would report it as the filer's silence.
        """

        return tuple(fact for fact in self.facts if fact.refused is not None)

    def refusal_caveat(self) -> str | None:
        """What a reader is owed about a figure that was printed and declined.

        Silent where nothing was refused. Where something was, it names
        the concept and quotes the reason the domain rule worded, because
        the alternative is a blank space that reads as a filer printing
        nothing.
        """

        refused = self.refused_facts

        if not refused:
            return None

        return " ".join(
            f"This platform read a figure for {fact.concept.value} and does "
            f"not count it. {fact.refused.because}"
            for fact in refused
            if fact.refused is not None
        )

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()


def authoritative(
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[FinancialStatementObservation, ...]:
    """The readings that still carry a vote, in the order they were taken.

    The door every caller of `statement_consensus_of` should knock on
    first. A statement whose every reading an audit withdrew is a
    statement this platform holds no *authoritative* account of — which
    is an absence, worded like every other absence, and not an error.
    Deriving a consensus over nothing would be the invented figure
    invariant 1 forbids, and raising at a page would put a maintenance
    action behind a page view.
    """

    return tuple(observation for observation in observations if observation.is_active)


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

    # Authority is counted over the readings that still hold it. A
    # superseded reading is not evidence that disagrees — it is evidence
    # the filing refutes, and counting it would let the document's own
    # contradiction vote. The withdrawn ones are carried as a number so
    # the consensus can say what it did not count, never subtracted in
    # silence, and never deleted: they remain in the store.
    withdrawn = tuple(
        observation for observation in observations if not observation.is_active
    )
    authoritative = tuple(
        observation for observation in observations if observation.is_active
    )

    if not authoritative:
        raise ValueError(
            "Every stored reading of this statement was superseded by an "
            "audit of the filing, so there is no consensus to derive. The "
            "readings are still stored; observing the statement again is "
            "what restores authority."
        )

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

    count = len(authoritative)

    # Two passes, because the second one is cross-concept. Each claim is
    # settled on its own first — content-blind, over the readings
    # entitled to answer it — and only then is the settled set asked
    # whether one statement's structure disproves another's semantic
    # role. A single pass could not do it: the figure that disproves a
    # top line is a different concept's, and it must be settled before
    # it can disprove anything.
    facts = _refused(
        tuple(
            _fact_consensus(concept, authoritative, count)
            for concept in _addressed(authoritative)
        )
    )

    return FinancialStatementConsensus(
        symbol=authoritative[0].symbol,
        statement=authoritative[0].statement,
        source=authoritative[0].source,
        observation_count=count,
        quorum=quorum,
        state=(
            ConsensusState.QUORATE
            if count >= quorum
            else ConsensusState.INSUFFICIENT_QUORUM
        ),
        located_among=max(observation.located_among for observation in authoritative),
        facts=facts,
        reading=_reading(authoritative, count, quorum),
        superseded_count=len(withdrawn),
    )


def _refused(facts: tuple[ConsensusFact, ...]) -> tuple[ConsensusFact, ...]:
    """The settled facts, with any the statement's own structure disproves.

    Every fact is returned, in order, whether or not anything happened to
    it — a refusal is a property carried on the claim, never a claim
    removed from the set.
    """

    established = {
        fact.concept: fact.anchor for fact in facts if fact.anchor is not None
    }

    return tuple(_refuse_one(fact, established) for fact in facts)


def _refuse_one(
    fact: ConsensusFact,
    established: dict[StatementConcept, ReportedFigure],
) -> ConsensusFact:
    """One fact, refused its concept where the structure says it must be.

    The anchor and row move onto the refusal rather than being dropped:
    the concept is unanswered, and the figure the filer printed is still
    reportable. Nothing is written and the observations are untouched —
    this is a property of today's derivation only.
    """

    refusal = refusal_for(fact.concept, fact.anchor, fact.row, established)

    if refusal is not None:
        return replace(fact, anchor=None, row=(), refused=refusal)

    if fact.anchor is None and fact.withdrawn_assignments:
        # The composition BQ27 owes BQ23. Readings that assigned a figure
        # here were withdrawn because the same figure settled under a
        # mutually exclusive concept — so the truthful account of this
        # concept is still the structural refusal of that figure, worded
        # by the same rule that refuses a settled positive, and never the
        # bare absence the surviving voters recorded. One reason, not
        # two: the surviving voters' own sentence says the same thing and
        # yields to it.
        carried = _carried_refusal(fact.concept, established)

        if carried is not None:
            return replace(fact, refused=carried, unlocated_because=None)

    return fact


def _carried_refusal(
    concept: StatementConcept,
    established: dict[StatementConcept, ReportedFigure],
) -> FactRefusal | None:
    """BQ23's refusal of the figure now settled under the sibling concept.

    Fires only where an assignment was withdrawn (the caller's guard) and
    the mutually exclusive sibling's figure is settled in this consensus —
    which is exactly the evidence that withdrew the assignment. A genuine
    tie has no withdrawal and is never masked by this: unsettled stays
    unsettled, worded as such.
    """

    governed = GOVERNED.get(concept)

    if governed is None:
        return None

    marker, requirement = governed

    for sibling, (sibling_marker, sibling_requirement) in GOVERNED.items():
        if (
            sibling is concept
            or sibling_marker is not marker
            or sibling_requirement is requirement
        ):
            continue

        anchor = established.get(sibling)

        if anchor is None:
            continue

        return refusal_for(concept, anchor, (anchor,), established)

    return None


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
    """One concept's claim, counted over the observations that addressed it.

    Counted over those still entitled to answer, which is not always all
    of them, and there are two authority rules rather than one:

    - an **absence** recorded under a vocabulary that provably could not
      have accepted the label a later reading located is a true statement
      about a narrower contract, and letting it vote deadlocks the claim
      it was never in a position to settle (BQ20);
    - a **positive assignment** of a physical fact that a later native
      reading — asked about both concepts — assigned to a mutually
      exclusive concept on the statement's own evidence is a true answer
      to a question the fact no longer takes, and letting it vote turns a
      later, better-qualified assignment into a manufactured tie (BQ27).

    Both withdrawals are concept-local: the same reading's other facts
    are untouched, and its stored bytes are untouched.
    """

    silenced_absences = {
        ruling.position
        for ruling in rule_absences(concept, observations)
        if not ruling.votes
    }
    silenced_assignments = {
        ruling.position
        for ruling in rule_assignments(concept, observations)
        if not ruling.votes
    }

    entitled = tuple(
        observation
        for position, observation in enumerate(observations)
        if position not in silenced_absences and position not in silenced_assignments
    )

    addressed = tuple(
        fact
        for observation in entitled
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
            f"{counted.readings} readings: {_distribution(counted)}."
        )
    elif counted.modal.stated == NO_FIGURE:
        unlocated_because = _modal_reason(
            tuple(fact.unlocated_because for fact in addressed if not fact.is_located),
            fallback="No reading located a figure for this concept.",
            counted=_repeated_readings(
                counted.agreeing, counted.readings, observations
            ),
        )
    else:
        anchor, row = _settled(counted.modal.stated, addressed)

    return ConsensusFact(
        concept=concept,
        addressed_in=len(addressed),
        observations=count,
        withdrawn_absences=len(silenced_absences),
        withdrawn_assignments=len(silenced_assignments),
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


def _repeated_readings(
    agreeing: int,
    readings: int,
    observations: tuple[FinancialStatementObservation, ...],
) -> str:
    """How many readings agreed, and of how many documents.

    The wording this platform is entitled to. *"5 of 5 observations"*
    reads as five independent corroborating sightings; measured, the
    five are five readings of **one** document by one model within
    forty seconds (`PROFITABILITY_EVIDENCE_SEMANTICS.md` §5). Repeated
    readings of one filing are repeated readings, and saying so is the
    difference between counting evidence and counting attempts.

    The document count is not invented: every observation carries the
    `PrimarySource` it was read from, so the distinct count is a fact
    the store already holds. Where more than one document is behind a
    consensus the sentence says that instead — the phrasing narrows to
    what is true rather than asserting a single filing.
    """

    documents = len({observation.source.stated() for observation in observations})

    if documents == 1:
        return f"{agreeing} of {readings} readings of one filing"

    return f"{agreeing} of {readings} readings across {documents} filings"


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
