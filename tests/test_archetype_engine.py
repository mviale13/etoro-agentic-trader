"""A company is what its own filing shows it earns from, or it is unclassified.

Every fixture here is the shape of a filing this platform has actually
read, named in the test that uses it. Invented shapes would prove the
rules self-consistent; these prove them right about documents.
"""

from datetime import UTC, datetime

import pytest

from app.domain.company_archetype import ARCHETYPE_OF, Archetype, Dimension
from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    RevenueModel,
    SegmentDescription,
)
from app.domain.knowledge_consensus import CompanyKnowledgeConsensus, consensus_of
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.prose_evidence import DescribedSegment
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, MeasuredShare, ReportedFigure
from app.services.archetype_engine import ENOUGH_EXPLAINED, LEADS, TIED, classify

#: The consolidated total every fixture segment is measured against.
TOTAL = 100_000.0


def size(share: float, row: int) -> MeasuredShare:
    """A segment's size, as two cells of one table divided."""

    def figure(label: str, value: float, at: int) -> ReportedFigure:
        return ReportedFigure(
            label=label,
            column_header="2025",
            printed=f"{value:,.0f}",
            value=value,
            cell=CellReference(table=1, row=at, column=1),
            caption="($ in millions)",
        )

    return MeasuredShare(
        numerator=figure("Segment", TOTAL * share, row),
        denominator=figure("Revenues", TOTAL, 99),
    )


def segment(
    name: str,
    *,
    share: float | None = None,
    earns: tuple[RevenueModel, ...] = (),
    row: int = 1,
    undescribed: str | None = None,
    unmeasured: str | None = None,
) -> BusinessSegment:
    """One segment, with either dimension present or absent independently."""

    description = (
        SegmentDescription(
            evidence=DescribedSegment(
                quoted=f"what {name} does",
                under=name,
                distance=0,
            ),
            revenue_models=earns,
        )
        if earns or undescribed is None
        else None
    )

    return BusinessSegment(
        name=name,
        revenue=size(share, row) if share is not None else None,
        description=description,
        undescribed_because=undescribed,
        unmeasured_because=unmeasured,
    )


def company(symbol: str, *segments: BusinessSegment) -> CompanyKnowledgeConsensus:
    """One observation's facts, as the width-1 consensus the rules consume.

    The rules read consensus only, so the harness derives one — at a
    quorum of one, which is the calibration instrument's question, not
    the decision path's. What is under test here is the rules, and the
    derivation itself is tested in test_knowledge_consensus.
    """

    return _consensus(
        CompanyKnowledgeObservation(
            symbol=symbol,
            description=f"What {symbol} says it does.",
            segments=segments,
            source=PrimarySource(
                symbol=symbol,
                company=symbol,
                source_type=SourceType.ANNUAL_REPORT,
                identifier="10-K 0000000000-00-000000",
                key="0000000000-00-000000",
                published_on=datetime(2026, 1, 1, tzinfo=UTC).date(),
                reporting_period=None,
                document_format="html",
                language="en",
                location="https://www.sec.gov/Archives/x",
                provider="SEC EDGAR",
                authority=SourceAuthority.REGULATOR_FILED,
                verification=(IdentityCheck.REGISTER_INDEXED,),
            ),
            reading=Provenance(
                source="10-K via SEC EDGAR", observed_at=datetime.now(UTC)
            ),
        )
    )


def _consensus(observation: CompanyKnowledgeObservation) -> CompanyKnowledgeConsensus:
    return consensus_of((observation,), quorum=1)


# ── the four regimes ────────────────────────────────────────────────


def test_one_way_of_earning_that_leads_names_the_company() -> None:
    """
    NVIDIA's shape. Both segments manufacture; only the larger one, 90%
    of revenue, also licenses and provides services. Manufacturing runs
    through everything, so the company is a manufacturer — decided by
    arithmetic over two measured sizes, not by the word "semiconductor"
    appearing anywhere.
    """

    nvda = company(
        "NVDA",
        segment(
            "Compute & Networking",
            share=0.90,
            row=1,
            earns=(
                RevenueModel.MANUFACTURING,
                RevenueModel.LICENSING,
                RevenueModel.SERVICES,
            ),
        ),
        segment("Graphics", share=0.10, row=2, earns=(RevenueModel.MANUFACTURING,)),
    )

    archetype = classify(nvda)

    assert archetype.primary is Archetype.MANUFACTURER
    assert archetype.is_ranked
    assert archetype.undecided_because is None


