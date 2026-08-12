"""The Fund Analytical Boundary (F1).

A fund cannot receive evaluative meaning from a company-specific
question its playbook does not ask. The acceptance case is IB01.L —
an accumulating US Treasury ETF whose only readable company-quality
field was Yahoo's `dividend_yield: 0.0`, and which rendered
"Business quality LOW (40)" from that single structural zero.

Every test here is a regression against a sentence the live dossier
actually showed on 2026-08-12, recorded in
`docs/architecture/FUND_EVIDENCE_RESEARCH.md`.
"""

import asyncio
from datetime import UTC, datetime

from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.cio.artificial_cio import ArtificialCIO
from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.dossier_definition import definition_for
from app.domain.market_snapshot import MarketQuote
from app.domain.momentum_signal import MomentumSignal
from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.value_provider import ValueProvider
from app.providers.yahoo_market_provider import YahooInstrument
from app.services.company_facts_service import CompanyFactsService
from app.services.playbook_selector import PlaybookSelector
from app.services.quality_signal_service import QualitySignalService
from app.services.value_signal_service import ValueSignalService


def fund_item() -> WatchlistItem:
    """IB01.L as the watchlists actually carry it: eToro asset type 6."""

    return WatchlistItem(
        instrument_id=1442,
        symbol="IB01.L",
        name="iShares $ Treasury Bond 0-1yr UCITS ETF",
        asset_type_id=6,
        asset_type_subcategory_id=0,
        exchange_id=7,
        rank=1,
        avatar_url=None,
    )


class StubMarketProvider:
    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        return (
            MarketQuote(
                symbol="IB01.L",
                name="iShares $ Treasury Bond 0-1yr UCITS ETF",
                price=121.4,
                change_percent=0.02,
            ),
        )


class StubValuationProvider:
    def __init__(self, snapshot: ValuationSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        return self._snapshot


class StubEarningsProvider:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def read(self, symbol: str) -> object:
        self.asked.append(symbol)
        raise AssertionError("a fund must never be asked for earnings")


def fund_facts(
    snapshot: ValuationSnapshot,
) -> tuple[CompanyFacts, StubEarningsProvider]:
    earnings = StubEarningsProvider()

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(snapshot),  # type: ignore[arg-type]
        earnings_provider=earnings,  # type: ignore[arg-type]
    )

    return asyncio.run(service.build(fund_item())), earnings


#: The provider payload the live defect arrived on: dividend 0.0 the only
#: readable quality field — plus the fields Yahoo *could* someday answer
#: for a fund, which must be equally incapable of scoring it.
LIVE_DEFECT_SNAPSHOT = ValuationSnapshot(
    forward_pe=None,
    trailing_pe=None,
    peg_ratio=None,
    dividend_yield=0.0,
    expense_ratio=0.0007,
    reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
)


# ── Outcome 1 + 2: no company-quality judgment, from any field ────────


def test_a_zero_dividend_cannot_recreate_low_quality_for_a_fund() -> None:
    """The acceptance regression: IB01.L's exact defect, replayed."""

    facts, _ = fund_facts(LIVE_DEFECT_SNAPSHOT)

    signal = QualitySignalService().build(facts, AssetClass.ETF)

    assert signal.quality == "UNKNOWN"
    assert signal.contributions == ()
    assert signal.earned == 0
    assert "No dividend." not in [f.statement for f in signal.evidence]


def test_no_company_field_scores_a_fund_even_when_populated() -> None:
    """Size and earnings are company questions; a fund is not asked them.

    A fund's `marketCap` is an AUM-shaped figure wearing a company
    field's name — counted, it would make a large fund a "large-cap
    company", the Bitcoin defect with a wrapper on.
    """

    generous = ValuationSnapshot(
        forward_pe=12.0,
        trailing_pe=11.0,
        peg_ratio=1.0,
        dividend_yield=0.03,
        market_cap=500_000_000_000.0,
        eps=4.2,
    )

    signal = QualitySignalService().build(
        CompanyFacts(
            instrument_id=1442,
            symbol="IB01.L",
            name="iShares $ Treasury Bond 0-1yr UCITS ETF",
            asset_type="etf",
            exchange="7",
            market_cap=generous.market_cap,
            eps=generous.eps,
            dividend_yield=generous.dividend_yield,
        ),
        AssetClass.ETF,
    )

    assert signal.quality == "UNKNOWN"
    assert signal.contributions == ()
    assert signal.basis is not None
    assert "does not ask" in signal.basis


