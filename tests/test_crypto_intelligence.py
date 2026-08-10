"""The first Crypto Intelligence slice: what is happening, and why it matters.

One test per acceptance criterion. The two that matter most cannot be
read off the code: that a brief renders for an asset whose Asset Quality
is UNKNOWN, and that a provider paragraph decomposes into claims of
different epistemic kinds rather than entering as one fact.

**Nothing here reads the live store or the network.** Every case runs on
readings recorded on 2026-08-10, pushed through the real service.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.asset_class import AssetClass
from app.domain.crypto_intelligence import (
    ClaimType,
    Direction,
    EventKind,
    IntelligenceClaim,
    Relevance,
    relevance_of,
)
from app.domain.crypto_market import (
    CryptoMarketSnapshot,
    MarketInterval,
    MarketMetric,
    MarketObservation,
)
from app.domain.crypto_market_context import CryptoMarketContext
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import ProtocolMetric
from app.domain.provenance import Provenance
from app.providers.defillama_provider import ProtocolClaimSet, ProtocolMetricClaim
from app.providers.etf_flow_provider import EtfFlowReading, TreasuryHolding
from app.services.crypto_intelligence_service import CryptoIntelligenceService
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
from tests.reachability import reachable

NOW = datetime(2026, 8, 10, 16, 0, tzinfo=UTC)
READ = datetime(2026, 8, 10, 10, 20, tzinfo=UTC)


# ── the recorded readings ───────────────────────────────────────────

_RETURNS = {
    "BTC": {"24h": 0.2, "7d": 3.9, "30d": 1.1},
    "ETH": {"24h": 0.0, "7d": 4.2, "30d": 6.4},
    "HYPE": {"24h": -0.2, "7d": 3.9, "30d": -18.0},
}

_FLOWS = {
    "BTC": EtfFlowReading(
        symbol="BTC",
        group="us-btc-spot",
        source="SoSoValue",
        as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
        observed_at=READ,
        daily_net_flow=98_845_326.995,
        total_net_assets=79_497_427_558.3,
        token_holdings=1_223_633.43623625,
        share_of_supply=0.06097325,
        cumulative_net_flow=52_196_491_735.47,
        flow_5d=853_535_547.0,
        flow_30d=127_718_020.0,
        inflow_days_30d=18,
        days_counted_30d=30,
    ),
    "ETH": EtfFlowReading(
        symbol="ETH",
        group="us-eth-spot",
        source="SoSoValue",
        as_of=datetime(2026, 8, 7, tzinfo=UTC).date(),
        observed_at=READ,
        daily_net_flow=49_601_034.6,
        total_net_assets=10_743_698_230.46,
        token_holdings=5_610_841.91240732,
        share_of_supply=0.04649276,
        flow_5d=244_939_122.0,
        flow_30d=539_615_811.0,
        inflow_days_30d=21,
        days_counted_30d=30,
    ),
}

_TREASURIES = {
    "BTC": TreasuryHolding(
        symbol="BTC",
        source="CoinGecko",
        observed_at=READ,
        companies=179,
        total_holdings=1_282_500.93,
        total_value_usd=82_461_500_546.52,
    ),
    "ETH": TreasuryHolding(
        symbol="ETH",
        source="CoinGecko",
        observed_at=READ,
        companies=33,
        total_holdings=7_818_592.23,
        total_value_usd=14_669_579_254.78,
    ),
}

_PROTOCOL: dict[str, ProtocolClaimSet] = {
    "bitcoin-chain": ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.FEES, 139_032.0, "24 hours"),),
        defines=frozenset({ProtocolMetric.FEES}),
    ),
    "ethereum-chain": ProtocolClaimSet(
        entity_key="ethereum-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 175_154.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                32_159.0,
                "24 hours",
                methodology="Amount of ETH burned — base fees plus blob fees",
            ),
        ),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.HOLDER_REVENUE}),
    ),
    "hyperliquid-protocol": ProtocolClaimSet(
        entity_key="hyperliquid-protocol",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 842_720.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                534_851.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: 99% of fees go to Assistance Fund "
                    "for buying HYPE tokens"
                ),
            ),
            ProtocolMetricClaim(ProtocolMetric.OPEN_INTEREST, 10_865_754_650.0, None),
        ),
        defines=frozenset(ProtocolMetric),
    ),
}


class _Market:
    """S4's context, recorded. Its arithmetic is not re-done here."""

    @staticmethod
    def context(symbol: str, asset_class: AssetClass | None) -> object | None:
        if asset_class is not AssetClass.CRYPTO or symbol not in _RETURNS:
            return None

        returns = tuple(
            MarketObservation(
                metric=MarketMetric.ASSET_RETURN,
                interval=MarketInterval(interval),
                standing=EvidenceStanding.CLAIMED,
                value=value,
                source="CoinGecko",
                observed_at=READ,
            )
            for interval, value in _RETURNS[symbol].items()
        )

        return CryptoMarketContext(
            symbol=symbol,
            snapshot=CryptoMarketSnapshot(observed_at=READ, source="CoinGecko"),
            returns=returns,
            relative=(),
        )


