"""Consensus is a property of repeated observations, never a preference."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    RevenueModel,
    SegmentDescription,
)
from app.domain.knowledge_consensus import (
    ConsensusState,
    consensus_of,
)
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


def source(key: str = "0001045810-26-000021") -> PrimarySource:
    return PrimarySource(
        symbol="NVDA",
        company="NVIDIA Corporation",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
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


def sized(name: str, share: float, row: int) -> MeasuredShare:
    return MeasuredShare(
        numerator=figure(name, 1000.0 * share, row),
        denominator=figure("Total", 1000.0, 9),
    )


def segment(
    name: str,
    *,
    share: float | None = None,
    row: int = 1,
    earns: tuple[RevenueModel, ...] = (),
    quoted: str | None = None,
    undescribed: str | None = None,
    unmeasured: str | None = None,
) -> BusinessSegment:
    return BusinessSegment(
        name=name,
        revenue=sized(name, share, row) if share is not None else None,
        description=(
            SegmentDescription(
                evidence=DescribedSegment(
                    quoted=quoted,
                    under=name,
                    distance=0,
                    ownership=Ownership.STRUCTURE,
                ),
                revenue_models=earns,
            )
            if quoted is not None
            else None
        ),
        undescribed_because=undescribed,
        unmeasured_because=unmeasured,
    )


def observation(
    *segments: BusinessSegment,
    ordinal: int = 0,
    key: str = "0001045810-26-000021",
) -> CompanyKnowledgeObservation:
    return CompanyKnowledgeObservation(
        symbol="NVDA",
        description=f"Self-description as worded by observation {ordinal}.",
        segments=segments,
        source=source(key),
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime(2026, 8, 7, tzinfo=UTC) + timedelta(hours=ordinal),
        ),
    )


def graphics(
    earns: tuple[RevenueModel, ...], ordinal: int
) -> CompanyKnowledgeObservation:
    """NVIDIA's measured shape: sizes identical, prose moving."""

    return observation(
        segment(
            "Graphics",
            share=0.10,
            earns=earns,
            quoted="includes GeForce GPUs",
        ),
        ordinal=ordinal,
    )


MFG = (RevenueModel.MANUFACTURING,)
MFG_SERVICES = (RevenueModel.MANUFACTURING, RevenueModel.SERVICES)


# ── the rule ────────────────────────────────────────────────────────


def test_a_strict_majority_settles_a_claim_with_an_observed_value() -> None:
    """NVIDIA's shape at quorum: 3 of 5 say manufacturing and services."""

    consensus = consensus_of(
        (
            graphics(MFG_SERVICES, 0),
            graphics(MFG, 1),
            graphics(MFG_SERVICES, 2),
            graphics(MFG, 3),
            graphics(MFG_SERVICES, 4),
        )
    )

    assert consensus.state is ConsensusState.QUORATE

    graphics_consensus = consensus.segments[0]

    assert graphics_consensus.revenue_models == MFG_SERVICES
    assert graphics_consensus.described is True
    assert graphics_consensus.undescribed_because is None


def test_the_full_distribution_survives_beside_the_winner() -> None:
    """3/5 and 5/5 must never look identical downstream."""

    split = consensus_of(
        (
            graphics(MFG_SERVICES, 0),
            graphics(MFG, 1),
            graphics(MFG_SERVICES, 2),
            graphics(MFG, 3),
            graphics(MFG_SERVICES, 4),
        )
    )
    unanimous = consensus_of(tuple(graphics(MFG_SERVICES, n) for n in range(5)))

    assert split.segments[0].revenue_models == unanimous.segments[0].revenue_models

    assert split.segments[0].earning_agreement.agreeing == 3
    assert not split.segments[0].earning_agreement.settled
    assert unanimous.segments[0].earning_agreement.settled