def test_the_company_path_is_untouched_by_the_boundary() -> None:
    """A stock with the same zero dividend still counts its factors."""

    signal = QualitySignalService().build(
        CompanyFacts(
            instrument_id=1,
            symbol="MSFT",
            name="Microsoft",
            asset_type="stock",
            exchange="4",
            market_cap=3_000_000_000_000.0,
            eps=12.5,
            dividend_yield=0.0,
        ),
        AssetClass.STOCK,
    )

    assert signal.quality == "MEDIUM"
    assert signal.earned == 2


def test_fund_facts_carry_no_company_fields_however_populated() -> None:
    """The dividend zero never reaches the facts a signal could read."""

    populated = ValuationSnapshot(
        forward_pe=12.0,
        trailing_pe=11.0,
        peg_ratio=1.0,
        dividend_yield=0.0,
        eps=4.2,
        revenue_growth=0.1,
        net_margin=0.2,
        sector="Financial Services",
        industry="Asset Management",
        expense_ratio=0.0007,
    )

    facts, earnings = fund_facts(populated)

    assert facts.dividend_yield is None
    assert facts.eps is None
    assert facts.forward_pe is None
    assert facts.revenue_growth is None
    assert facts.net_margin is None
    assert facts.sector is None

    # A fund is not a token either: no supply figure may be read out of
    # the payload merely because the fund is not a company.
    assert facts.circulating_supply is None
    assert facts.max_supply is None

    # Outcome 7: the one fund-shaped fact is retained rather than
    # discarded — and it is the only fundamentals field a fund carries.
    assert facts.expense_ratio == 0.0007

    # Outcome 6: the earnings calendar was never asked (the stub raises).
    assert earnings.asked == []


def test_expense_ratio_stays_absent_off_the_fund_path() -> None:
    """A company never carries the fund's field, even if a provider sent it."""

    snapshot = ValuationSnapshot(
        forward_pe=21.5,
        trailing_pe=24.1,
        peg_ratio=1.4,
        dividend_yield=0.012,
        expense_ratio=0.0095,
    )

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(snapshot),  # type: ignore[arg-type]
        earnings_provider=None,
    )

    item = WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )

    facts = asyncio.run(service.build(item))

    assert facts.expense_ratio is None
    assert facts.dividend_yield == 0.012


def test_the_provider_reads_the_expense_ratio_as_a_ratio() -> None:
    """Yahoo reports percent (0.07 for 0.07%); the snapshot holds a ratio."""

    snapshot = ValueProvider.from_info({"netExpenseRatio": 0.07})

    assert snapshot.expense_ratio is not None
    assert abs(snapshot.expense_ratio - 0.0007) < 1e-12


# ── Outcome 3: an unavailable valuation is not the next thing needed ──


def fund_recommendation() -> CompanyRecommendation:
    """A fund's signals as the boundary now produces them."""

    quality = QualitySignalService().build(
        CompanyFacts(
            instrument_id=1442,
            symbol="IB01.L",
            name="iShares $ Treasury Bond 0-1yr UCITS ETF",
            asset_type="etf",
            exchange="7",
        ),
        AssetClass.ETF,
    )

    value = ValueSignalService().build(
        CompanyFacts(
            instrument_id=1442,
            symbol="IB01.L",
            name="iShares $ Treasury Bond 0-1yr UCITS ETF",
            asset_type="etf",
            exchange="7",
        ),
        AssetClass.ETF,
    )

    signals = CompanySignals(
        value=value,
        momentum=MomentumSignal(
            trend="NEUTRAL",
            strength="WEAK",
            confidence=50,
            evidence=(),
        ),
        quality=quality,
        risk=None,
        research=None,
    )

    return CompanyRecommendation(
        symbol="IB01.L",
        recommendation="HOLD",
        confidence=50,
        summary="",
        signals=signals,
        evidence=(),
    )


def test_unavailable_valuation_is_not_the_funds_next_thing_needed() -> None:
    """The dossier's review condition was "Valuation data is unavailable
    for IB01.L" with "Measuring it is what would let this case progress"
    — a promise no fund can be kept. Neither sentence may return."""

    missing = DecisionEvidenceBuilder._missing_evidence(
        fund_recommendation(),
        "IB01.L",
        AssetClass.ETF,
    )

    assert not any("Valuation data is unavailable" in line for line in missing)
    assert not any("Quality data is unavailable" in line for line in missing)


