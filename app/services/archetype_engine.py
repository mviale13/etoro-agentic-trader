"""Decide what kind of business a company is, from its own filing.

Deterministic, and that word is doing real work. Every input is a fact
the knowledge layer proved against a document — a segment the filing
named, a size divided out of two cells this platform read for itself, a
way of earning carried by a description shown to be about that segment.
Every step below is arithmetic over those facts. No model is asked, and
none could be: a model asked "what kind of business is this?" answers
from what it knows about the company, and what it knows about the
company is exactly the outside taxonomy this layer replaces.

**Coverage, not revenue.** The one arithmetic idea here. A filing states
what each segment earned and which ways of earning it uses; it does not
split a segment's revenue between them. So a way of earning is weighted
by the size of the segments that use it — "segments worth 90% of
measured revenue license as well as manufacture" — and never by a
revenue figure nobody printed. Coverages therefore overlap and do not
sum to 1. Disney's Entertainment segment earns five ways and contributes
all 45% of itself to each.

**The rules refuse to read names.** Volkswagen reports a segment called
*Finanzdienstleistungen* worth 19% of revenue, and nothing here concludes
that Volkswagen has a lending business, because the filing's descriptions
of its segments were not established and a segment's name is not a
statement of what it does. Reading meaning out of the label would be a
taxonomy again — this platform's own, in German — which is the thing
this engine exists to stop doing.
"""

from __future__ import annotations

from collections import defaultdict

from app.domain.agreement import Agreement
from app.domain.company_archetype import (
    ARCHETYPE_OF,
    Archetype,
    CompanyArchetype,
    Dimension,
    ModelCoverage,
    Ruling,
    Unestablished,
)
from app.domain.company_knowledge import RevenueModel
from app.domain.knowledge_consensus import (
    CompanyKnowledgeConsensus,
    ConsensusSegment,
)

#: How much of a company must be shown to earn *some* particular way
#: before any archetype is decided for it.
#:
#: Reasoned rather than measured, and said plainly because the
#: difference matters: `NEARBY` in the prose module sits inside a gap
#: between two populations that were actually observed, and there is no
#: such gap here yet. Half is the point at which a conclusion drawn from
#: the explained part would be outvoted by the part that is not, so a
#: platform that draws it anyway is generalising from a minority of the
#: business without saying so.
#:
#: What would change it: a population of filings where archetypes
#: reached at some other coverage were checked against the businesses
#: and found right or wrong. Until that exists, this is a stated
#: judgement, not a finding.
ENOUGH_EXPLAINED = 0.5

#: How widespread a way of earning must be before it names the company.
#:
#: Same reasoning, applied to a different quantity. A way of earning that
#: runs through less than half of measured revenue describes a minority
#: of the business, and a company named after it would be named after its
#: smaller part.
LEADS = 0.5

#: How far apart two coverages must be to be ordered at all.
#:
#: The mix is arithmetic over segment sizes, and several ways of earning
#: routinely ride on the same segments — Disney's licensing, transaction
#: and services coverages are identical to the digit because all three
#: run through all three segments. A gap narrower than this says which
#: segments happen to carry a model, not which way of earning leads a
#: business, and ordering on it would manufacture a finding out of
#: rounding.
TIED = 0.05