def test_a_plurality_settles_nothing_and_carries_its_distribution() -> None:
    """CAT's Financial Products shape: 2/2/1 has no strict majority."""

    fs = (RevenueModel.FINANCIAL_SPREAD,)
    fs_premiums = (RevenueModel.FINANCIAL_SPREAD, RevenueModel.PREMIUMS)
    fs_services = (RevenueModel.FINANCIAL_SPREAD, RevenueModel.SERVICES)

    consensus = consensus_of(
        (
            graphics(fs, 0),
            graphics(fs, 1),
            graphics(fs_premiums, 2),
            graphics(fs_premiums, 3),
            graphics(fs_services, 4),
        )
    )

    unsettled = consensus.segments[0]

    assert unsettled.revenue_models == ()
    assert unsettled.described is True
    assert "unsettled across 5 observations" in (unsettled.undescribed_because or "")
    assert "2× financial_spread" in (unsettled.undescribed_because or "")
    assert "1× financial_spread, services" in (unsettled.undescribed_because or "")


def test_an_absence_wins_the_vote_with_full_standing() -> None:
    """
    META's Reality Labs shape at quorum: two genuine descriptions lose
    to three counted absences, and stay inspectable as the minority.
    """

    refused = "The description quotes words printed outside the owning section."

    consensus = consensus_of(
        tuple(
            observation(segment("Reality Labs", undescribed=refused), ordinal=n)
            for n in range(3)
        )
        + tuple(
            observation(
                segment(
                    "Reality Labs",
                    earns=(RevenueModel.RETAIL,),
                    quoted=f"product description worded {n} ways",
                ),
                ordinal=3 + n,
            )
            for n in range(2)
        )
    )

    reality_labs = consensus.segments[0]

    assert reality_labs.described is False
    assert reality_labs.revenue_models == ()
    assert refused in (reality_labs.undescribed_because or "")
    assert "3 of 5 observations" in (reality_labs.undescribed_because or "")

    # The minority's genuine spans remain in the record.
    minority = [answer.stated for answer in reality_labs.span_agreement.answers]

    assert any("product description" in span for span in minority)


def test_every_settled_value_was_actually_observed() -> None:
    """Consensus selects; it never synthesizes.

    Observations {a}, {b}, {a,b,c} must not elect {a,b} — a set nobody
    asserted, with no reading to walk back to.
    """

    a = (RevenueModel.ADVERTISING,)
    b = (RevenueModel.SUBSCRIPTION,)
    abc = (
        RevenueModel.ADVERTISING,
        RevenueModel.SUBSCRIPTION,
        RevenueModel.TRANSACTION,
    )

    consensus = consensus_of((graphics(a, 0), graphics(b, 1), graphics(abc, 2)))

    assert consensus.segments[0].revenue_models == ()
    assert "unsettled" in (consensus.segments[0].undescribed_because or "")


def test_order_is_normalized_where_it_carries_no_meaning() -> None:
    """The same set in two orders is one answer, not two."""

    consensus = consensus_of(
        (
            graphics((RevenueModel.SERVICES, RevenueModel.MANUFACTURING), 0),
            graphics((RevenueModel.MANUFACTURING, RevenueModel.SERVICES), 1),
            graphics(MFG, 2),
        )
    )

    assert consensus.segments[0].revenue_models == MFG_SERVICES
    assert consensus.segments[0].earning_agreement.agreeing == 2


def test_a_settled_size_is_the_evidence_of_an_observation_that_gave_it() -> None:
    with_size = tuple(graphics(MFG_SERVICES, n) for n in range(5))

    consensus = consensus_of(with_size)

    settled = consensus.segments[0].revenue

    assert settled is not None
    assert settled.numerator.cell == CellReference(table=2, row=1, column=1)
    assert settled.share == pytest.approx(0.10)


def test_identity_settles_by_majority_and_keeps_the_minority_visible() -> None:
    """JPM's shape: a fourth segment in a minority of observations."""

    three = tuple(
        observation(segment("CCB"), segment("CIB"), segment("AWM"), ordinal=n)
        for n in range(3)
    )
    four = tuple(
        observation(
            segment("CCB"),
            segment("CIB"),
            segment("AWM"),
            segment("Corporate"),
            ordinal=3 + n,
        )
        for n in range(2)
    )

    consensus = consensus_of(three + four)

    assert [named.name for named in consensus.segments] == ["CCB", "CIB", "AWM"]

    # Corporate is disagreement on the record, not a silent removal.
    assert consensus.identity.agreeing == 3
    assert len(consensus.identity.answers) == 2
    assert any("Corporate" in answer.stated for answer in consensus.identity.answers)


