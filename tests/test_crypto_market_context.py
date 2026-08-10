"""S4: what kind of crypto market an asset is trading inside.

One test per acceptance criterion in the ruling, plus the structural
guards. The two that cannot be checked by reading the code are that
relative arithmetic refuses misaligned intervals, and that no asset
liquidity figure and no global volume figure can ever meet.

**Nothing here reads the live store or the network.** Every case runs on
the recorded cycle below — the figures CoinGecko returned on 2026-08-10,
including the ones that made the design decisions — pushed through the
real service. A test that consulted `data/cache` would pass on this
machine, fail in CI, and change its own subject the next time
`movrvest acquire` ran.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.crypto_market import (
    MEASURES,
    MarketInterval,
    MarketMetric,
    MarketObservation,
    MarketPeriodicity,
    MarketUnit,
    relative_return,
)
from app.domain.evidence_standing import EvidenceStanding
from app.domain.market_peer_group import (
    PEER_GROUPS,
    acquired_groups,
    peer_group_for,
)
from app.domain.provenance import Provenance
from app.providers.coingecko_market_provider import (
    AssetReturnClaim,
    CategoryClaim,
    MarketClaimSet,
    MarketStateClaim,
    UniverseClaim,
)
from app.services.crypto_market_service import CryptoMarketService

CORPUS = ("BTC", "ETH", "SOL", "ADA", "ARB", "1INCH", "HYPE", "TAO")


def _code(module: str) -> str:
    """A module's identifiers and literal values, without its prose.

    Every guard below asks what a module can *reach*, never what it
    mentions. `market_peer_group` says in as many words that it must not
    see an archetype, and a raw text search would forbid it from saying
    so — the same lesson S3 learned about naming the rater it refuses.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    tree = ast.parse((root / module).read_text(encoding="utf-8"))

    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
    }

    words: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            words.append(node.id)
        elif isinstance(node, ast.Attribute):
            words.append(node.attr)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            words.append(node.name)
        elif isinstance(node, ast.alias):
            words.append(node.name)
            words.append(node.asname or "")
        elif isinstance(node, ast.ImportFrom):
            words.append(node.module or "")
        elif isinstance(node, ast.arg):
            words.append(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                words.append(node.value)

    return "\n".join(words)


READ = datetime(2026, 8, 10, 10, 20, tzinfo=UTC)


#: CoinGecko's answers on 2026-08-10, as the measurement recorded them.
#:
#: Two figures here are the reason the design is what it is. The
#: provider's aggregate capitalisation moved +0.051% while the
#: capitalisation-weighted return of its 250 largest assets was +0.113%,
#: and the Layer 1 category's aggregate moved +0.046% while its members'
#: weighted return was +0.150% — a factor of three. The first is not a
#: return, and only the second may be subtracted from an asset's.
def _recorded() -> MarketClaimSet:
    return MarketClaimSet(
        source="CoinGecko",
        read=Provenance(source="CoinGecko", observed_at=READ),
        state=MarketStateClaim(
            total_market_cap=2_300_918_318_489.9,
            total_volume=39_514_925_001.1,
            market_cap_change_24h=0.051038033285026735,
            volume_change_24h=21.03352322863359,
            btc_dominance=56.67781862843528,
            eth_dominance=10.054778096162018,
            stablecoin_share=11.09022610968778,
            tracked_assets=18_325.0,
        ),
        universe=UniverseClaim(
            key="coingecko-top-250",
            described=(
                "the 250 largest assets by market capitalisation as "
                "CoinGecko ranks them, read in one page"
            ),
            counted=250,
            weighted_return_24h=0.11274692290518916,
            advancing=98,
            declining=97,
            market_cap=2_280_941_984_325.0,
        ),
        categories=(
            CategoryClaim(
                key="layer-1",
                name="Layer 1 (L1)",
                market_cap=1_846_665_287_647.6,
                market_cap_change_24h=0.04627309341487906,
                volume_24h=24_780_600_492.0,
            ),
            CategoryClaim(
                key="decentralized-perpetuals",
                name="Perpetuals",
                market_cap=16_472_037_057.8,
                market_cap_change_24h=-0.5080801407035955,
                volume_24h=509_000_000.0,
            ),
            CategoryClaim(
                key="rollup",
                name="Rollup",
                market_cap=1_384_060_479.2,
                market_cap_change_24h=1.1746742140308548,
                volume_24h=141_778_353.0,
            ),
            CategoryClaim(
                key="dex-aggregator",
                name="Dex Aggregator",
                market_cap=871_528_572.7,
                market_cap_change_24h=-0.42960040235237634,
                volume_24h=70_713_559.0,
            ),
        ),
        assets=(
            AssetReturnClaim(
                symbol="BTC",
                provider_id="bitcoin",
                market_cap=1_303_848_053_636.0,
                returns={"1h": -0.4, "24h": 0.2, "7d": 3.9, "30d": 1.1},
            ),
            AssetReturnClaim(
                symbol="ETH",
                provider_id="ethereum",
                market_cap=231_426_574_644.0,
                returns={"1h": -0.5, "24h": 0.0, "7d": 4.2, "30d": 6.4},
            ),
            AssetReturnClaim(
                symbol="SOL",
                provider_id="solana",
                market_cap=44_543_865_033.0,
                returns={"1h": -0.4, "24h": 0.3, "7d": 5.9, "30d": -2.0},
            ),
            AssetReturnClaim(
                symbol="ADA",
                provider_id="cardano",
                market_cap=7_272_989_671.0,
                returns={"1h": -0.6, "24h": -1.3, "7d": 6.2, "30d": 16.3},
            ),
            AssetReturnClaim(
                symbol="ARB",
                provider_id="arbitrum",
                market_cap=525_269_066.0,
                returns={"1h": -0.2, "24h": 3.3, "7d": -1.3, "30d": -12.3},
            ),
            AssetReturnClaim(
                symbol="1INCH",
                provider_id="1inch",
                market_cap=118_357_112.0,
                returns={"1h": 0.0, "24h": 0.4, "7d": 5.1, "30d": 15.9},
            ),
            AssetReturnClaim(
                symbol="HYPE",
                provider_id="hyperliquid",
                market_cap=12_102_933_796.0,
                returns={"1h": -0.3, "24h": -0.2, "7d": 3.9, "30d": -18.0},
            ),
            AssetReturnClaim(
                symbol="TAO",
                provider_id="bittensor",
                market_cap=1_948_137_647.0,
                returns={"1h": -0.5, "24h": -1.8, "7d": 7.7, "30d": -4.8},
            ),
        ),
        category_universes={
            "layer-1": UniverseClaim(
                key="layer-1",
                described="the largest members of CoinGecko's layer-1 category",
                counted=100,
                weighted_return_24h=0.14957382384674564,
                advancing=44,
                declining=48,
                market_cap=1_845_264_244_245.0,
            ),
            "decentralized-perpetuals": UniverseClaim(
                key="decentralized-perpetuals",
                described=(
                    "the largest members of CoinGecko's "
                    "decentralized-perpetuals category"
                ),
                counted=100,
                weighted_return_24h=0.0029014588144428066,
                advancing=51,
                declining=46,
                market_cap=16_486_797_064.9,
            ),
            "rollup": UniverseClaim(
                key="rollup",
                described="the largest members of CoinGecko's rollup category",
                counted=30,
                weighted_return_24h=1.5034951175867908,
                advancing=14,
                declining=15,
                market_cap=1_420_633_386.1,
            ),
            "dex-aggregator": UniverseClaim(
                key="dex-aggregator",
                described=(
                    "the largest members of CoinGecko's dex-aggregator category"
                ),
                counted=31,
                weighted_return_24h=-0.2900685835042744,
                advancing=10,
                declining=20,
                market_cap=874_118_174.1,
            ),
        },
    )


class _Recorded:
    """The cycle as a stored reader, reaching no network and no disk."""

    @staticmethod
    def claims(
        coin_ids: tuple[str, ...] = (),
        category_keys: tuple[str, ...] = (),
    ) -> MarketClaimSet | None:
        return _recorded()


class _Unread:
    """A store nothing has been acquired into."""

    @staticmethod
    def claims(
        coin_ids: tuple[str, ...] = (),
        category_keys: tuple[str, ...] = (),
    ) -> MarketClaimSet | None:
        return None


def _service() -> CryptoMarketService:
    return CryptoMarketService(reader=_Recorded())  # type: ignore[arg-type]


# ── acceptance 1 and 2: a family of its own, and no leaking types ───


def test_the_market_family_is_separate_from_token_and_protocol_facts() -> None:
    """Acceptance 1, made structural.

    Three evidence families now describe a token. They must not be able
    to read each other: a market aggregate is not a token fact, and a
    protocol's fees are not a market observation.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/crypto_market.py",
        "app/domain/crypto_market_context.py",
        "app/domain/market_peer_group.py",
    ):
        text = (root / module).read_text(encoding="utf-8")

        imports = [
            line for line in text.splitlines() if line.startswith(("import ", "from "))
        ]

        for line in imports:
            assert "token_facts" not in line, (module, line)
            assert "token_fact_validation" not in line, (module, line)
            assert "protocol_fundamentals" not in line, (module, line)
            assert "protocol_entities" not in line, (module, line)

    # And the reverse: nothing in the older families learned about this.
    for module in (
        "app/domain/token_facts.py",
        "app/domain/protocol_fundamentals.py",
        "app/domain/protocol_entities.py",
    ):
        text = (root / module).read_text(encoding="utf-8")

        assert "crypto_market" not in text, module
        assert "market_peer_group" not in text, module


def test_no_provider_type_reaches_a_canonical_object() -> None:
    """Acceptance 2: CoinGecko terminates at the adapter."""

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/crypto_market.py",
        "app/domain/crypto_market_context.py",
        "app/domain/market_peer_group.py",
    ):
        text = (root / module).read_text(encoding="utf-8")

        assert "app.providers" not in text, module
        assert "requests" not in text, module


def test_a_second_market_provider_joins_without_canonical_change() -> None:
    """The seam, exercised by a source nobody wrote a line for.

    The service takes any reader that answers with a claim set. A future
    CoinMarketCap adapter changes no canonical object, no surface and no
    reasoning — which is the only thing that makes "do not make
    CoinGecko canonical" a fact rather than an intention.
    """

    class _Invented:
        @staticmethod
        def claims(
            coin_ids: tuple[str, ...] = (),
            category_keys: tuple[str, ...] = (),
        ) -> MarketClaimSet:
            return MarketClaimSet(
                source="A source nobody wrote a line for",
                read=Provenance(source="Invented", observed_at=READ),
                state=MarketStateClaim(total_market_cap=1_000.0),
            )

    snapshot = CryptoMarketService(reader=_Invented()).established()  # type: ignore[arg-type]

    assert snapshot.source == "A source nobody wrote a line for"
    assert snapshot.value(MarketMetric.TOTAL_MARKET_CAP) == 1_000.0


# ── acceptance 3: intervals are part of the figure ──────────────────


def test_every_observation_carries_an_interval_that_matches_its_kind() -> None:
    """Acceptance 3.

    A level may not acquire a window and a change may not lose one.
    Those are the two ways market data lies, and the corpus runs the
    whole snapshot past both.
    """

    context = _service().context("HYPE", AssetClass.CRYPTO)

    assert context is not None

    everything = (
        *context.snapshot.observations,
        *context.returns,
        *context.peer_observations,
    )

    assert everything

    for item in everything:
        measure = MEASURES[item.metric]

        if measure.periodicity is MarketPeriodicity.LEVEL:
            assert item.interval is MarketInterval.INSTANT, item.metric
        else:
            assert item.interval.is_window, item.metric


def test_no_metric_is_named_for_a_trend() -> None:
    """A provider field called "change" is not a fact until it says over what.

    Every metric here is named for what was measured, and the interval
    travels beside it. A `market_trend` would be an interpretation
    wearing a fact's name.
    """

    for metric in MarketMetric:
        assert "trend" not in metric.value
        assert "momentum" not in metric.value
        assert "regime" not in metric.value


# ── acceptance 4 and 5: category is not archetype ───────────────────


def test_a_provider_category_can_never_modify_an_archetype() -> None:
    """Acceptance 4 and 5, made structural in both directions."""

    peers = _code("app/domain/market_peer_group.py")

    assert "crypto_archetype" not in peers
    assert "TokenArchetype" not in peers
    assert "AnalyticalCapability" not in peers

    for module in (
        "app/domain/crypto_archetype.py",
        "app/domain/crypto_questions.py",
        "app/domain/crypto_playbook.py",
        "app/services/crypto_playbook_service.py",
    ):
        code = _code(module)

        assert "market_peer_group" not in code, module
        assert "crypto_market" not in code, module


def test_the_archetype_and_the_peer_group_are_allowed_to_disagree() -> None:
    """The measured case the ruling names.

    Ethereum is read as a smart-contract network and compared against a
    market group that contains Bitcoin, XRP and Monero. Both are true,
    and the platform states each in its own vocabulary rather than
    bending one to the other.
    """

    from app.domain.crypto_archetype import TokenArchetype, archetype_for

    assert archetype_for("ETH").archetype is TokenArchetype.SMART_CONTRACT_NETWORK

    peer = peer_group_for("ETH")

    assert peer.group is not None
    assert peer.group.key == "layer-1"
    assert peer.group.key != TokenArchetype.SMART_CONTRACT_NETWORK.value


def test_the_smart_contract_category_was_rejected_on_its_membership() -> None:
    """The ruling's own acceptance case, measured rather than asserted.

    CoinGecko's `smart-contract-platform` category holds Bitcoin at rank
    1. A peer group chosen from a category *name* would have compared
    Ethereum against assets the name excludes.
    """

    rejected = {
        item.key for selection in PEER_GROUPS.values() for item in selection.considered
    }

    assert "smart-contract-platform" in rejected

    for selection in PEER_GROUPS.values():
        assert selection.group is None or selection.group.key != (
            "smart-contract-platform"
        )

    reason = next(
        item.rejected_because
        for selection in PEER_GROUPS.values()
        for item in selection.considered
        if item.key == "smart-contract-platform"
    )

    assert "Bitcoin" in reason


# ── acceptance 6: aligned intervals only ────────────────────────────


def test_relative_arithmetic_refuses_misaligned_intervals() -> None:
    """Acceptance 6, at the one place it could go wrong.

    An asset's 7-day return minus a market's 24-hour move is a number
    with no meaning that would look exactly as authoritative as a real
    one. The function refuses rather than the callers remembering.
    """

    def _observation(interval: MarketInterval, value: float) -> MarketObservation:
        return MarketObservation(
            metric=MarketMetric.ASSET_RETURN,
            interval=interval,
            standing=EvidenceStanding.CLAIMED,
            value=value,
            source="CoinGecko",
        )

    assert (
        relative_return(
            subject="HYPE",
            subject_observation=_observation(MarketInterval.DAYS_7, 3.9),
            comparator="the crypto market",
            comparator_observation=_observation(MarketInterval.HOURS_24, 0.11),
        )
        is None
    )

    aligned = relative_return(
        subject="HYPE",
        subject_observation=_observation(MarketInterval.HOURS_24, -0.2),
        comparator="the crypto market",
        comparator_observation=_observation(MarketInterval.HOURS_24, 0.11),
    )

    assert aligned is not None
    assert aligned.delta == -0.2 - 0.11


def test_only_the_aligned_interval_produces_a_comparison() -> None:
    """The corpus makes it live: four asset intervals, one market interval."""

    context = _service().context("HYPE", AssetClass.CRYPTO)

    assert context is not None
    assert len(context.returns) == 4

    for relative in context.relative:
        assert relative.interval is MarketInterval.HOURS_24

    assert set(context.uncompared) == {
        MarketInterval.HOURS_1,
        MarketInterval.DAYS_7,
        MarketInterval.DAYS_30,
    }


def test_a_capitalisation_change_is_never_used_as_the_comparator() -> None:
    """The semantic trap the measurement exposed.

    The provider's aggregate capitalisation moved +0.05% while the
    weighted return of its 250 largest assets was +0.11%; the Layer 1
    category's aggregate moved +0.05% while its members returned +0.15%.
    Only the second of each pair is a return, and only a return may be
    subtracted from a return.
    """

    context = _service().context("ETH", AssetClass.CRYPTO)

    assert context is not None

    against_market = context.relative_to("the crypto market")
    against_peers = context.relative_to("Layer 1 (L1)")

    assert against_market is not None and against_peers is not None

    market_return = context.snapshot.value(
        MarketMetric.MARKET_RETURN, MarketInterval.HOURS_24
    )
    capitalisation_change = context.snapshot.value(
        MarketMetric.MARKET_CAP_CHANGE, MarketInterval.HOURS_24
    )

    assert market_return is not None and capitalisation_change is not None
    assert market_return != capitalisation_change

    assert against_market.comparator_return == market_return

    peer_return = next(
        item.value
        for item in context.peer_observations
        if item.metric is MarketMetric.PEER_RETURN
    )
    peer_capitalisation = next(
        item.value
        for item in context.peer_observations
        if item.metric is MarketMetric.PEER_MARKET_CAP_CHANGE
    )

    assert peer_return != peer_capitalisation
    assert against_peers.comparator_return == peer_return


# ── acceptance 7: liquidity and market volume never meet ────────────


def test_asset_liquidity_and_global_volume_can_never_be_divided() -> None:
    """Acceptance 7, and the S3 seam it protects.

    The market family holds no asset volume at all, so there is nothing
    to divide a global figure by. `spot_volume_24h` and its relatives
    live in the token-facts family and are not reachable from here.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/crypto_market.py",
        "app/domain/crypto_market_context.py",
        "app/services/crypto_market_service.py",
    ):
        text = (root / module).read_text(encoding="utf-8")

        assert "spot_volume" not in text, module
        assert "market_volume_24h" not in text, module

    context = _service().context("HYPE", AssetClass.CRYPTO)

    assert context is not None

    for item in (*context.snapshot.observations, *context.returns):
        assert "liquidity" not in item.metric.value


