"""A playbook is earned from understanding, or the fallback says why not."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.company_archetype import Archetype
from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    RevenueModel,
    SegmentDescription,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.domain.playbook_selection import (
    PlaybookSelection,
    RefusedGrounding,
    SelectedBy,
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
from app.services.company_knowledge_service import KnowledgeOutcome, KnowledgeState
from app.services.playbook_mapping import (
    GROUNDED,
    GROUNDED_PAIRS,
    rule_for,
    select_grounded,
)
from app.services.playbook_selection_service import PlaybookSelectionService
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


def observations_of(
    *observations_segments: tuple[BusinessSegment, ...],
) -> tuple[CompanyKnowledgeObservation, ...]:
    return tuple(
        CompanyKnowledgeObservation(
            symbol="NVDA",
            description="What the company says it does.",
            segments=segments,
            source=SOURCE,
            reading=Provenance(
                source="10-K via SEC EDGAR, read by stub-1",
                observed_at=datetime(2026, 8, 7, tzinfo=UTC) + timedelta(hours=ordinal),
            ),
        )
        for ordinal, segments in enumerate(observations_segments)
    )


def consensus(*observations_segments: tuple[BusinessSegment, ...]):
    return consensus_of(observations_of(*observations_segments))


MFG = (RevenueModel.MANUFACTURING,)
MFG_SERVICES = (RevenueModel.MANUFACTURING, RevenueModel.SERVICES)
COMPUTE_EARNS = (
    RevenueModel.LICENSING,
    RevenueModel.MANUFACTURING,
    RevenueModel.SERVICES,
)


def manufacturer_shape():
    """NVDA's accepted live shape: Manufacturer resting on a 3/5 claim."""

    both = (
        segment("Compute", share=0.90, earns=COMPUTE_EARNS),
        segment("Graphics", share=0.10, earns=MFG_SERVICES, row=2),
    )
    one = (
        segment("Compute", share=0.90, earns=COMPUTE_EARNS),
        segment("Graphics", share=0.10, earns=MFG, row=2),
    )

    return consensus(one, one, one, both, both)


def diversified_shape():
    """CAT's accepted live shape: Diversified, one 2/2/1 claim excluded."""

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


def unexplained_shape():
    """META's accepted live shape: measured, and nothing explained."""

    same = (
        segment("Family of Apps", share=0.99),
        segment("Reality Labs", share=0.01, row=2),
    )

    return consensus(same, same, same, same, same)


def unmapped_shape():
    """A conclusion the corpus has not earned a playbook for."""

    same = (segment("Only", share=0.95, earns=(RevenueModel.SERVICES,)),)

    return consensus(same, same, same, same, same)


# ── the mapping ─────────────────────────────────────────────────────


def test_a_manufacturer_at_quorum_selects_industrial_authoritatively() -> None:
    selection = select_grounded(understand(manufacturer_shape()))

    assert isinstance(selection, PlaybookSelection)
    assert selection.playbook.kind is PlaybookKind.INDUSTRIAL
    assert selection.authoritative
    assert selection.selected_by is SelectedBy.BUSINESS_UNDERSTANDING
    assert selection.rule_fired == "manufacturer-activates-industrial"
    assert selection.fallback_reason is None


def test_a_diversified_business_selects_diversified_business() -> None:
    selection = select_grounded(understand(diversified_shape()))

    assert isinstance(selection, PlaybookSelection)
    assert selection.playbook.kind is PlaybookKind.DIVERSIFIED
    assert selection.authoritative
    assert selection.rule_fired == "diversified-activates-diversified-business"


def test_every_fact_consumed_is_a_ruling_a_reader_can_audit() -> None:
    selection = select_grounded(understand(manufacturer_shape()))

    assert isinstance(selection, PlaybookSelection)
    assert selection.facts_consumed
    assert any("one-way-of-earning-leads" in fact for fact in selection.facts_consumed)
    assert selection.narrowest_agreement is not None
    assert "3/5" in selection.narrowest_agreement