def test_an_unsettled_identity_leaves_no_segments_and_says_why() -> None:
    consensus = consensus_of(
        (
            observation(segment("A"), ordinal=0),
            observation(segment("B"), ordinal=1),
        )
    )

    assert consensus.segments == ()
    assert "unsettled across 2 observations" in (consensus.segments_because or "")


def test_a_segment_claim_is_counted_over_the_observations_that_named_it() -> None:
    """Identity can settle on a set an observation did not give."""

    consensus = consensus_of(
        (
            observation(segment("A", share=0.6), ordinal=0),
            observation(segment("A", share=0.6), ordinal=1),
            observation(segment("A", share=0.6), ordinal=2),
            observation(segment("A", share=0.6), segment("B", row=2), ordinal=3),
            observation(segment("A", share=0.6), ordinal=4),
        )
    )

    only_a = consensus.segments

    assert [named.name for named in only_a] == ["A"]
    assert only_a[0].named_in == 5
    assert only_a[0].size_agreement.readings == 5


# ── the states ──────────────────────────────────────────────────────


def test_one_observation_is_never_called_a_consensus() -> None:
    """Width 1 keeps operating, labeled. The defect was the missing label."""

    single = consensus_of((graphics(MFG_SERVICES, 0),))

    assert single.observation_count == 1
    assert single.state is ConsensusState.INSUFFICIENT_QUORUM
    assert "a single reading, not a consensus" in single.reading.source

    # The values are served — refusing them would discard verified
    # evidence — and every claim still reads as the observation's.
    assert single.segments[0].revenue_models == MFG_SERVICES


def test_a_quorate_consensus_says_so_in_its_provenance() -> None:
    quorate = consensus_of(tuple(graphics(MFG_SERVICES, n) for n in range(5)))

    assert quorate.is_quorate
    assert "consensus of 5 observations" in quorate.reading.source


def test_the_self_description_is_the_earliest_observations_wording() -> None:
    """Content-blind by position, until its variance is calibrated."""

    consensus = consensus_of((graphics(MFG, 0), graphics(MFG, 1), graphics(MFG, 2)))

    assert consensus.description == "Self-description as worded by observation 0."


# ── the boundaries ──────────────────────────────────────────────────


def test_a_changed_rule_recomputes_without_touching_observations() -> None:
    """Derived on read: the same set answers differently under another quorum."""

    observations = tuple(graphics(MFG_SERVICES, n) for n in range(3))

    assert consensus_of(observations, quorum=5).state is (
        ConsensusState.INSUFFICIENT_QUORUM
    )
    assert consensus_of(observations, quorum=3).state is ConsensusState.QUORATE


def test_a_consensus_over_nothing_is_refused() -> None:
    with pytest.raises(ValueError):
        consensus_of(())


def test_a_consensus_across_two_documents_is_refused() -> None:
    with pytest.raises(ValueError) as refused:
        consensus_of(
            (
                graphics(MFG, 0),
                observation(segment("Graphics"), ordinal=1, key="other-doc"),
            )
        )

    assert "one immutable document" in str(refused.value)


# ── agreement strength, and what it never claims ────────────────────


def test_a_majority_is_worded_with_its_count_and_never_without() -> None:
    """ "Narrow" alone would be an interpretation wearing a measurement's
    authority; the count always travels with the word."""

    from app.domain.agreement import agreement as agree

    assert agree("q", ("a",) * 5).stated_majority() == "unanimous (5/5)"
    assert agree("q", ("a", "a", "a", "b", "b")).stated_majority() == (
        "a narrow majority (3/5)"
    )
    assert agree("q", ("a", "a", "a", "a", "b")).stated_majority() == (
        "a majority (4/5)"
    )
    assert agree("q", ("a", "a", "b", "b", "c")).stated_majority() == (
        "no majority (2/5)"
    )


def test_the_smallest_strict_majority_is_named_narrow() -> None:
    """One changed answer would unsettle it, and the name says so."""

    from app.domain.agreement import agreement as agree

    assert agree("q", ("a", "a", "a", "b", "b")).is_narrow
    assert not agree("q", ("a", "a", "a", "a", "b")).is_narrow
    assert not agree("q", ("a", "a", "b", "b")).is_narrow