def test_the_crypto_quality_liquidity_reading_is_untouched() -> None:
    """Acceptance 12 for S3's finding: the liquidity question did not move.

    S4 supplies another volume field and changes no liquidity rule. The
    quality service's own bands are asserted at their values, and its
    turnover still divides one provider's volume by that provider's
    market value.
    """

    from app.services.crypto_quality_signal_service import CryptoQualitySignalService

    assert CryptoQualitySignalService.LIQUID == 0.02
    assert CryptoQualitySignalService.ILLIQUID == 0.002

    root = pathlib.Path(__file__).resolve().parent.parent

    text = (root / "app/services/crypto_quality_signal_service.py").read_text(
        encoding="utf-8"
    )

    assert "crypto_market" not in text
    assert "total_volume" not in text


# ── acceptance 8 and 9: no sentiment, no regime ─────────────────────


def test_sentiment_and_attention_are_not_in_the_factual_core() -> None:
    """Acceptance 8.

    Fear & Greed and trending are attention signals, not market state.
    Neither is in this family, and neither reaches Asset Quality — the
    quality service cannot import either.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/crypto_market.py",
        "app/domain/crypto_market_context.py",
        "app/services/crypto_market_service.py",
        "app/providers/coingecko_market_provider.py",
    ):
        code = _code(module).casefold()

        assert "fear" not in code, module
        assert "greed" not in code, module
        assert "trending" not in code, module

    quality = (root / "app/services/crypto_quality_signal_service.py").read_text(
        encoding="utf-8"
    )

    assert "sentiment" not in quality.casefold()


def test_no_regime_is_named_anywhere_in_the_market_family() -> None:
    """Acceptance 9.

    S4 acquires the ingredients of a future regime model and classifies
    nothing. `RISK_ON`, `ALTSEASON` and their relatives are
    interpretations, and the layer entitled to make one does not exist.
    """

    forbidden = (
        "risk_on",
        "risk-on",
        "risk_off",
        "altseason",
        "bull market",
        "bear market",
        "overheated",
        "regime",
    )

    for module in (
        "app/domain/crypto_market.py",
        "app/domain/crypto_market_context.py",
        "app/domain/market_peer_group.py",
        "app/services/crypto_market_service.py",
        "app/api/models/crypto_market_adapter.py",
    ):
        code = _code(module).casefold()

        for word in forbidden:
            assert word not in code, (module, word)


def test_relative_wording_is_descriptive_and_threshold_free() -> None:
    """The ruling's own example, checked on the corpus.

    *"HYPE returned 0.20 percentage points less than Perpetuals"* is a
    measurement. *"significant relative weakness"* is a verdict, and no
    rule here has earned one.
    """

    service = _service()

    for symbol in CORPUS:
        context = service.context(symbol, AssetClass.CRYPTO)

        assert context is not None

        for relative in context.relative:
            assert "percentage points" in relative.stated

            for word in ("strong", "weak", "outperform", "underperform"):
                assert word not in relative.stated.casefold(), symbol


# ── acceptance 10, 11, 12: nothing moved ────────────────────────────


def test_no_score_or_decision_path_can_import_the_market_family() -> None:
    """Acceptance 10 and 11, made structural.

    The guard S2 and S3 both carry. A slice that wants market context in
    a score has to argue with this test first.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    reasoning = (
        "app/analysts",
        "app/application/brain",
        "app/application/committees",
        "app/application/executive",
        "app/cio",
        "app/committee",
        "app/domain/business_quality.py",
        "app/domain/playbook.py",
        "app/domain/financial_question.py",
        "app/services/business_quality_service.py",
        "app/services/company_facts_service.py",
        "app/services/company_signal_service.py",
        "app/services/crypto_quality_signal_service.py",
        "app/services/playbook_selector.py",
        "app/services/quality_signal_service.py",
    )

    offenders: list[str] = []

    for target in reasoning:
        path = root / target

        files = (
            sorted(path.rglob("*.py"))
            if path.is_dir()
            else ([path] if path.exists() else [])
        )

        for source in files:
            text = source.read_text(encoding="utf-8")

            if any(
                name in text
                for name in (
                    "crypto_market",
                    "market_peer_group",
                    "coingecko_market_provider",
                )
            ):
                offenders.append(str(source.relative_to(root)))

    assert offenders == []