def test_several_ways_of_earning_tied_at_the_top_is_diversified() -> None:
    """
    Disney's shape, and the reason this slice exists. All three segments
    license, transact and provide services, so all three coverages are
    identical and no arithmetic separates them. An industry code would
    have said "Entertainment"; the filing says the business earns three
    ways at once and does not rank them.
    """

    dis = classify(
        company(
            "DIS",
            segment(
                "Entertainment",
                share=0.45,
                row=1,
                earns=(
                    RevenueModel.SUBSCRIPTION,
                    RevenueModel.ADVERTISING,
                    RevenueModel.LICENSING,
                    RevenueModel.TRANSACTION,
                    RevenueModel.SERVICES,
                ),
            ),
            segment(
                "Sports",
                share=0.19,
                row=2,
                earns=(
                    RevenueModel.SUBSCRIPTION,
                    RevenueModel.ADVERTISING,
                    RevenueModel.LICENSING,
                    RevenueModel.TRANSACTION,
                    RevenueModel.SERVICES,
                ),
            ),
            segment(
                "Experiences",
                share=0.36,
                row=3,
                earns=(
                    RevenueModel.TRANSACTION,
                    RevenueModel.RETAIL,
                    RevenueModel.LICENSING,
                    RevenueModel.SERVICES,
                ),
            ),
        )
    )

    assert dis.primary is Archetype.DIVERSIFIED
    assert dis.secondary is None
    assert not dis.is_ranked

    # And it says which ways of earning tied, so the finding is checkable.
    concluded = dis.basis[0].concluded
    assert "licensing" in concluded
    assert "transaction" in concluded
    assert "services" in concluded


def test_ways_of_earning_without_measured_sizes_are_candidates_not_a_ranking() -> None:
    """
    Caterpillar's shape: four described segments, not one of whose sizes
    was proven against a table. The platform knows Caterpillar
    manufactures and lends. It does not know which is the business, and
    counting three manufacturing segments against one finance segment
    would weigh a company's largest and smallest parts equally.
    """

    cat = classify(
        company(
            "CAT",
            segment("Construction", earns=(RevenueModel.MANUFACTURING,)),
            segment("Resource", earns=(RevenueModel.MANUFACTURING,)),
            segment("Power & Energy", earns=(RevenueModel.MANUFACTURING,)),
            segment(
                "Financial Products",
                earns=(RevenueModel.FINANCIAL_SPREAD, RevenueModel.PREMIUMS),
            ),
        )
    )

    assert cat.primary is None
    assert cat.secondary is None
    assert set(cat.candidates) == {
        Archetype.MANUFACTURER,
        Archetype.LENDER,
        Archetype.INSURER,
    }

    # Unranked, so every coverage is absent rather than zero: nothing was
    # weighed, which is not the same as weighing nothing.
    assert all(coverage.covers is None for coverage in cat.coverage)
    assert cat.undecided_because is not None


def test_a_fully_measured_company_with_no_evidenced_earning_is_unclassified() -> None:
    """
    Meta's shape, and the one that decides whether this layer is honest.
    Every share is measured, both descriptions were refused — one for
    quoting the other segment's words, one for sitting 404 characters
    from its own naming — and the most obvious advertising business in
    the market comes back unclassified rather than guessed.
    """

    meta = classify(
        company(
            "META",
            segment(
                "Family of Apps",
                share=0.99,
                row=1,
                undescribed="quotes words the document prints under 'Reality Labs'",
            ),
            segment(
                "Reality Labs",
                share=0.01,
                row=2,
                undescribed="sits 404 characters from where the document named it",
            ),
        )
    )

    assert meta.primary is None
    assert meta.candidates == ()
    assert Archetype.ADVERTISING_BUSINESS not in meta.candidates
    assert meta.measured == pytest.approx(1.0)
    assert meta.explained == 0.0


def test_diversified_and_unranked_are_not_the_same_answer() -> None:
    """
    One says the business genuinely has no leading way of earning. The
    other says this platform cannot tell. Collapsing them would report
    an absence of measurement as a finding about the company.
    """

    measured = classify(
        company(
            "DIS",
            segment(
                "One",
                share=0.5,
                row=1,
                earns=(RevenueModel.LICENSING, RevenueModel.SERVICES),
            ),
            segment(
                "Two",
                share=0.5,
                row=2,
                earns=(RevenueModel.LICENSING, RevenueModel.SERVICES),
            ),
        )
    )
    unmeasured = classify(
        company(
            "CAT",
            segment("One", earns=(RevenueModel.LICENSING, RevenueModel.SERVICES)),
            segment("Two", earns=(RevenueModel.LICENSING, RevenueModel.SERVICES)),
        )
    )

    assert measured.primary is Archetype.DIVERSIFIED
    assert measured.undecided_because is None

    assert unmeasured.primary is None
    assert unmeasured.undecided_because is not None


