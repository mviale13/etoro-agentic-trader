"""What repeated observations of one document agree the company is.

The knowledge layer's second concept, kept strictly apart from its
first. A `CompanyKnowledgeObservation` is one reading — admissible,
grounded, and one draw from a distribution the calibration measured. A
`CompanyKnowledgeConsensus` is what a set of independent observations
agree on, claim by claim, with how far they agree carried everywhere.

The distinction in one line: identity, grounding and applicability are
**admissibility** boundaries, deciding whether an observation may enter
trusted knowledge at all; consensus is a **stability** boundary,
deciding whether admissible observations are reproducible enough to
support interpretation. Consensus cannot rescue an inadmissible
observation, and an unsettled consensus does not mean the observations
are untrue — it means the platform cannot yet claim representativeness.

The rule, and what makes it safe:

- **Content-blind strict majority, per claim, over the observations
  that addressed the claim.** The rule counts who agreed and never
  reads what they agreed on, so a worded absence wins exactly as a
  measured value does. What makes that safe is that verification
  already removed falsehood per observation — what is being adjudicated
  is representativeness among grounded answers, not truth.
- **Consensus selects; it never synthesizes.** Every settled value is,
  verbatim, a value some observation gave. Collections are compared
  atomically with order normalized where order carries no meaning; a
  per-element winner could be a set no observation asserted, which
  nothing could walk backward to a reading that said it.
- **Ties and pluralities settle nothing.** An unsettled claim is an
  absence carrying its distribution, through the same absence fields
  every consumer already reads.
- **Derived, never stored.** A consensus is recomputed from the stored
  observations every time it is asked for, so a changed rule leaves no
  stale conclusions and there is no second place for an answer to be
  true.

Four words, kept apart because conflating any two of them overstates
what the platform knows:

- **Quorum** — enough observations exist. A property of the set's size
  and nothing else.
- **Consensus** — one observed value carries a strict majority. A
  property of these answers.
- **Agreement strength** — the winning count and the complete
  distribution. 3/5 and 5/5 are both consensus and different findings,
  and no surface may collapse them.
- **Robustness** — whether that consensus would survive additional
  observations. **Not established, for anything.** Measured on NVIDIA:
  a claim that leaned one way over ten calibration readings settled the
  other way over a five-observation quorum, correctly, both times.
  "Settled" therefore means a majority among these observations — it
  never means unlikely to change, and a downstream consumer that
  treated every majority as equally stable would be reading a forecast
  nobody made.

Nothing here is a probability. "3 of 5 observations" counts something
that happened; the chance a sixth agrees was not measured and is not
stated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.agreement import Agreement, agreement
from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    EconomicRelationship,
    RevenueModel,
)
from app.domain.primary_source import PrimarySource
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import MeasuredShare

#: How many observations of one document the platform wants before it
#: calls anything settled. Reasoned rather than measured, and odd on
#: purpose so a bare strict majority exists: small enough to control
#: cost, large enough that 3 of 5 and 5 of 5 are visibly different
#: findings — and they are never allowed to look the same downstream.
QUORUM = 5


class ConsensusState(StrEnum):
    """Whether enough observations exist for consensus to mean anything.

    Below quorum the platform keeps operating — refusing to serve
    knowledge it holds would discard verified evidence — but nothing is
    called settled, and every consumer is told it is reading one or few
    observations rather than a consensus. The defect this prevents was
    never a small N; it was an N of one presented without its width.
    """

    QUORATE = "quorate"
    INSUFFICIENT_QUORUM = "insufficient_quorum"


@dataclass(frozen=True, slots=True)
class ConsensusSegment:
    """One segment, as the observations that named it agree it is.

    Field names deliberately mirror `BusinessSegment`: a settled claim
    reads exactly as an observed one does, an unsettled claim reads as
    an absence whose reason carries the distribution, and the rules
    downstream consume either without knowing which they were given.
    Beside each claim sits its `Agreement`, so 3/5 and 5/5 never look
    identical to a surface.
    """

    name: str

    #: How many observations named this segment, of how many were taken.
    #: Per-claim agreement below is counted over `named_in` — the
    #: observations that never mentioned the segment said nothing about
    #: its size either, and counting silence as dissent would report one
    #: instability twice.
    named_in: int
    observations: int

    #: The settled size — verbatim the `MeasuredShare` of an observation
    #: that gave the modal answer — or None with the reason worded.
    revenue: MeasuredShare | None
    unmeasured_because: str | None
    size_agreement: Agreement

    #: The settled ways of earning, order-normalized, atomically one
    #: observation's answer. Empty where unsettled or settled-absent,
    #: with the reason in `undescribed_because`.
    revenue_models: tuple[RevenueModel, ...]
    earning_agreement: Agreement

    #: Whether the filing was shown to describe this segment. None where
    #: the observations could not agree.
    described: bool | None
    undescribed_because: str | None
    described_agreement: Agreement

    #: The spans the observations cited. Deliberately never settled: a
    #: canonical span would mistake stable wording for stable meaning —
    #: ten readings quoted one Caterpillar sentence eight ways and meant
    #: the same thing. The claim settles; the evidence spans stay
    #: attached to the observations that produced them, and this is
    #: their distribution.
    span_agreement: Agreement

    #: The settled filer-stated economic dependence of this business on
    #: another, atomically one observation's answer — or None, which is
    #: the ordinary state and an evidence state, never a finding of
    #: independence. Settles exactly as every claim here does: by
    #: majority over the observations that named the segment.
    dependency: EconomicRelationship | None = None
    dependency_agreement: Agreement | None = None

    @property
    def revenue_share(self) -> float | None:
        """The settled share of revenue, 0.0 to 1.0, or None."""

        return self.revenue.share if self.revenue is not None else None


@dataclass(frozen=True, slots=True)
class CompanyKnowledgeConsensus:
    """What this platform treats as knowledge of a business.

    Derived from stored observations on every read and never stored
    itself. The shape mirrors an observation closely enough that the
    archetype rules consume it unchanged — which is the point: the
    decision path reads consensus only, and an observation reaches a
    decision through the consensus function or not at all.
    """

    symbol: str

    #: The company's own self-description — one observation's wording,
    #: chosen content-blind (the earliest stored), because this claim's
    #: variance is not yet calibrated and putting it through a rule
    #: whose behaviour on it is unmeasured would be assuming the answer.
    #: Surfaces label it as one observation's wording.
    description: str

    source: PrimarySource

    #: How many observations this consensus is derived over, against
    #: what the platform wants.
    observation_count: int
    quorum: int
    state: ConsensusState

    #: How far the observations agreed on which segments exist at all.
    #: The frame every per-segment claim lives in: if this is unsettled,
    #: there are no consensus segments, and the reason below says so
    #: with the distribution.
    identity: Agreement
    segments: tuple[ConsensusSegment, ...]
    segments_because: str | None

    #: The derivation, stated: which reader produced the observations,
    #: how many there are, and whether that reaches the quorum. Dated to
    #: the newest observation, because consensus is exactly as current
    #: as the last reading in it.
    reading: Provenance

    @property
    def is_quorate(self) -> bool:
        return self.state is ConsensusState.QUORATE

    @property
    def has_segments(self) -> bool:
        """Whether consensus holds any segments at all."""

        return bool(self.segments)

    @property
    def measured_share(self) -> float:
        """How much of revenue the settled sizes account for."""

        return sum(
            segment.revenue_share
            for segment in self.segments
            if segment.revenue_share is not None
        )

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()


def consensus_of(
    observations: tuple[CompanyKnowledgeObservation, ...],
    quorum: int = QUORUM,
) -> CompanyKnowledgeConsensus:
    """
    Derive what these observations agree on, claim by claim.

    Deterministic given the observation set: same observations in, same
    consensus out, with no reference anywhere to what any answer says.
    The order of `observations` is their stored (append) order, which is
    what makes "the first observation that gave the modal answer" a
    deterministic choice rather than a preference.

    Raises `ValueError` for an empty set or a mixed one — a consensus
    over nothing means nothing, and a consensus across two different
    documents would compare readings of different strings and call the
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

    count = len(observations)

    identity = agreement(
        "which segments the document names",
        (_identity(observation) for observation in observations),
    )

    settled_frame = identity.by_majority

    segments: tuple[ConsensusSegment, ...] = ()
    segments_because: str | None = None

    if settled_frame and identity.modal is not None:
        segments = tuple(
            _segment_consensus(name, observations, count)
            for name in _modal_names(observations, identity.modal.stated)
        )
    else:
        segments_because = (
            f"Which segments this document names is unsettled across {count} "
            f"observations: {_distribution(identity)}."
        )

    return CompanyKnowledgeConsensus(
        symbol=observations[0].symbol,
        description=observations[0].description,
        source=observations[0].source,
        observation_count=count,
        quorum=quorum,
        state=(
            ConsensusState.QUORATE
            if count >= quorum
            else ConsensusState.INSUFFICIENT_QUORUM
        ),
        identity=identity,
        segments=segments,
        segments_because=segments_because,
        reading=_reading(observations, count, quorum),
    )