def test_equity_behaviour_is_unchanged() -> None:
    """Acceptance 14: nothing that reads a company learned about this."""

    root = pathlib.Path(__file__).resolve().parent.parent

    for module in (
        "app/domain/financial_question.py",
        "app/domain/playbook.py",
        "app/services/playbook_selector.py",
    ):
        text = (root / module).read_text(encoding="utf-8").casefold()

        assert "peer group" not in text, module
        assert "crypto_market" not in text, module


def test_nothing_but_a_cryptocurrency_gets_market_context() -> None:
    service = _service()

    for asset_class in (AssetClass.STOCK, AssetClass.ETF, AssetClass.UNKNOWN, None):
        assert service.context("BTC", asset_class) is None


# ── acceptance 13: TAO keeps its absence ────────────────────────────


def test_tao_has_no_peer_group_and_is_not_given_one() -> None:
    """Acceptance 13.

    The market comparison stands and the peer comparison is absent with
    its reason. A comparison against an AI theme would put a number on
    the page that reads like a measurement — and this platform already
    refused to classify TAO from that label in S3.
    """

    context = _service().context("TAO", AssetClass.CRYPTO)

    assert context is not None
    assert not context.has_peer_context

    assert context.peer is not None
    assert context.peer.unavailable_because
    assert "Chainlink" in context.peer.unavailable_because

    assert context.peer_observations == ()

    comparators = {item.comparator for item in context.relative}

    assert comparators == {"the crypto market"}

    rejected = {item.key for item in context.peer.considered}

    assert "artificial-intelligence" in rejected