def classify(knowledge: CompanyKnowledgeConsensus) -> CompanyArchetype:
    """
    What kind of business this is, or why that could not be decided.

    Four outcomes, and they are different claims about the world:
    ranked, diversified, unranked and undecided. Which one is reached
    depends on which dimensions of the knowledge survived — size and
    description fail independently, so a company can be fully measured
    and wholly unexplained, or fully explained and wholly unmeasured.
    Both happen; both are in the population these rules were written
    against.

    The rules consume consensus, never a single observation, and an
    unsettled claim reaches them as an absence carrying its
    distribution — so a rule that needs it declines with the
    disagreement worded, rather than deciding from whichever answer a
    single reading happened to give.
    """

    if knowledge.segments_because is not None:
        # The observations could not agree what segments exist, so
        # every per-segment rule is starved of its frame. Refused
        # outright with the distribution, never adjudicated here: which
        # reading to prefer is exactly the question the rules must not
        # answer.
        return _undecided(
            knowledge,
            missing=(),
            coverage=(),
            explained=0.0,
            basis=(
                Ruling(
                    rule="segments-unsettled",
                    read=(
                        f"{knowledge.observation_count} observations that "
                        "do not agree which segments this document names"
                    ),
                    concluded=(
                        "No archetype. Until the observations agree what "
                        "the parts of this business are, no rule about "
                        "the parts can run."
                    ),
                ),
            ),
            because=knowledge.segments_because,
        )

    missing = _unestablished(knowledge.segments)
    earning = tuple(segment for segment in knowledge.segments if segment.revenue_models)

    if not earning:
        return _undecided(
            knowledge,
            missing=missing,
            coverage=(),
            explained=0.0,
            basis=(
                Ruling(
                    rule="nothing-explained",
                    read=(
                        f"{len(knowledge.segments)} segment(s), none of which the "
                        "filing was shown to describe a way of earning for"
                    ),
                    concluded=(
                        "No archetype. What this company earns from is not "
                        "established, whatever its segments are called."
                    ),
                ),
            ),
            because=(
                "No segment of this business was shown to earn any particular "
                "way, so there is nothing to classify it on. Its segments and "
                "their sizes are unaffected."
            ),
        )

    measurable = tuple(segment for segment in earning if segment.revenue_share)
    explained = sum(segment.revenue_share or 0.0 for segment in measurable)

    if not measurable:
        return _unranked(knowledge, earning, missing)

    if explained < ENOUGH_EXPLAINED:
        return _undecided(
            knowledge,
            missing=missing,
            coverage=_coverage(measurable),
            explained=explained,
            basis=(
                Ruling(
                    rule="too-little-explained",
                    read=(
                        f"{_pct(explained)} of revenue is both measured and "
                        f"shown to earn some particular way, against a floor "
                        f"of {_pct(ENOUGH_EXPLAINED)}"
                    ),
                    concluded=(
                        "No archetype. An archetype decided here would "
                        "describe a minority of the business."
                    ),
                ),
            ),
            because=(
                f"Only {_pct(explained)} of this company's revenue is both "
                "measured and shown to earn a particular way. Naming the "
                "business after that would generalise from its smaller part."
            ),
        )

    return _ranked(knowledge, measurable, missing, explained)


# ── the regimes ─────────────────────────────────────────────────────


def _ranked(
    knowledge: CompanyKnowledgeConsensus,
    measurable: tuple[ConsensusSegment, ...],
    missing: tuple[Unestablished, ...],
    explained: float,
) -> CompanyArchetype:
    """Sizes and ways of earning both established: order them."""

    covers = _coverage(measurable)
    leading = [coverage for coverage in covers if (coverage.covers or 0.0) >= LEADS]

    read = ", ".join(
        f"{coverage.model.value} {_pct(coverage.covers or 0.0)}" for coverage in covers
    )

    if not leading:
        return _diversified(
            knowledge,
            coverage=covers,
            missing=missing,
            explained=explained,
            rule="no-way-of-earning-leads",
            read=read,
            concluded=(
                "Diversified. No way of earning runs through as much as "
                f"{_pct(LEADS)} of the segment revenue total."
            ),
        )

    top = leading[0]
    contenders = [
        coverage
        for coverage in leading
        if abs((coverage.covers or 0.0) - (top.covers or 0.0)) < TIED
    ]

    if len(contenders) > 1:
        return _diversified(
            knowledge,
            coverage=covers,
            missing=missing,
            explained=explained,
            rule="no-single-way-of-earning-leads",
            read=read,
            concluded=(
                "Diversified. "
                + ", ".join(coverage.model.value for coverage in contenders)
                + " lead together, within "
                + f"{_pct(TIED)} of one another."
            ),
        )

    narrowest, rests_on = _rests_on(knowledge, measurable, sizes_consumed=True)

    return CompanyArchetype(
        symbol=knowledge.symbol,
        primary=ARCHETYPE_OF[top.model],
        secondary=_secondary(leading),
        candidates=(),
        coverage=covers,
        measured=knowledge.measured_share,
        explained=explained,
        missing=missing,
        basis=(
            Ruling(
                rule="one-way-of-earning-leads",
                read=read,
                concluded=(
                    f"{ARCHETYPE_OF[top.model].stated}. {top.model.value} runs "
                    f"through {_pct(top.covers or 0.0)} of the segment revenue "
                    f"total, "
                    f"more than {_pct(TIED)} clear of anything else."
                ),
            ),
        ),
        undecided_because=None,
        source=knowledge.stated_source(),
        reading=knowledge.reading,
        quorate=knowledge.is_quorate,
        narrowest=narrowest,
        rests_on=rests_on,
    )