# ── what the rules refuse to do ─────────────────────────────────────


def test_a_segments_name_is_never_read_as_what_it_does() -> None:
    """
    Volkswagen's shape. A segment called *Finanzdienstleistungen* is 19%
    of revenue and no description of it was established, so nothing here
    concludes Volkswagen lends. Reading meaning out of the label would
    be a taxonomy again — this platform's own, in German — which is the
    thing the engine exists to stop doing.
    """

    vow = classify(
        company(
            "VOW3.DE",
            segment(
                "Pkw und leichte Nutzfahrzeuge",
                share=0.76,
                row=1,
                undescribed="no words at all",
            ),
            segment("Nutzfahrzeuge", share=0.13, row=2, undescribed="no words at all"),
            segment(
                "Finanzdienstleistungen",
                share=0.19,
                row=3,
                undescribed="no words at all",
            ),
        )
    )

    assert vow.primary is None
    assert Archetype.LENDER not in vow.candidates
    assert vow.coverage == ()

    # The sizes survive: they were proven by cells, and a missing
    # description is not evidence against a measurement.
    assert vow.measured == pytest.approx(1.08)


def test_an_archetype_is_never_decided_from_a_minority_of_the_business() -> None:
    """
    A tenth of revenue subscribing does not make a subscription
    business, however clean that tenth's evidence is. The floor is the
    point past which the explained part would be outvoted by the part
    that is not.
    """

    thin = classify(
        company(
            "THIN",
            segment("Small", share=0.10, row=1, earns=(RevenueModel.SUBSCRIPTION,)),
            segment("Large", share=0.90, row=2, undescribed="not described"),
        )
    )

    assert thin.explained == pytest.approx(0.10)
    assert thin.explained < ENOUGH_EXPLAINED
    assert thin.primary is None
    assert thin.basis[0].rule == "too-little-explained"


def test_coverage_counts_a_segments_whole_size_for_every_way_it_earns() -> None:
    """
    A filing states what a segment earned and which ways it earns; it
    never splits the one between the others. So a segment worth 60%
    earning three ways contributes 60% to each, coverages overlap, and
    they do not sum to 1 — which is why this is called coverage and not
    revenue.
    """

    mix = classify(
        company(
            "MIX",
            segment(
                "Both",
                share=0.60,
                row=1,
                earns=(RevenueModel.SUBSCRIPTION, RevenueModel.ADVERTISING),
            ),
            segment("One", share=0.40, row=2, earns=(RevenueModel.SUBSCRIPTION,)),
        )
    ).coverage

    covers = {coverage.model: coverage.covers for coverage in mix}

    assert covers[RevenueModel.SUBSCRIPTION] == pytest.approx(1.0)
    assert covers[RevenueModel.ADVERTISING] == pytest.approx(0.60)
    assert sum(covers.values()) > 1.0


def test_a_runner_up_that_ties_with_the_next_one_is_not_a_secondary() -> None:
    """
    NVIDIA licenses and provides services across exactly the same 90% of
    revenue. Naming either one the secondary archetype would pick
    between them on nothing at all.
    """

    nvda = classify(
        company(
            "NVDA",
            segment(
                "Compute & Networking",
                share=0.90,
                row=1,
                earns=(
                    RevenueModel.MANUFACTURING,
                    RevenueModel.LICENSING,
                    RevenueModel.SERVICES,
                ),
            ),
            segment("Graphics", share=0.10, row=2, earns=(RevenueModel.MANUFACTURING,)),
        )
    )

    assert nvda.primary is Archetype.MANUFACTURER
    assert nvda.secondary is None


def test_a_runner_up_that_stands_alone_is_the_secondary() -> None:
    """The same rule the other way: a clear second is reported as one."""

    both = classify(
        company(
            "BOTH",
            segment(
                "Large",
                share=0.70,
                row=1,
                earns=(RevenueModel.MANUFACTURING, RevenueModel.SERVICES),
            ),
            segment("Small", share=0.30, row=2, earns=(RevenueModel.MANUFACTURING,)),
        )
    )

    assert both.primary is Archetype.MANUFACTURER
    assert both.secondary is Archetype.SERVICE_BUSINESS