# ── the arithmetic itself ───────────────────────────────────────────


def test_the_corpus_arithmetic_is_what_the_figures_say() -> None:
    """The deliverable, checked against the recorded cycle.

    ARB rose 3.3% on a day the market returned 0.11% and rollups
    returned 1.50%: it outpaced both, and by different amounts. That is
    the whole question S4 exists to make answerable.
    """

    service = _service()

    arb = service.context("ARB", AssetClass.CRYPTO)

    assert arb is not None

    against_market = arb.relative_to("the crypto market")
    against_peers = arb.relative_to("Rollup")

    assert against_market is not None and against_peers is not None

    assert round(against_market.delta, 2) == 3.19
    assert round(against_peers.delta, 2) == 1.80

    hype = service.context("HYPE", AssetClass.CRYPTO)

    assert hype is not None

    hype_market = hype.relative_to("the crypto market")
    hype_peers = hype.relative_to("Perpetuals")

    assert hype_market is not None and hype_peers is not None

    assert round(hype_market.delta, 2) == -0.31
    assert round(hype_peers.delta, 2) == -0.20


def test_concentration_states_its_denominator() -> None:
    """A share of "the market" is a share of some named set of assets.

    Bitcoin is 57% of the universe the market return was computed over,
    and Hyperliquid is three-quarters of its own peer group. Both are
    stated as plain measurements — no threshold decides when a
    comparison stops being informative.
    """

    service = _service()

    btc = service.context("BTC", AssetClass.CRYPTO)

    assert btc is not None

    share = btc.concentration_in("the crypto market")

    assert share is not None
    assert 56.0 < share.share < 58.0
    assert share.comparator_described is not None
    assert "250 largest" in share.comparator_described

    hype = service.context("HYPE", AssetClass.CRYPTO)

    assert hype is not None

    peers = hype.concentration_in("Perpetuals")

    assert peers is not None
    assert 70.0 < peers.share < 80.0