def _unranked(
    knowledge: CompanyKnowledgeConsensus,
    earning: tuple[ConsensusSegment, ...],
    missing: tuple[Unestablished, ...],
) -> CompanyArchetype:
    """
    The ways of earning are known and no size was measured.

    Candidates, and no primary. Ordering them would need a weight, the
    only honest weight is a measured size, and there is none — counting
    segments instead would treat a company's largest and smallest parts
    as equals, which is the estimate this platform does not make.
    """

    covers = _coverage(earning)
    candidates = tuple(ARCHETYPE_OF[coverage.model] for coverage in covers)

    narrowest, rests_on = _rests_on(knowledge, earning, sizes_consumed=False)

    return CompanyArchetype(
        symbol=knowledge.symbol,
        primary=None,
        secondary=None,
        candidates=candidates,
        coverage=covers,
        measured=knowledge.measured_share,
        explained=0.0,
        missing=missing,
        basis=(
            Ruling(
                rule="nothing-measured",
                read=(
                    f"{len(earning)} segment(s) shown to earn by "
                    + ", ".join(coverage.model.value for coverage in covers)
                    + ", and no segment size proven against a table"
                ),
                concluded=(
                    "The ways this business earns are known and cannot be "
                    "ordered. Counting segments would weigh its largest and "
                    "smallest parts equally."
                ),
            ),
        ),
        undecided_because=(
            "This platform knows how this business earns but not how much of "
            "it earns each way: no segment size was proven against a table in "
            "the filing. What it might be is stated instead, unranked."
        ),
        source=knowledge.stated_source(),
        reading=knowledge.reading,
        quorate=knowledge.is_quorate,
        narrowest=narrowest,
        rests_on=rests_on,
    )


def _diversified(
    knowledge: CompanyKnowledgeConsensus,
    *,
    coverage: tuple[ModelCoverage, ...],
    missing: tuple[Unestablished, ...],
    explained: float,
    rule: str,
    read: str,
    concluded: str,
) -> CompanyArchetype:
    """Measured, explained, and genuinely without a leading way to earn."""

    narrowest, rests_on = _rests_on(
        knowledge,
        tuple(segment for segment in knowledge.segments if segment.revenue_models),
        sizes_consumed=True,
    )

    return CompanyArchetype(
        symbol=knowledge.symbol,
        primary=Archetype.DIVERSIFIED,
        secondary=None,
        candidates=(),
        coverage=coverage,
        measured=knowledge.measured_share,
        explained=explained,
        missing=missing,
        basis=(Ruling(rule=rule, read=read, concluded=concluded),),
        undecided_because=None,
        source=knowledge.stated_source(),
        reading=knowledge.reading,
        quorate=knowledge.is_quorate,
        narrowest=narrowest,
        rests_on=rests_on,
    )


def _undecided(
    knowledge: CompanyKnowledgeConsensus,
    *,
    missing: tuple[Unestablished, ...],
    coverage: tuple[ModelCoverage, ...],
    explained: float,
    basis: tuple[Ruling, ...],
    because: str,
) -> CompanyArchetype:
    """No archetype, with the reason and the evidence that fell short."""

    # An undecided archetype consumed no claim all the way to a
    # conclusion, so it asserts no basis — its reasons carry the
    # distributions instead.
    return CompanyArchetype(
        symbol=knowledge.symbol,
        primary=None,
        secondary=None,
        candidates=(),
        coverage=coverage,
        measured=knowledge.measured_share,
        explained=explained,
        missing=missing,
        basis=basis,
        undecided_because=because,
        source=knowledge.stated_source(),
        reading=knowledge.reading,
        quorate=knowledge.is_quorate,
    )


# ── what a conclusion rests on ──────────────────────────────────────