class _Flows:
    @staticmethod
    def flows(symbol: str) -> EtfFlowReading | None:
        return _FLOWS.get(symbol.upper())

    @staticmethod
    def treasuries(symbol: str) -> TreasuryHolding | None:
        return _TREASURIES.get(symbol.upper())


class _NoFlows:
    @staticmethod
    def flows(symbol: str) -> None:
        return None

    @staticmethod
    def treasuries(symbol: str) -> None:
        return None


class _Claims:
    @staticmethod
    def claim_set(entity_key: str) -> ProtocolClaimSet | None:
        return _PROTOCOL.get(entity_key)


class _NoSupply:
    @staticmethod
    def established(symbol: str, asset_class: AssetClass | None) -> None:
        return None


class _NoFacts:
    @staticmethod
    def established(symbol: str, name: str, asset_class: AssetClass | None) -> None:
        return None


def _service(flows: object | None = None) -> CryptoIntelligenceService:
    return CryptoIntelligenceService(
        facts=_NoFacts(),  # type: ignore[arg-type]
        market=_Market(),  # type: ignore[arg-type]
        protocol=ProtocolFundamentalsService(sources=(_Claims(),)),
        supply=_NoSupply(),  # type: ignore[arg-type]
        flows=flows or _Flows(),  # type: ignore[arg-type]
    )


def _snapshot(symbol: str, flows: object | None = None):  # type: ignore[no-untyped-def]
    outcome = _service(flows).snapshot(symbol, AssetClass.CRYPTO, now=NOW)

    assert outcome is not None

    return outcome


# ── 1: Asset Quality does not gate intelligence ─────────────────────


def test_asset_quality_cannot_reach_the_intelligence_layer() -> None:
    """Acceptance 1, made structural.

    Every crypto asset currently reads UNKNOWN. If the intelligence
    layer could see that, the product would have nothing to say about
    Bitcoin — which is the entire reason this layer exists.
    """

    for module in (
        "app/domain/crypto_intelligence.py",
        "app/services/crypto_intelligence_service.py",
        "app/commands/intelligence_brief.py",
    ):
        code = reachable(module)

        for forbidden in ("crypto_quality", "quality_signal", "asset_quality"):
            assert forbidden not in code, (module, forbidden)


def test_a_brief_renders_while_quality_is_unknown() -> None:
    """The same assertion from the other side: it actually works."""

    from app.services.crypto_asset_quality_service import CryptoAssetQualityService

    quality = CryptoAssetQualityService().established("BTC", AssetClass.CRYPTO)

    assert quality is not None
    assert quality.quality == "UNKNOWN"

    assert _snapshot("BTC").is_useful


# ── 2, 3, 4: three assets, three different briefs ───────────────────


def test_btc_gets_flows_and_holdings() -> None:
    snapshot = _snapshot("BTC")

    kinds = {claim.kind for claim in snapshot.claims}

    assert EventKind.CAPITAL_FLOW in kinds
    assert EventKind.INSTITUTIONAL_HOLDING in kinds
    assert EventKind.MARKET_BEHAVIOUR in kinds

    assert snapshot.tailwinds


def test_eth_is_not_a_copy_of_btc() -> None:
    """Acceptance 3. ETH's burn reaches holders; Bitcoin's fees do not.

    The difference comes from the protocol evidence, not from a branch
    on the symbol.
    """

    btc = {claim.ref for claim in _snapshot("BTC").claims}
    eth = {claim.ref for claim in _snapshot("ETH").claims}

    accrual = {ref for ref in eth if "holder_revenue" in ref}

    assert accrual
    assert not {ref for ref in btc if "holder_revenue" in ref}

    assert any(
        "reaching the token" in driver.stated for driver in _snapshot("ETH").drivers
    )