def test_a_small_holding_is_not_rounded_to_nothing() -> None:
    """0.02% of the market and nothing at all are different readings."""

    context = _service().context("1INCH", AssetClass.CRYPTO)

    assert context is not None

    share = context.concentration_in("the crypto market")

    assert share is not None
    assert "0.01%" in share.stated


# ── standing, and the epistemic finding ─────────────────────────────


def test_every_market_figure_is_a_claim_and_none_is_established() -> None:
    """Acceptance 12 for S1's contract.

    One market source, so nothing is corroborated — and a total market
    capitalisation could not be corroborated even by a second vendor,
    because the universe is the vendor's own. The rule was not weakened
    to make the number look firmer.
    """

    service = _service()

    for symbol in CORPUS:
        context = service.context(symbol, AssetClass.CRYPTO)

        assert context is not None

        for item in (
            *context.snapshot.observations,
            *context.returns,
            *context.peer_observations,
        ):
            assert item.standing in (
                EvidenceStanding.CLAIMED,
                EvidenceStanding.ABSENT,
            ), (symbol, item.metric)

        for relative in context.relative:
            assert relative.standing is EvidenceStanding.CLAIMED


def test_a_derived_figure_names_what_it_was_computed_from() -> None:
    """Arithmetic that cannot be checked is a number with a story."""

    snapshot = _service().established()

    for metric in (
        MarketMetric.MARKET_RETURN,
        MarketMetric.ADVANCING,
        MarketMetric.DECLINING,
    ):
        held = snapshot.observation(metric)

        assert held is not None
        assert held.derived_from
        assert held.universe is not None
        assert held.measure.derived


