"""Business Understanding explains; it never infers, and never compensates."""

from datetime import UTC, datetime, timedelta

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    RevenueModel,
    SegmentDescription,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.prose_evidence import DescribedSegment, Ownership
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
)
from app.services.understanding_engine import understand

SOURCE = PrimarySource(
    symbol="NVDA",
    company="NVIDIA Corporation",
    source_type=SourceType.ANNUAL_REPORT,
    identifier="10-K 0001045810-26-000021",
    key="0001045810-26-000021",
    published_on=datetime(2026, 2, 25, tzinfo=UTC).date(),
    reporting_period=None,
    document_format="html",
    language="en",
    location="https://example.invalid/10k.htm",
    provider="SEC EDGAR",
    authority=SourceAuthority.REGULATOR_FILED,
    verification=(IdentityCheck.REGISTER_INDEXED,),
)


def figure(label: str, value: float, row: int) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header="2026",
        printed=f"{value:,.0f}",
        value=value,
        cell=CellReference(table=2, row=row, column=1),
        caption="Revenue by segment",
    )


def segment(
    name: str,
    *,
    share: float | None = None,
    row: int = 1,
    earns: tuple[RevenueModel, ...] = (),
) -> BusinessSegment:
    return BusinessSegment(
        name=name,
        revenue=(
            MeasuredShare(
                numerator=figure(name, 1000.0 * share, row),
                denominator=figure("Total", 1000.0, 9),
            )
            if share is not None
            else None
        ),
        description=(
            SegmentDescription(
                evidence=DescribedSegment(
                    quoted=f"what {name} does",
                    under=name,
                    distance=0,
                    ownership=Ownership.STRUCTURE,
                ),
                revenue_models=earns,
            )
            if earns
            else None
        ),
    )


def consensus(*observations_segments: tuple[BusinessSegment, ...]):
    return consensus_of(
        tuple(
            CompanyKnowledgeObservation(
                symbol="NVDA",
                description="What the company says it does.",
                segments=segments,
                source=SOURCE,
                reading=Provenance(
                    source="10-K via SEC EDGAR, read by stub-1",
                    observed_at=datetime(2026, 8, 7, tzinfo=UTC)
                    + timedelta(hours=ordinal),
                ),
            )
            for ordinal, segments in enumerate(observations_segments)
        )
    )


MFG = (RevenueModel.MANUFACTURING,)
MFG_SERVICES = (RevenueModel.MANUFACTURING, RevenueModel.SERVICES)


COMPUTE_EARNS = (
    RevenueModel.LICENSING,
    RevenueModel.MANUFACTURING,
    RevenueModel.SERVICES,
)


def nvidia_shape():
    """The accepted live shape: 3/5 manufacturing-only for Graphics.

    Compute carries services at 90%, so whether Graphics also earns by
    services is exactly what separates Manufacturer (services 90%, 10%
    behind manufacturing) from Diversified (services 100%, tied).
    """

    both = (
        segment("Compute", share=0.90, earns=COMPUTE_EARNS),
        segment("Graphics", share=0.10, earns=MFG_SERVICES, row=2),
    )
    one = (
        segment("Compute", share=0.90, earns=COMPUTE_EARNS),
        segment("Graphics", share=0.10, earns=MFG, row=2),
    )

    return consensus(one, one, one, both, both)


def cat_shape():
    """Three settled segments plus an unsettled 2/2/1 earning claim."""

    def observation(fp_earns: tuple[RevenueModel, ...]):
        return (
            segment("Construction", share=0.37, earns=MFG_SERVICES),
            segment("Resource", share=0.18, earns=MFG_SERVICES, row=2),
            segment("Power", share=0.48, earns=MFG_SERVICES, row=3),
            segment("Financial Products", share=0.06, earns=fp_earns, row=4),
        )

    fs = (RevenueModel.FINANCIAL_SPREAD,)
    fs_services = (RevenueModel.FINANCIAL_SPREAD, RevenueModel.SERVICES)
    fs_premiums = (RevenueModel.FINANCIAL_SPREAD, RevenueModel.PREMIUMS)

    return consensus(
        observation(fs_services),
        observation(fs_services),
        observation(fs),
        observation(fs),
        observation(fs_premiums),
    )


# ── the explanation ─────────────────────────────────────────────────