def test_the_selection_states_why_the_other_playbook_did_not_fire() -> None:
    """NVDA's acceptance: why not Diversified, in the ruling's own words."""

    selection = select_grounded(understand(manufacturer_shape()))

    assert isinstance(selection, PlaybookSelection)

    not_selected = {
        alternative.kind: alternative
        for alternative in selection.alternatives_considered
    }

    # Every earned rule that did not fire is listed — the pair rule
    # included, named by the whole conclusion that would activate it
    # rather than by the leading engine it shares with nothing here.
    assert set(not_selected) == {PlaybookKind.DIVERSIFIED, PlaybookKind.BANK}
    assert not_selected[PlaybookKind.DIVERSIFIED].activated_by == "Diversified"
    assert (
        not_selected[PlaybookKind.BANK].activated_by == "Service business, then lender"
    )
    assert "clear of anything else" in (
        not_selected[PlaybookKind.DIVERSIFIED].not_selected_because
    )


def test_a_narrow_claim_marks_the_selection_contingent() -> None:
    """NVDA's acceptance: the 3/5, and what a minority answer would select."""

    selection = select_grounded(understand(manufacturer_shape()))

    assert isinstance(selection, PlaybookSelection)
    assert selection.could_change

    contingency = selection.contingencies[0]

    assert contingency.claim == "how 'Graphics' earns"
    assert "3/5" in contingency.agreement
    assert contingency.consumed

    by_answer = {
        alternative.answer: alternative for alternative in contingency.alternatives
    }

    settled = by_answer["manufacturing"]
    minority = by_answer["manufacturing, services"]

    assert settled.selects is PlaybookKind.INDUSTRIAL
    assert not settled.changes_selection

    assert minority.concludes == "Diversified"
    assert minority.selects is PlaybookKind.DIVERSIFIED
    assert minority.changes_selection


def test_an_excluded_claim_cannot_control_the_selection() -> None:
    """CAT's acceptance: the 2/2/1 stays excluded, and the retired
    one-in-twenty 'Service business' reading could only ever reach a
    refusal — never a silently different playbook."""

    selection = select_grounded(understand(diversified_shape()))

    assert isinstance(selection, PlaybookSelection)
    assert selection.playbook.kind is PlaybookKind.DIVERSIFIED

    contingency = selection.contingencies[0]

    assert not contingency.consumed

    service_reading = next(
        alternative
        for alternative in contingency.alternatives
        if alternative.concludes == "Service business, then manufacturer"
    )

    assert service_reading.selects is None
    assert service_reading.changes_selection


def test_alternatives_are_only_answers_some_observation_gave() -> None:
    """The no-synthesis rule reaches the selection layer intact."""

    understanding = understand(diversified_shape())
    selection = select_grounded(understanding)

    assert isinstance(selection, PlaybookSelection)

    observed = {
        answer.stated for answer in understanding.contingencies[0].agreement.answers
    }

    assert {
        alternative.answer for alternative in selection.contingencies[0].alternatives
    } == observed


# ── the refusals ────────────────────────────────────────────────────


def test_below_quorum_is_refused_with_the_count() -> None:
    refused = select_grounded(
        understand(consensus((segment("Only", share=0.95, earns=MFG),)))
    )

    assert isinstance(refused, RefusedGrounding)
    assert "below the quorum" in refused.because


def test_an_undecided_archetype_is_refused_with_its_own_reason() -> None:
    """META's acceptance: quorate, unexplained, and the refusal is the
    archetype's own absence, verbatim — never re-worded."""

    understanding = understand(unexplained_shape())
    refused = select_grounded(understanding)

    assert isinstance(refused, RefusedGrounding)
    assert refused.because == understanding.characteristics.undecided_because


def test_a_decided_but_unmapped_conclusion_is_refused_by_name() -> None:
    refused = select_grounded(understand(unmapped_shape()))

    assert isinstance(refused, RefusedGrounding)
    assert "'Service business'" in refused.because
    assert "not yet earned" in refused.because


def test_the_mapping_is_deterministic() -> None:
    first = select_grounded(understand(manufacturer_shape()))
    second = select_grounded(understand(manufacturer_shape()))

    assert first == second


def test_each_conclusion_maps_to_exactly_one_earned_playbook() -> None:
    """The door ambiguity would come through, held shut."""

    kinds = [rule.kind for rule in GROUNDED.values()]

    assert len(kinds) == len(set(kinds))
    assert all(kind in PLAYBOOKS for kind in kinds)


# ── the migration seam ──────────────────────────────────────────────


class FakeKnowledge:
    def __init__(self, outcome: KnowledgeOutcome) -> None:
        self._outcome = outcome

    async def knowledge(self, symbol: str) -> KnowledgeOutcome:
        return self._outcome