def test_the_cio_states_the_platform_limit_for_a_fund() -> None:
    """The same honest wording crypto earned, reached through the same
    capability boundary rather than a presentation special case."""

    class Evidence:
        asset_class = AssetClass.ETF

    quality_reason = ArtificialCIO._unassessable_quality(Evidence())  # type: ignore[arg-type]
    valuation_reason = ArtificialCIO._unassessable_valuation(Evidence())  # type: ignore[arg-type]

    assert "A fund has no business quality or valuation to assess" in quality_reason
    assert "no recommendation rests on them alone" in quality_reason
    assert "fund" in valuation_reason
    assert "unavailable" not in quality_reason
    assert "unavailable" not in valuation_reason


def test_the_valuation_basis_carries_the_signals_own_account() -> None:
    """Asked to explain a fund's UNKNOWN, the builder must not say the
    figures "could not be read" — nothing is going to become readable."""

    basis = DecisionEvidenceBuilder._valuation_basis(fund_recommendation())

    assert "could not be read" not in basis.basis
    assert "no earnings to be priced against" in basis.basis


def test_the_quality_basis_carries_the_signals_own_account() -> None:
    basis = DecisionEvidenceBuilder._quality_basis(fund_recommendation())

    assert "could not be read" not in basis.basis
    assert "does not ask" in basis.basis


# ── Outcomes 4 + 5: one precise platform limit, no company labels ─────


def test_the_fund_dossier_states_the_platform_limit_for_filings() -> None:
    definition = definition_for(AssetClass.ETF)

    assert definition.filings_apply is False
    assert definition.filings_inapplicable_because is not None

    reason = definition.filings_inapplicable_because

    # The limit is this platform's. No claim about what funds publish —
    # in either direction — and no promise of a reading to come.
    assert "not part of the fund playbook" in reason
    assert "limit of this platform" in reason
    assert "publishes no" not in reason
    assert "not yet" not in reason
    assert "movrvest observe" not in reason


def test_no_fund_surface_is_labelled_business_quality() -> None:
    definition = definition_for(AssetClass.ETF)

    assert definition.score_labels["quality"] == "Asset quality"


def test_a_fund_is_still_served_the_general_dossier() -> None:
    """Outcome 8: no fund dossier kind was built in this slice."""

    definition = definition_for(AssetClass.ETF)

    assert definition.kind.value == "general"
    assert definition.title == "Investment dossier"


# ── Outcome 6: the honest behaviour is preserved ──────────────────────


def test_the_fund_playbook_is_still_selected_from_identity() -> None:
    from app.domain.company_profile import CompanyProfile, Sector

    playbook = PlaybookSelector().select(
        CompanyProfile(
            asset_class=AssetClass.ETF,
            sector=Sector.OTHER,
            industry=None,
        )
    )

    assert playbook.kind.value == "fund"
    assert playbook.analysts == ()
    assert len(playbook.excluded) == 4


def test_the_committee_never_says_never_and_not_yet_together() -> None:
    """The Investment Committee declared a fund's business quality both
    outside its knowledge ("can never answer") and an absent measurement
    ("could not be read") — a contradiction the surface rendered
    faithfully. The unanswerable questions are not inputs at all."""

    from app.application.committees.investment_committee import (
        InvestmentCommittee,
    )
    from app.domain.finding import FindingLedger

    recommendation = fund_recommendation()

    class StubBrain:
        def security_evidence(self, symbol: str) -> CompanyRecommendation:
            return recommendation

        def asset_class_for(self, symbol: str) -> AssetClass:
            return AssetClass.ETF

    opinion = InvestmentCommittee().review(
        StubBrain(),  # type: ignore[arg-type]
        "IB01.L",
        FindingLedger.of(()),
    )

    worded = [item.about for item in opinion.uncertainty]

    assert any("question this committee can ever answer" in text for text in worded)
    assert not any("could not be read" in text for text in worded)


def test_the_boundary_membership_is_exactly_three_classes() -> None:
    """UNKNOWN stays out: saying an unclassified thing has no business
    would assert something nobody established."""

    assert AssetClass.ETF.has_no_company
    assert AssetClass.CRYPTO.has_no_company
    assert AssetClass.COMMODITY.has_no_company
    assert not AssetClass.STOCK.has_no_company
    assert not AssetClass.UNKNOWN.has_no_company

    # And the two capability properties stay independent: asking the
    # provider about a fund is meaningful — that is where its price,
    # risk history and expense ratio come from.
    assert AssetClass.ETF.has_company_fundamentals