def test_the_engine_is_worded_from_the_rules_own_outcome() -> None:
    understanding = understand(nvidia_shape())

    assert understanding.engine.startswith("single-engine — manufacturing")
    assert "100%" in understanding.engine


def test_a_diversified_business_reads_as_multi_engine() -> None:
    understanding = understand(cat_shape())

    assert understanding.engine.startswith("multi-engine")
    assert "manufacturing" in understanding.engine
    assert "services" in understanding.engine


def test_a_mechanism_is_as_established_as_the_weakest_claim_carrying_it() -> None:
    """Manufacturing runs through both segments; Graphics holds it 3/5."""

    understanding = understand(nvidia_shape())

    manufacturing = next(
        mechanism
        for mechanism in understanding.mechanisms
        if mechanism.model is RevenueModel.MANUFACTURING
    )

    assert manufacturing.support.counted() == "3/5"
    assert manufacturing in understanding.narrow_support


def test_what_the_business_sells_through_carries_only_settled_facts() -> None:
    understanding = understand(nvidia_shape())

    graphics = next(sold for sold in understanding.sells if sold.name == "Graphics")

    assert graphics.share == 0.1
    assert graphics.mechanisms == MFG


# ── the contingencies ───────────────────────────────────────────────


def test_a_narrow_claim_names_the_conclusion_that_depends_on_it() -> None:
    """
    NVIDIA's acceptance: why Manufacturer, why not Diversified, and
    which conclusion depends on the 3/5 majority — all from one
    contingency, evaluated only at observed answers.
    """

    understanding = understand(nvidia_shape())

    contingency = understanding.contingencies[0]

    assert contingency.claim == "how 'Graphics' earns"
    assert contingency.as_it_stands == "Manufacturer"
    assert contingency.consumed
    assert contingency.could_change_conclusion

    minority = next(
        alternative
        for alternative in contingency.alternatives
        if alternative.answer == "manufacturing, services"
    )

    assert minority.given == 2
    assert minority.concludes == "Diversified"


def test_an_unsettled_claim_reports_what_each_observed_answer_concludes() -> None:
    """
    CAT's acceptance: the unsettled claim was excluded, not resolved —
    and the report shows exactly which observed answer would have
    changed the conclusion, which is why excluding it was the honest
    move.
    """

    understanding = understand(cat_shape())

    contingency = understanding.contingencies[0]

    assert contingency.claim == "how 'Financial Products' earns"
    assert not contingency.consumed
    assert contingency.as_it_stands == "Diversified"

    concluded = {
        alternative.answer: alternative.concludes
        for alternative in contingency.alternatives
    }

    assert concluded["financial_spread"] == "Diversified"
    assert concluded["financial_spread, premiums"] == "Diversified"
    assert concluded["financial_spread, services"] == (
        "Service business, then manufacturer"
    )


def test_alternatives_are_only_answers_some_observation_gave() -> None:
    """The no-synthesis rule reaches the hypotheticals too."""

    understanding = understand(cat_shape())

    observed = {
        answer.stated for answer in understanding.contingencies[0].agreement.answers
    }

    assert {
        alternative.answer
        for alternative in understanding.contingencies[0].alternatives
    } == observed


def test_a_settled_unanimous_claim_raises_no_contingency() -> None:
    same = (segment("Only", share=0.95, earns=MFG),)

    understanding = understand(consensus(same, same, same, same, same))

    assert understanding.contingencies == ()


# ── never infers, never compensates ─────────────────────────────────


def test_what_the_consensus_leaves_unestablished_stays_unestablished() -> None:
    understanding = understand(cat_shape())

    gaps = {(gap.segment, gap.dimension.value) for gap in understanding.not_established}

    assert ("Financial Products", "earning") in gaps

    financial = next(
        sold for sold in understanding.sells if sold.name == "Financial Products"
    )

    assert financial.mechanisms == ()
    assert "unsettled across 5 observations" in (financial.mechanisms_because or "")


def test_understanding_is_deterministic() -> None:
    assert understand(nvidia_shape()) == understand(nvidia_shape())


def test_the_consensus_width_travels_on_the_understanding() -> None:
    understanding = understand(nvidia_shape())

    assert understanding.quorate
    assert understanding.observation_count == 5

    single = understand(consensus((segment("Only", share=0.95, earns=MFG),)))

    assert not single.quorate
    assert single.observation_count == 1