def test_hype_gets_no_etf_concepts_and_is_not_penalised_for_it() -> None:
    """Acceptance 4.

    No fund group is mapped, so no flow claim exists — and *nothing* in
    the snapshot says it is missing one. An absent question is not an
    unmet demand.
    """

    snapshot = _snapshot("HYPE", flows=_NoFlows())

    assert snapshot.is_useful

    for claim in snapshot.claims:
        assert claim.kind is not EventKind.CAPITAL_FLOW

    rendered = " ".join(claim.stated for claim in snapshot.claims).casefold()

    assert "etf" not in rendered

    # It has venue economics instead, which is what it actually has.
    assert any("held open" in claim.stated for claim in snapshot.claims)


def test_the_difference_is_not_a_symbol_check() -> None:
    """The architecture claim, tested.

    Hand Hyperliquid a fund group and it gets flow claims; the service
    branches on the evidence, never on the ticker.
    """

    class _HypeFlows:
        @staticmethod
        def flows(symbol: str) -> EtfFlowReading:
            return _FLOWS["BTC"]

        @staticmethod
        def treasuries(symbol: str) -> None:
            return None

    snapshot = _snapshot("HYPE", flows=_HypeFlows())

    assert any(claim.kind is EventKind.CAPITAL_FLOW for claim in snapshot.claims)


# ── 5, 6: epistemics ────────────────────────────────────────────────


def test_the_epistemic_types_are_carried_apart() -> None:
    """Acceptance 5 and 6.

    A brief holds measurements, reported facts and this platform's own
    readings at once, and every one says which it is.
    """

    snapshot = _snapshot("BTC")

    kinds = {claim.claim_type for claim in snapshot.claims}

    assert ClaimType.REPORTED in kinds
    assert ClaimType.MEASURED in kinds

    # The rolling sum is this platform's arithmetic and says so.
    rolling = snapshot.claim("flow.30d")

    assert rolling is not None
    assert rolling.claim_type is ClaimType.MEASURED
    assert "MOVRvest" in rolling.source

    # The day's flow is the source's, and it is not a measurement here.
    daily = snapshot.claim("flow.daily")

    assert daily is not None
    assert daily.claim_type is ClaimType.REPORTED
    assert daily.source == "SoSoValue"

    # And a driver that interprets is marked as an interpretation.
    inferred = [
        driver for driver in snapshot.drivers if driver.support.value == "inferred"
    ]

    assert inferred


def test_a_provider_paragraph_decomposes_into_four_kinds_of_claim() -> None:
    """Acceptance 6, on the ruling's own example sentence.

    *"ETF inflows are supporting Bitcoin while institutional interest
    remains high"* is not one fact. It is a reported flow, a measured
    price state, an inferred reading of holdings, and an attributed
    causal link — and only the last belongs to whoever said it.

    No narrative source is acquired in this slice, so this demonstrates
    the vocabulary rather than an integration. The types exist and hold
    the distinction; wiring a narrative provider is the next slice.
    """

    decomposed = (
        IntelligenceClaim(
            ref="narrative.flow",
            kind=EventKind.CAPITAL_FLOW,
            claim_type=ClaimType.REPORTED,
            stated="US spot BTC ETFs took $99m net on 7 August.",
            source="SoSoValue",
            authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
            standing=EvidenceStanding.CLAIMED,
            relevance=Relevance.RECENT,
        ),
        IntelligenceClaim(
            ref="narrative.price",
            kind=EventKind.MARKET_BEHAVIOUR,
            claim_type=ClaimType.MEASURED,
            stated="BTC returned +1.1% over 30 days.",
            source="MOVRvest",
            authority=EvidenceAuthority.SECONDARY_COMPUTATION,
            standing=EvidenceStanding.CLAIMED,
            relevance=Relevance.CURRENT,
        ),
        IntelligenceClaim(
            ref="narrative.institutional",
            kind=EventKind.INSTITUTIONAL_HOLDING,
            claim_type=ClaimType.INFERRED,
            stated="Institutional participation is material.",
            source="MOVRvest, from fund and treasury holdings",
            authority=EvidenceAuthority.SECONDARY_COMPUTATION,
            standing=EvidenceStanding.CLAIMED,
            relevance=Relevance.STRUCTURAL,
        ),
        IntelligenceClaim(
            ref="narrative.causal",
            kind=EventKind.MARKET_NARRATIVE,
            claim_type=ClaimType.ATTRIBUTED,
            stated="Inflows are supporting the price.",
            source="the publishing provider",
            authority=EvidenceAuthority.ATTRIBUTED_OPINION,
            standing=EvidenceStanding.CLAIMED,
            relevance=Relevance.CURRENT,
        ),
    )

    assert len({claim.claim_type for claim in decomposed}) == 4

    facts = [claim for claim in decomposed if claim.claim_type.is_fact]
    opinions = [claim for claim in decomposed if not claim.claim_type.is_fact]

    assert len(facts) == 2
    assert len(opinions) == 2

    # The causal link is the source's, never this platform's.
    causal = decomposed[-1]

    assert causal.claim_type is ClaimType.ATTRIBUTED
    assert causal.authority is EvidenceAuthority.ATTRIBUTED_OPINION