class NeverCalled:
    """A route that must not run; running it is the test failing."""

    def __getattr__(self, name: str):
        raise AssertionError("the industry route ran on the grounded path")


class FakeWatchlist:
    def __init__(self, item: object | None) -> None:
        self._item = item

    async def find_symbol(self, symbol: str) -> object | None:
        return self._item


class FakeFacts:
    async def build(self, item: object) -> object:
        return object()


class FakeProfiler:
    def profile(self, facts: object) -> object:
        return object()


class FakeIndustry:
    def select(self, profile: object):
        return PLAYBOOKS[PlaybookKind.BANK]


def known(knowledge) -> KnowledgeOutcome:
    return KnowledgeOutcome(
        state=KnowledgeState.AVAILABLE_CACHED,
        knowledge=knowledge,
    )


@pytest.mark.anyio
async def test_an_authoritative_selection_never_reaches_the_industry_route() -> None:
    service = PlaybookSelectionService(
        knowledge=FakeKnowledge(known(manufacturer_shape())),
        watchlist=NeverCalled(),
        facts=NeverCalled(),
        profiler=NeverCalled(),
        industry=NeverCalled(),
    )

    selection = await service.select("NVDA")

    assert selection.authoritative
    assert selection.selected_by is SelectedBy.BUSINESS_UNDERSTANDING


@pytest.mark.anyio
async def test_a_refused_grounding_falls_back_and_records_the_refusal() -> None:
    service = PlaybookSelectionService(
        knowledge=FakeKnowledge(known(unexplained_shape())),
        watchlist=FakeWatchlist(item=object()),
        facts=FakeFacts(),
        profiler=FakeProfiler(),
        industry=FakeIndustry(),
    )

    selection = await service.select("META")

    assert not selection.authoritative
    assert selection.selected_by is SelectedBy.REPORTED_INDUSTRY
    assert selection.playbook.kind is PlaybookKind.BANK
    assert selection.fallback_reason is not None
    assert "No segment of this business was shown to earn" in (
        selection.fallback_reason
    )


@pytest.mark.anyio
async def test_a_fallback_consumes_no_consensus_claim() -> None:
    """Never a hybrid: the industry route's selection carries nothing
    that traces to a filing, and the empty tuple is the proof."""

    service = PlaybookSelectionService(
        knowledge=FakeKnowledge(known(unexplained_shape())),
        watchlist=FakeWatchlist(item=object()),
        facts=FakeFacts(),
        profiler=FakeProfiler(),
        industry=FakeIndustry(),
    )

    selection = await service.select("META")

    assert selection.facts_consumed == ()
    assert selection.narrowest_agreement is None
    assert selection.rule_fired is None
    assert selection.contingencies == ()


@pytest.mark.anyio
async def test_no_knowledge_at_all_falls_back_with_the_absence() -> None:
    service = PlaybookSelectionService(
        knowledge=FakeKnowledge(
            KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                absent_because="No provider holds a source for this security.",
            )
        ),
        watchlist=FakeWatchlist(item=object()),
        facts=FakeFacts(),
        profiler=FakeProfiler(),
        industry=FakeIndustry(),
    )

    selection = await service.select("XYZ")

    assert not selection.authoritative
    assert selection.fallback_reason == (
        "No provider holds a source for this security."
    )


@pytest.mark.anyio
async def test_a_symbol_off_the_book_is_unclassified_not_guessed() -> None:
    service = PlaybookSelectionService(
        knowledge=FakeKnowledge(KnowledgeOutcome(state=KnowledgeState.UNAVAILABLE)),
        watchlist=FakeWatchlist(item=None),
        facts=NeverCalled(),
        profiler=NeverCalled(),
        industry=NeverCalled(),
    )

    selection = await service.select("XYZ")

    assert selection.playbook.kind is PlaybookKind.UNCLASSIFIED
    assert not selection.authoritative


# ------------------------------------------------------------------
# The pair rule: BNP Paribas's acceptance, and the case that keeps the
# key narrow.
# ------------------------------------------------------------------

BANKING = (RevenueModel.FINANCIAL_SPREAD, RevenueModel.SERVICES)
IPS_EARNS = (
    RevenueModel.ASSET_MANAGEMENT_FEES,
    RevenueModel.PREMIUMS,
    RevenueModel.SERVICES,
)
IPS_WITHOUT_SERVICES = (
    RevenueModel.ASSET_MANAGEMENT_FEES,
    RevenueModel.PREMIUMS,
)


