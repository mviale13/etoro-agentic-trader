"""Derive how a business creates value from its consensus knowledge.

A pure function, like `classify` beside it, and consuming only what the
knowledge layer finished: the consensus, its agreements, and the
archetype the rules concluded. No model, no reading, no provider
metadata, no industry — a business is explained from what its own
filing was shown to establish, or the explanation says what is missing.

The one genuinely new computation here is the contingency analysis.
For every earning claim that is narrow or unsettled, the engine asks
what `classify` would have concluded had the claim settled at each of
its observed answers — the identical rules, run over a consensus that
differs in exactly one settled claim. That is a statement about the
rules, not about the company: no answer is evaluated that no
observation gave, and nothing evaluated is ever stored or promoted.
It is how "not established" gets the explanation it is owed — whether
the gap bears on the conclusion — without ever being compensated for.
"""

from __future__ import annotations

from dataclasses import replace

from app.domain.agreement import Agreement
from app.domain.business_understanding import (
    AlternativeConclusion,
    BusinessUnderstanding,
    Contingency,
    RevenueMechanism,
    SellsThrough,
)
from app.domain.company_archetype import CompanyArchetype
from app.domain.company_knowledge import RevenueModel
from app.domain.knowledge_consensus import (
    CompanyKnowledgeConsensus,
    ConsensusSegment,
    models_of_answer,
)
from app.services.archetype_engine import LEADS, TIED, classify


def understand(consensus: CompanyKnowledgeConsensus) -> BusinessUnderstanding:
    """How this business creates value, from its consensus facts alone."""

    archetype = classify(consensus)

    return BusinessUnderstanding(
        symbol=consensus.symbol,
        source=consensus.stated_source(),
        reading=consensus.reading,
        quorate=consensus.is_quorate,
        observation_count=consensus.observation_count,
        quorum=consensus.quorum,
        engine=_engine(archetype),
        sells=tuple(
            SellsThrough(
                name=segment.name,
                share=segment.revenue_share,
                unmeasured_because=segment.unmeasured_because,
                mechanisms=segment.revenue_models,
                mechanisms_because=(
                    segment.undescribed_because if not segment.revenue_models else None
                ),
                # The filer's stated dependence, worded here — the one
                # layer that knows both the company's name and the
                # settled claim — and carried with its span and width.
                # Decision-neutral by construction: no rule, analyst or
                # selector reads these three fields, and the regression
                # suite holds that door shut.
                depends_stated=(
                    f"{consensus.source.company} states that this business "
                    f"{segment.dependency.statement}"
                    if segment.dependency is not None
                    else None
                ),
                depends_quoted=(
                    segment.dependency.quoted
                    if segment.dependency is not None
                    else None
                ),
                depends_support=(
                    f"stated by the filer; {segment.dependency_agreement.counted()} "
                    "readings agree"
                    if segment.dependency is not None
                    and segment.dependency_agreement is not None
                    else None
                ),
            )
            for segment in consensus.segments
        ),
        mechanisms=_mechanisms(consensus, archetype),
        characteristics=archetype,
        contingencies=_contingencies(consensus, archetype),
        not_established=archetype.missing,
        segments_because=consensus.segments_because,
    )


def _engine(archetype: CompanyArchetype) -> str:
    """The engine in one sentence, worded from the rules' own outcome.

    Single- or multi-engine is the archetype restated in the language
    of value creation, and it is only ever the archetype: a wording
    that consulted anything else would be a second classifier.
    """

    if archetype.candidates:
        return (
            "mechanisms known, weights unmeasured — the ways this business "
            "earns are established and no measured size orders them"
        )

    if not archetype.is_decided:
        # Names what *is* established, because the segments and their
        # sizes are shown directly beneath this line. "Not established"
        # alone read as though the platform knew nothing about the
        # business, while three checked segment shares sat under it.
        return "how it earns is not established — its segments and their sizes are"

    if archetype.is_ranked:
        top = archetype.coverage[0]

        stated = (
            f"single-engine — {top.model.value} runs through "
            f"{(top.covers or 0.0):.0%} of measured revenue"
        )

        if archetype.secondary is not None:
            stated += f", with {archetype.coverage[1].model.value} behind it"

        return stated

    contenders = [
        coverage.model.value
        for coverage in archetype.coverage
        if (coverage.covers or 0.0) >= LEADS
        and abs((coverage.covers or 0.0) - (archetype.coverage[0].covers or 0.0)) < TIED
    ]

    return (
        "multi-engine — "
        + ", ".join(contenders)
        + " lead together, none clear of the others"
    )


def _mechanisms(
    consensus: CompanyKnowledgeConsensus,
    archetype: CompanyArchetype,
) -> tuple[RevenueMechanism, ...]:
    """Each settled way of earning, with the narrowest claim carrying it."""

    return tuple(
        RevenueMechanism(
            model=coverage.model,
            through=coverage.segments,
            coverage=coverage.covers,
            support=_narrowest_carrying(consensus, coverage.model),
        )
        for coverage in archetype.coverage
    )


def _narrowest_carrying(
    consensus: CompanyKnowledgeConsensus,
    model: RevenueModel,
) -> Agreement:
    """The weakest earning agreement among segments settled on this model."""

    carrying = [
        segment.earning_agreement
        for segment in consensus.segments
        if model in segment.revenue_models
    ]

    return min(carrying, key=lambda agreement: agreement.stability or 0.0)


def _contingencies(
    consensus: CompanyKnowledgeConsensus,
    archetype: CompanyArchetype,
) -> tuple[Contingency, ...]:
    """Every narrow or unsettled earning claim, evaluated at its answers.

    Only earning claims in this first version: every size in the
    measured corpus settled unanimously, so probing sizes would be
    machinery without a population. The mechanism generalises when a
    disagreeing size appears.
    """

    found: list[Contingency] = []

    for segment in consensus.segments:
        earning = segment.earning_agreement

        if earning.settled or earning.modal is None:
            continue

        alternatives = []

        for answer in earning.answers:
            concluded = classify(
                _with_settled_earning(consensus, segment, answer.stated)
            )

            alternatives.append(
                AlternativeConclusion(
                    answer=answer.stated,
                    given=answer.given,
                    concludes=concluded.stated,
                    primary=concluded.primary,
                    secondary=concluded.secondary,
                )
            )

        found.append(
            Contingency(
                claim=f"how {segment.name!r} earns",
                agreement=earning,
                as_it_stands=archetype.stated,
                consumed=bool(segment.revenue_models),
                alternatives=tuple(alternatives),
            )
        )

    return tuple(found)


def _with_settled_earning(
    consensus: CompanyKnowledgeConsensus,
    segment: ConsensusSegment,
    answer: str,
) -> CompanyKnowledgeConsensus:
    """The same consensus with one claim settled at one observed answer.

    The hypothetical exists only inside the contingency evaluation. It
    is never stored, never served, and built only from an answer some
    observation actually gave — walking the canonical answer format
    back to models is a round trip, not an interpretation.
    """

    return replace(
        consensus,
        segments=tuple(
            replace(
                existing,
                revenue_models=models_of_answer(answer),
                undescribed_because=None,
            )
            if existing.name == segment.name
            else existing
            for existing in consensus.segments
        ),
    )