# ── each claim, counted ─────────────────────────────────────────────


def _segment_consensus(
    name: str,
    observations: tuple[CompanyKnowledgeObservation, ...],
    count: int,
) -> ConsensusSegment:
    """One segment's claims, counted over the observations that named it."""

    named = tuple(
        segment
        for observation in observations
        for segment in observation.segments
        if segment.name == name
    )

    size = agreement("its size", (_size(segment) for segment in named))
    earning = agreement("how it earns", (_earning(segment) for segment in named))
    described = agreement(
        "whether the filing was shown to describe it",
        (_described(segment) for segment in named),
    )
    spans = agreement(
        "which span was cited for that",
        (_span(segment) for segment in named),
    )

    revenue, unmeasured_because = _settled_size(size, named)
    models, described_settled, undescribed_because = _settled_earning(
        earning, described, named
    )

    # Counted over the readings that were *asked* the question: an
    # observation taken before the relationship question existed holds
    # an empty tuple for a different reason than one that was asked and
    # found nothing, and counting it as a "no" would let old readings
    # outvote the filer's own stated dependence.
    dependency_claims = tuple(
        _dependency(observation, name)
        for observation in observations
        if observation.relationships_asked
        and any(segment.name == name for segment in observation.segments)
    )
    dependence = agreement(
        "whether the filing states its economics are driven by another business",
        (_dependency_answer(claim) for claim in dependency_claims),
    )
    dependency = _settled_dependency(dependence, dependency_claims)

    return ConsensusSegment(
        name=name,
        named_in=len(named),
        observations=count,
        revenue=revenue,
        unmeasured_because=unmeasured_because,
        size_agreement=size,
        revenue_models=models,
        earning_agreement=earning,
        described=described_settled,
        undescribed_because=undescribed_because,
        described_agreement=described,
        span_agreement=spans,
        dependency=dependency,
        dependency_agreement=dependence,
    )