def bank_shape():
    """BNP's accepted live shape: services covers every segment, lending
    covers the two that are banks — Service business, then lender."""

    def observation(ips_earns: tuple[RevenueModel, ...]):
        return (
            segment("CIB", share=0.37, earns=BANKING),
            segment("CPBS", share=0.52, earns=BANKING, row=2),
            segment("IPS", share=0.14, earns=ips_earns, row=3),
        )

    settled = observation(IPS_EARNS)
    minority = observation(IPS_WITHOUT_SERVICES)

    return consensus(settled, settled, settled, settled, minority)


def test_the_pair_rule_fires_where_lending_is_the_second_engine() -> None:
    """BNP's acceptance: a bank is analysed with a bank's playbook."""

    understanding = understand(bank_shape())

    assert understanding.characteristics.stated == "Service business, then lender"

    selection = select_grounded(understanding)

    assert isinstance(selection, PlaybookSelection)
    assert selection.playbook.kind is PlaybookKind.BANK
    assert selection.authoritative
    assert selection.rule_fired == "service-business-then-lender-activates-bank"
    assert selection.selected_by is SelectedBy.BUSINESS_UNDERSTANDING


def test_a_service_business_alone_is_still_refused() -> None:
    """
    The pair is the rule, not the primary. A business whose services
    lead and whose second engine is not lending has earned nothing, and
    serving a bank's playbook on the shared primary would be exactly
    the industry substitution this selector replaces.
    """

    def observation():
        return (
            segment("Consulting", share=0.70, earns=(RevenueModel.SERVICES,)),
            segment(
                "Licensing",
                share=0.30,
                earns=(RevenueModel.LICENSING, RevenueModel.SERVICES),
                row=2,
            ),
        )

    understanding = understand(consensus(*[observation()] * 5))

    assert understanding.characteristics.primary is Archetype.SERVICE_BUSINESS

    refused = select_grounded(understanding)

    assert isinstance(refused, RefusedGrounding)
    assert "has not yet earned a playbook mapping" in refused.because


def test_a_maker_with_a_captive_lender_keeps_the_industrial_playbook() -> None:
    """
    The corpus case that decided how narrow the key had to be.
    Caterpillar makes machines and lends against them; a rule keyed on
    "lending is a leading engine" would have handed a maker of
    excavators a bank's playbook. Keyed on the pair, the primary rule
    still answers.
    """

    def observation():
        # Lending large enough to *lead* as the runner-up, which is what
        # the pair key has to survive. A captive lender too small to lead
        # never reaches a secondary at all, so it could not test this.
        return (
            segment("Machines", share=0.60, earns=MFG),
            segment(
                "Financial Products",
                share=0.52,
                earns=(RevenueModel.FINANCIAL_SPREAD,),
                row=2,
            ),
        )

    understanding = understand(consensus(*[observation()] * 5))
    archetype = understanding.characteristics

    assert archetype.primary is Archetype.MANUFACTURER
    assert archetype.secondary is Archetype.LENDER

    selection = select_grounded(understanding)

    assert isinstance(selection, PlaybookSelection)
    assert selection.playbook.kind is PlaybookKind.INDUSTRIAL
    assert selection.rule_fired == "manufacturer-activates-industrial"


def test_a_pair_rule_is_consulted_before_the_primary_rule() -> None:
    """Precedence, stated as a property rather than inferred from a case."""

    assert (
        rule_for(Archetype.SERVICE_BUSINESS, Archetype.LENDER).kind is PlaybookKind.BANK
    )
    # Same primary, no runner-up: nothing earned.
    assert rule_for(Archetype.SERVICE_BUSINESS, None) is None
    # Same primary, a different runner-up: nothing earned.
    assert rule_for(Archetype.SERVICE_BUSINESS, Archetype.INSURER) is None
    # A primary rule is unaffected by any runner-up.
    assert (
        rule_for(Archetype.MANUFACTURER, Archetype.LENDER).kind
        is PlaybookKind.INDUSTRIAL
    )


def test_every_pair_key_is_a_genuine_pair() -> None:
    """A pair whose two halves are the same archetype is not a pair, and
    would be a primary rule wearing the more specific table's clothes."""

    assert all(primary is not secondary for primary, secondary in GROUNDED_PAIRS)