def test_coverages_within_the_tie_tolerance_are_not_ordered() -> None:
    """
    The mix is arithmetic over segment sizes, so a gap of a percentage
    point says which segments happen to carry a model — not which way of
    earning leads a business.
    """

    close = classify(
        company(
            "CLOSE",
            segment(
                "Large",
                share=0.98,
                row=1,
                earns=(RevenueModel.MANUFACTURING, RevenueModel.SERVICES),
            ),
            segment("Small", share=0.02, row=2, earns=(RevenueModel.MANUFACTURING,)),
        )
    )

    gap = close.coverage[0].covers - close.coverage[1].covers
    assert gap < TIED
    assert close.primary is Archetype.DIVERSIFIED


# ── what a reader is owed ───────────────────────────────────────────


def test_every_missing_dimension_carries_the_knowledge_layers_own_reason() -> None:
    """
    An absence carries its reason across every layer of this platform,
    and a rule restating it in its own words would be a second,
    unevidenced account of the same event.
    """

    refused = "quotes words the document prints under 'Reality Labs'"

    gaps = classify(
        company("META", segment("Family of Apps", share=0.99, undescribed=refused))
    ).missing

    earning = [gap for gap in gaps if gap.dimension is Dimension.EARNING]

    # The knowledge layer's own words survive, with the consensus width
    # counted beside them — an absence at width one says it is one.
    assert len(earning) == 1
    assert refused in earning[0].because
    assert "1 of 1 observations" in earning[0].because


def test_a_missing_size_and_a_missing_description_are_reported_apart() -> None:
    """
    They fail independently in the knowledge layer and they are acted on
    differently here, so a reader must be able to tell which one is
    missing without inferring it.
    """

    gaps = classify(
        company(
            "MIXED",
            segment("Measured, undescribed", share=0.60, undescribed="no words"),
            segment("Described, unmeasured", earns=(RevenueModel.RETAIL,)),
        )
    ).missing

    assert {(gap.segment, gap.dimension) for gap in gaps} == {
        ("Measured, undescribed", Dimension.EARNING),
        ("Described, unmeasured", Dimension.SIZE),
    }


def test_a_described_segment_that_names_no_way_of_earning_is_a_gap_with_a_reason() -> (
    None
):
    """
    JPMorgan's shape: a description that passed applicability and cited
    the sentence listing the segments, which says nothing about how any
    of them earns. Applicable and uninformative are different failures,
    and the second one still leaves the platform unable to classify.
    """

    gaps = classify(company("JPM", segment("CCB", share=0.60, earns=()))).missing

    earning = [gap for gap in gaps if gap.dimension is Dimension.EARNING]

    assert len(earning) == 1
    assert "names no way of earning" in earning[0].because


def test_every_rule_that_fires_records_the_facts_it_read() -> None:
    """
    A classification a reader cannot audit is a label, which is what
    this layer refuses to be. Every ruling names itself, states the
    grounded facts it was given, and states what it concluded.
    """

    decided = classify(
        company(
            "NVDA",
            segment("Big", share=0.90, row=1, earns=(RevenueModel.MANUFACTURING,)),
            segment("Small", share=0.10, row=2, earns=(RevenueModel.MANUFACTURING,)),
        )
    )

    assert decided.basis
    for ruling in decided.basis:
        assert ruling.rule
        assert ruling.read
        assert ruling.concluded

    # And the facts read are the measured coverage, not a restatement of
    # the conclusion.
    assert "manufacturing" in decided.basis[0].read
    assert "100%" in decided.basis[0].read


def test_an_unclassified_company_always_says_why() -> None:
    """
    The question a reader has when a company comes back unclassified is
    why, and a blank would read as ignorance of the company rather than
    honesty about the reading.
    """

    for knowledge in (
        company("NONE"),
        company("META", segment("Apps", share=0.99, undescribed="refused")),
        company("THIN", segment("Small", share=0.10, earns=(RevenueModel.RETAIL,))),
        company("CAT", segment("Products", earns=(RevenueModel.MANUFACTURING,))),
    ):
        archetype = classify(knowledge)

        assert archetype.primary is None
        assert archetype.undecided_because
        assert archetype.stated == "Not classified"


def test_a_company_with_no_segments_at_all_is_unclassified_not_empty() -> None:
    """A filing that described no parts leaves nothing to classify on."""

    none = classify(company("NONE"))

    assert none.primary is None
    assert none.coverage == ()
    assert none.basis[0].rule == "nothing-explained"


# ── the vocabulary ──────────────────────────────────────────────────


def test_every_way_of_earning_has_an_archetype() -> None:
    """
    A revenue model with no archetype beside it would be silently
    unclassifiable: the company would come back undecided and no rule
    would say why. A new model must be given its archetype, and this
    fails until it is.
    """

    assert set(ARCHETYPE_OF) == set(RevenueModel)