def _settled_size(
    size: Agreement,
    named: tuple[BusinessSegment, ...],
) -> tuple[MeasuredShare | None, str | None]:
    """The modal size where a majority cited it, else a worded absence.

    A settled value is verbatim an observed one: the share returned is
    the `MeasuredShare` of the first observation whose answer matches
    the modal answer, evidence and all.
    """

    if not size.by_majority or size.modal is None:
        return None, (
            f"The size of this segment is unsettled across {size.readings} "
            f"observations: {_distribution(size)}."
        )

    if size.modal.stated == NO_SIZE:
        return None, _modal_reason(
            tuple(
                segment.unmeasured_because
                for segment in named
                if segment.revenue is None
            ),
            fallback="No observation located a figure for this segment.",
            counted=f"{size.agreeing} of {size.readings} observations",
        )

    for segment in named:
        if _size(segment) == size.modal.stated and segment.revenue is not None:
            return segment.revenue, None

    # Unreachable while _size is derived from the segments counted, and
    # checked rather than assumed because a consensus that silently
    # returned nothing here would report a settled claim as absent.
    raise AssertionError("The modal size answer matches no observation.")


def _settled_earning(
    earning: Agreement,
    described: Agreement,
    named: tuple[BusinessSegment, ...],
) -> tuple[tuple[RevenueModel, ...], bool | None, str | None]:
    """The settled ways of earning, with the description claim beside it.

    Returns (models, described, undescribed_because). The reason field
    serves whichever claim failed first: an unsettled description, a
    settled absence of one, or settled description whose ways of
    earning would not settle.
    """

    if not described.by_majority or described.modal is None:
        return (
            (),
            None,
            (
                f"Whether the filing describes this segment is unsettled across "
                f"{described.readings} observations: {_distribution(described)}."
            ),
        )

    if described.modal.stated == NOT_DESCRIBED:
        return (
            (),
            False,
            _modal_reason(
                tuple(
                    segment.undescribed_because
                    for segment in named
                    if segment.description is None
                ),
                fallback="No observation established a description.",
                counted=f"{described.agreeing} of {described.readings} observations",
            ),
        )

    if not earning.by_majority or earning.modal is None:
        return (
            (),
            True,
            (
                f"Which ways this segment earns is unsettled across "
                f"{earning.readings} observations: {_distribution(earning)}."
            ),
        )

    if earning.modal.stated == NO_EARNING:
        # Described, and the description names no way of earning — the
        # engine's own default wording covers it.
        return (), True, None

    for segment in named:
        if _earning(segment) == earning.modal.stated:
            return tuple(sorted(segment.revenue_models)), True, None

    raise AssertionError("The modal earning answer matches no observation.")