def _rests_on(
    knowledge: CompanyKnowledgeConsensus,
    used: tuple[ConsensusSegment, ...],
    sizes_consumed: bool,
) -> tuple[Agreement | None, str | None]:
    """The weakest agreement among the claims the rules consumed, worded.

    A conclusion is exactly as firm as the narrowest claim beneath it.
    Which claims count is which claims were *used*: identity always,
    each used segment's ways of earning always, and its size only in
    the regimes that weighed sizes — an unranked outcome consumed no
    size, and charging it with one would report a width nothing rested
    on.

    Robustness is deliberately not asserted. A narrow majority is a
    fact about these observations; whether it survives further ones has
    not been established for anything, and the wording stops at the
    count.
    """

    consumed: list[tuple[str, Agreement]] = [
        ("which segments the document names", knowledge.identity)
    ]

    for segment in used:
        consumed.append((f"how {segment.name!r} earns", segment.earning_agreement))

        if sizes_consumed:
            consumed.append((f"the size of {segment.name!r}", segment.size_agreement))

    answered = [
        (about, agreement) for about, agreement in consumed if agreement.readings > 0
    ]

    if not answered:
        return None, None

    about, narrowest = min(
        answered,
        key=lambda claim: claim[1].stability or 0.0,
    )

    if not knowledge.is_quorate:
        counted = (
            "1 observation"
            if knowledge.observation_count == 1
            else f"{knowledge.observation_count} observations"
        )

        return narrowest, (
            f"{counted}, below the quorum of {knowledge.quorum} — not a "
            "consensus, and nothing decided from it is authoritative."
        )

    if narrowest.settled:
        return narrowest, (
            f"a consensus of {knowledge.observation_count} observations, "
            f"unanimous on every claim consumed."
        )

    return narrowest, (
        f"a consensus of {knowledge.observation_count} observations; the "
        f"narrowest claim beneath it is {narrowest.stated_majority()} — "
        f"{about}. Whether that majority would survive further observations "
        "has not been established."
    )


# ── the arithmetic ──────────────────────────────────────────────────


def _coverage(segments: tuple[ConsensusSegment, ...]) -> tuple[ModelCoverage, ...]:
    """
    How much of the business earns each way, widest first.

    Where no segment carries a measured size the coverages are absent
    rather than zero: nothing was weighed, which is a different fact
    from weighing nothing.
    """

    weight: dict[RevenueModel, float] = defaultdict(float)
    naming: dict[RevenueModel, list[str]] = defaultdict(list)
    measured = any(segment.revenue_share for segment in segments)

    for segment in segments:
        for model in segment.revenue_models:
            weight[model] += segment.revenue_share or 0.0
            naming[model].append(segment.name)

    coverages = tuple(
        ModelCoverage(
            model=model,
            covers=weight[model] if measured else None,
            segments=tuple(naming[model]),
        )
        for model in weight
    )

    # Deterministic order, widest first. The model's own value breaks
    # ties so that two runs over one filing cannot disagree.
    return tuple(sorted(coverages, key=lambda c: (-(c.covers or 0.0), c.model.value)))


def _secondary(leading: list[ModelCoverage]) -> Archetype | None:
    """
    The next-widest way of earning, where one stands apart.

    Absent where the runners-up are tied, and that absence is honest
    rather than tidy: NVIDIA licenses and provides services across
    exactly the same 90% of revenue, so naming either one the secondary
    would pick between them on nothing.
    """

    if len(leading) < 2:
        return None

    runner_up = leading[1]

    if abs((leading[0].covers or 0.0) - (runner_up.covers or 0.0)) < TIED:
        return None

    if (
        len(leading) > 2
        and abs((runner_up.covers or 0.0) - (leading[2].covers or 0.0)) < TIED
    ):
        return None

    return ARCHETYPE_OF[runner_up.model]


def _unestablished(
    segments: tuple[ConsensusSegment, ...],
) -> tuple[Unestablished, ...]:
    """What the rules needed about each segment and did not have."""

    gaps: list[Unestablished] = []

    for segment in segments:
        if segment.revenue is None:
            gaps.append(
                Unestablished(
                    segment=segment.name,
                    dimension=Dimension.SIZE,
                    because=segment.unmeasured_because
                    or (
                        "No figure for this segment was proven against a table "
                        "in the filing."
                    ),
                )
            )

        if segment.revenue_models:
            continue

        gaps.append(
            Unestablished(
                segment=segment.name,
                dimension=Dimension.EARNING,
                because=segment.undescribed_because
                or (
                    "The filing's description of this segment names no way of earning."
                ),
            )
        )

    return tuple(gaps)


def _pct(share: float) -> str:
    """A share as an investor reads it."""

    return f"{share * 100:.0f}%"