def test_the_leading_threshold_is_the_one_the_rules_apply() -> None:
    """
    A way of earning just under the floor does not name the company, and
    the same one just over it does. Stated as a test so the constant
    cannot drift from the behaviour it documents.
    """

    def classify_at(share: float) -> Archetype | None:
        return classify(
            company(
                "EDGE",
                segment("Named", share=share, row=1, earns=(RevenueModel.RETAIL,)),
                segment(
                    "Rest",
                    share=1.0 - share,
                    row=2,
                    earns=(RevenueModel.SERVICES, RevenueModel.TRANSACTION),
                ),
            )
        ).primary

    assert classify_at(LEADS - 0.01) is Archetype.DIVERSIFIED
    assert classify_at(LEADS + 0.02) is Archetype.RETAILER


def test_a_missing_size_reports_the_reason_the_reading_recorded() -> None:
    """
    Rather than the one sentence that used to stand for every cause.

    "No figure was proven against a table in the filing" reads as a fact
    about the filing, and for Caterpillar it was a fact about this
    platform: the section holding the table had been located wrongly, so
    the reading never saw it. A reader deciding whether a gap is worth
    chasing needs to know which of those it is.
    """

    gaps = classify(
        company(
            "CAT",
            segment(
                "Financial Products Segment",
                earns=(RevenueModel.FINANCIAL_SPREAD,),
                unmeasured="This filing's discussion prints no table.",
            ),
        )
    ).missing

    size = next(gap for gap in gaps if gap.dimension is Dimension.SIZE)

    assert "This filing's discussion prints no table." in size.because


def test_a_missing_size_the_reading_left_unworded_still_states_one() -> None:
    """A knowledge entry that predates the reason is not shown as blank."""

    gaps = classify(
        company("OLD", segment("Unworded", earns=(RevenueModel.RETAIL,)))
    ).missing

    size = next(gap for gap in gaps if gap.dimension is Dimension.SIZE)

    assert "No observation located a figure for this segment" in size.because


# ── what a conclusion rests on ──────────────────────────────────────


def multi(
    *observations_segments: tuple[BusinessSegment, ...],
) -> CompanyKnowledgeConsensus:
    """A consensus over several observations of one document."""

    return consensus_of(
        tuple(
            CompanyKnowledgeObservation(
                symbol="NVDA",
                description="What NVDA says it does.",
                segments=segments,
                source=company("NVDA").source,
                reading=Provenance(
                    source="10-K via SEC EDGAR",
                    observed_at=datetime.now(UTC),
                ),
            )
            for segments in observations_segments
        )
    )


def test_a_conclusion_carries_the_narrowest_claim_it_rests_on() -> None:
    """NVIDIA's accepted shape: Manufacturer, resting on 3 of 5."""

    both = (
        segment("Compute", share=0.90, earns=(RevenueModel.MANUFACTURING,)),
        segment(
            "Graphics",
            share=0.10,
            earns=(RevenueModel.MANUFACTURING, RevenueModel.SERVICES),
            row=2,
        ),
    )
    one = (
        segment("Compute", share=0.90, earns=(RevenueModel.MANUFACTURING,)),
        segment("Graphics", share=0.10, earns=(RevenueModel.MANUFACTURING,), row=2),
    )

    archetype = classify(multi(one, one, one, both, both))

    assert archetype.quorate
    assert archetype.narrowest is not None
    assert archetype.narrowest.counted() == "3/5"
    assert "a narrow majority (3/5)" in (archetype.rests_on or "")
    assert "how 'Graphics' earns" in (archetype.rests_on or "")
    assert "has not been established" in (archetype.rests_on or "")


def test_a_unanimous_consensus_says_so_rather_than_scoring_itself() -> None:
    same = (segment("Only", share=0.95, earns=(RevenueModel.RETAIL,)),)

    archetype = classify(multi(same, same, same, same, same))

    assert archetype.quorate
    assert "unanimous on every claim consumed" in (archetype.rests_on or "")


def test_below_quorum_nothing_is_authoritative_and_the_basis_says_so() -> None:
    """
    At the decision path's quorum of five, not the harness's one. The
    width-1 conclusion is served, labeled, and never authoritative.
    """

    archetype = classify(
        multi((segment("Only", share=0.95, earns=(RevenueModel.RETAIL,)),))
    )

    assert not archetype.quorate
    assert "nothing decided from it is authoritative" in (archetype.rests_on or "")


def test_an_undecided_archetype_asserts_no_basis() -> None:
    """Its reasons carry the distributions; there is no conclusion to rest."""

    archetype = classify(company("META", segment("FoA", share=0.99)))

    assert archetype.rests_on is None
    assert archetype.narrowest is None