# ── answers, as compared ────────────────────────────────────────────
#
# The comparable form of each claim. Collections are order-normalized —
# a filing's segments and a description's ways of earning carry no
# meaning in their order — and otherwise verbatim.

NO_SIZE = "no size measured"
NOT_DESCRIBED = "not described"
NO_EARNING = "no way of earning established"
NO_DEPENDENCY = "no dependence stated"


def _dependency(
    observation: CompanyKnowledgeObservation,
    name: str,
) -> EconomicRelationship | None:
    """This observation's dependence claim for this segment, if any."""

    for relationship in observation.relationships:
        if relationship.dependent == name:
            return relationship

    return None


def _dependency_answer(claim: EconomicRelationship | None) -> str:
    """The comparable form of a dependence claim.

    Compared on the statement rather than the span, for the same reason
    descriptions settle on the claim while spans stay a distribution:
    five readings of one sentence word its meaning nearly alike and
    quote it many ways.
    """

    return claim.statement if claim is not None else NO_DEPENDENCY


def _settled_dependency(
    dependence: Agreement,
    claims: tuple[EconomicRelationship | None, ...],
) -> EconomicRelationship | None:
    """The settled dependence, atomically one observation's answer.

    None wherever the majority did not state one — including where the
    readings could not agree, which renders as nothing rather than as a
    hedge, because an unsettled relationship claim must not reach a
    surface half-said.
    """

    if not dependence.by_majority or dependence.modal is None:
        return None

    if dependence.modal.stated == NO_DEPENDENCY:
        return None

    for claim in claims:
        if claim is not None and claim.statement == dependence.modal.stated:
            return claim

    raise AssertionError("The modal dependence answer matches no observation.")


def _identity(observation: CompanyKnowledgeObservation) -> str:
    if not observation.segments:
        return "no segments"

    return ", ".join(sorted(segment.name for segment in observation.segments))


def _size(segment: BusinessSegment) -> str:
    if segment.revenue is None:
        return NO_SIZE

    return (
        f"{segment.revenue.share:.0%} "
        f"({segment.revenue.numerator.cell.stated()} of "
        f"{segment.revenue.denominator.cell.stated()})"
    )


def _earning(segment: BusinessSegment) -> str:
    if not segment.revenue_models:
        return NO_EARNING

    return ", ".join(sorted(model.value for model in segment.revenue_models))


def models_of_answer(stated: str) -> tuple[RevenueModel, ...]:
    """The ways of earning an observed earning answer states.

    The inverse of `_earning`, kept beside it because this module owns
    the format. What it exists for is contingency analysis: Business
    Understanding evaluates what the rules would conclude had a narrow
    or unsettled claim settled at one of its *observed* answers — and an
    observed answer is a string in exactly this format, so walking it
    back to models is a round trip, never an interpretation. An answer
    this cannot parse is an error, not a guess: the only strings that
    reach it are ones `_earning` produced.
    """

    if stated == NO_EARNING:
        return ()

    return tuple(RevenueModel(value) for value in stated.split(", "))


def _described(segment: BusinessSegment) -> str:
    return "described" if segment.description is not None else NOT_DESCRIBED


def _span(segment: BusinessSegment) -> str:
    if segment.description is None:
        return "no description established"

    return f'"{segment.description.quoted}"'


# ── wording ─────────────────────────────────────────────────────────


def _modal_names(
    observations: tuple[CompanyKnowledgeObservation, ...],
    modal: str,
) -> tuple[str, ...]:
    """The segment names of the modal identity, in an observed order.

    The modal identity string is sorted for comparison; the names are
    taken back from the first observation that gave that answer, so the
    consensus presents segments in an order a reading actually used.
    """

    for observation in observations:
        if _identity(observation) == modal:
            return tuple(segment.name for segment in observation.segments)

    return ()


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
    observations: tuple[CompanyKnowledgeObservation, ...],
    count: int,
    quorum: int,
) -> Provenance:
    """The derivation stated, dated to the newest observation."""

    readers = sorted({observation.reading.source for observation in observations})
    reader = readers[0] if len(readers) == 1 else " and ".join(readers)

    if count >= quorum:
        stated = f"{reader} — consensus of {count} observations"
    elif count == 1:
        stated = (
            f"{reader} — 1 observation, below the quorum of {quorum}: "
            "a single reading, not a consensus"
        )
    else:
        stated = (
            f"{reader} — {count} observations, below the quorum of {quorum}: "
            "not yet a consensus"
        )

    return Provenance(
        source=stated,
        observed_at=max(
            observation.reading.observed_at for observation in observations
        ),
    )