# ── 7: recency ──────────────────────────────────────────────────────


def test_a_claim_ages_out_of_being_current() -> None:
    """Acceptance 7. Intelligence is perishable, and says when it has perished."""

    assert relevance_of(NOW, NOW) is Relevance.CURRENT
    assert relevance_of(NOW - timedelta(days=4), NOW) is Relevance.RECENT
    assert relevance_of(NOW - timedelta(days=30), NOW) is Relevance.STALE
    assert relevance_of(None, NOW) is Relevance.STALE

    # A holdings level is a condition rather than a change.
    assert (
        relevance_of(NOW - timedelta(days=20), NOW, structural=True)
        is Relevance.STRUCTURAL
    )

    stale = _service().snapshot("BTC", AssetClass.CRYPTO, now=NOW + timedelta(days=60))

    assert stale is not None
    assert not stale.live
    assert stale.thin_because is not None


# ── 10, 11: grounding and the deterministic floor ───────────────────


def test_every_driver_resolves_to_claims_the_snapshot_holds() -> None:
    """Acceptance 10, as a property rather than a promise.

    A driver referencing a claim that is not here would be a sentence
    with no evidence behind it — which is exactly what a writer must be
    unable to produce.
    """

    for symbol in ("BTC", "ETH", "HYPE"):
        snapshot = _snapshot(symbol, flows=None if symbol != "HYPE" else _NoFlows())

        assert snapshot.grounded

        for driver in snapshot.drivers:
            assert driver.claims

            for ref in driver.claims:
                assert snapshot.claim(ref) is not None


def test_the_whole_brief_renders_with_no_model_at_all() -> None:
    """Acceptance 11. The deterministic layer is the implementation,
    not a fallback bolted beside one — no writer is wired in this slice."""

    code = reachable("app/commands/intelligence_brief.py")

    for forbidden in ("writer", "openai", "anthropic", "llm", "prompt"):
        assert forbidden not in code, forbidden

    from app.commands.intelligence_brief import IntelligenceBriefCommand

    assert IntelligenceBriefCommand().run("BTC") == 0


# ── 12, 13, 14: nothing else moved ──────────────────────────────────


def test_no_decision_or_quality_behaviour_changed() -> None:
    """Acceptance 12, 13 and 14.

    The layer is visible and decision-neutral: nothing that decides can
    reach it, so it cannot move a recommendation by accident.
    """

    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent

    for target in (
        "app/cio",
        "app/application/executive",
        "app/services/company_signal_service.py",
        "app/services/quality_signal_service.py",
        "app/domain/crypto_quality.py",
    ):
        path = root / target

        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]

        for source in files:
            text = source.read_text(encoding="utf-8")

            assert "crypto_intelligence" not in text, source
            assert "etf_flow_provider" not in text, source

    from app.domain.crypto_quality import MINIMUM_SCORED, RULES

    assert MINIMUM_SCORED == 2
    assert len(RULES) == 1


def test_conflicting_signals_are_held_rather_than_resolved() -> None:
    """Acceptance for the ruling's twelfth section.

    Hyperliquid earns for its holders and is down 18% over a month. The
    brief states both as tension rather than picking a label.
    """

    snapshot = _snapshot("HYPE", flows=_NoFlows())

    assert snapshot.tailwinds
    assert snapshot.headwinds
    assert snapshot.conflicting

    assert any("At the same time" in line for line in snapshot.conflicting)


def test_a_driver_states_a_consequence_only_where_evidence_carries_one() -> None:
    """`matters_because` is absent rather than invented.

    A pure observation — the asset moved 18% — gets no consequence,
    because nothing here establishes what the move means.
    """

    snapshot = _snapshot("HYPE", flows=_NoFlows())

    movement = [d for d in snapshot.drivers if "moved" in d.stated]

    assert movement
    assert movement[0].matters_because is None
    assert movement[0].direction is Direction.ADVERSE