def test_an_unread_store_says_so_rather_than_showing_zero() -> None:
    """A fresh clone has no cycle, and every surface must say that."""

    service = CryptoMarketService(reader=_Unread())  # type: ignore[arg-type]

    snapshot = service.established()

    assert not snapshot.is_read
    assert snapshot.unavailable_because
    assert "movrvest acquire" in snapshot.unavailable_because

    context = service.context("BTC", AssetClass.CRYPTO)

    assert context is not None
    assert context.relative == ()
    assert context.unavailable_because


# ── the acquisition batch ───────────────────────────────────────────


def test_the_batch_reads_each_peer_group_once() -> None:
    """Four securities share one group, and it costs one call.

    The deduplication is what keeps the call count a property of the
    peer-group table rather than of the corpus size.
    """

    groups = acquired_groups()

    keys = [group.key for group in groups]

    assert len(keys) == len(set(keys))

    assigned = {
        selection.group.key
        for selection in PEER_GROUPS.values()
        if selection.group is not None
    }

    assert set(keys) == assigned

    # Layer 1 serves three securities and is read once.
    layer_1 = [
        symbol
        for symbol, selection in PEER_GROUPS.items()
        if selection.group is not None and selection.group.key == "layer-1"
    ]

    assert len(layer_1) == 3


def test_every_corpus_security_has_a_verified_peer_decision() -> None:
    """Present in the table, with a group or a stated reason for none."""

    for symbol in CORPUS:
        selection = peer_group_for(symbol)

        assert selection.symbol == symbol

        if selection.group is None:
            assert selection.unavailable_because, symbol
        else:
            assert selection.group.selected_because, symbol


def test_a_security_outside_the_corpus_is_not_given_a_guessed_group() -> None:
    selection = peer_group_for("DOGE")

    assert selection.group is None
    assert selection.unavailable_because is not None
    assert "guess" in selection.unavailable_because


def test_market_units_are_never_mixed_up() -> None:
    """A share, a change and a difference are three different units."""

    assert MEASURES[MarketMetric.BTC_DOMINANCE].unit is MarketUnit.PERCENT_SHARE
    assert MEASURES[MarketMetric.MARKET_RETURN].unit is MarketUnit.PERCENT_CHANGE
    assert MEASURES[MarketMetric.TOTAL_MARKET_CAP].unit is MarketUnit.USD
    assert MEASURES[MarketMetric.ADVANCING].unit is MarketUnit.COUNT

    assert set(MEASURES) == set(MarketMetric)
