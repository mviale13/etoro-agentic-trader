"""The second factual claimant, and the pool's openness to a third.

CoinGecko is an adapter and nothing more: it terminates its payload at
a `TokenClaimSet` and takes no authority. These tests hold that
boundary — and prove, at the service seam rather than the validator's,
that a wholly unknown claimant joins the pool without a line changing
anywhere else.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import TokenClaimSet
from app.domain.token_facts import TokenFactStanding
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.coingecko_facts_provider import (
    CachedCoinGeckoFactsProvider,
    CoinGeckoFactsProvider,
)
from app.services.token_facts_service import TokenFactsService

#: CoinGecko's answer for Hyperliquid, in the shape /coins/{id} returns.
HYPERLIQUID = {
    "id": "hyperliquid",
    "symbol": "hype",
    "name": "Hyperliquid",
    "market_cap_rank": 10,
    "genesis_date": None,
    "market_data": {
        "current_price": {"usd": 54.63, "eur": 47.0},
        "market_cap": {"usd": 12_150_000_000.0},
        "fully_diluted_valuation": {"usd": 54_630_000_000.0},
        "total_volume": {"usd": 163_000_000.0},
        "circulating_supply": 222_445_714.0,
        "total_supply": 955_307_079.0,
        "max_supply": 1_000_000_000.0,
        "last_updated": "2026-08-10T09:00:00.000Z",
    },
}


def test_the_payload_distills_into_an_unjudged_claim_set() -> None:
    claims = CoinGeckoFactsProvider._distill("HYPE", HYPERLIQUID)

    assert claims.source == "CoinGecko"
    assert claims.symbol_echo == "HYPE"
    assert claims.provider_id == "hyperliquid"
    assert claims.price == 54.63
    assert claims.market_cap == 12_150_000_000.0
    assert claims.circulating_supply == 222_445_714.0
    assert claims.total_supply == 955_307_079.0
    assert claims.max_supply == 1_000_000_000.0
    assert claims.fully_diluted_valuation == 54_630_000_000.0
    assert claims.rank == 10.0

    # Its tracked-venue aggregate keeps its own name and is never mapped
    # onto tracked spot volume or the generalist's broader figure.
    assert claims.market_volume_24h == 163_000_000.0
    assert claims.spot_volume_24h is None

    assert claims.read.observed_at == datetime(2026, 8, 10, 9, 0, tzinfo=UTC)


def test_an_answer_about_another_token_is_refused() -> None:
    import pytest

    from app.providers.coingecko_facts_provider import CoinGeckoFactsUnavailable

    with pytest.raises(CoinGeckoFactsUnavailable) as refused:
        CoinGeckoFactsProvider._distill("HYPE", dict(HYPERLIQUID, symbol="supreme"))

    assert "SUPREME" in str(refused.value)


def test_a_provider_zero_is_an_absence() -> None:
    zeroed = dict(
        HYPERLIQUID,
        market_data={
            "current_price": {"usd": 0},
            "market_cap": {"usd": 0},
            "circulating_supply": 0,
            "max_supply": 0,
            "total_volume": {"usd": 0},
        },
    )

    claims = CoinGeckoFactsProvider._distill("HYPE", zeroed)

    assert claims.price is None
    assert claims.market_cap is None
    assert claims.circulating_supply is None
    assert claims.market_volume_24h is None


def test_the_stored_door_never_reaches_the_network(
    tmp_path: pathlib.Path,
) -> None:
    class Explosive(CoinGeckoFactsProvider):
        def claims(self, symbol: str):  # pragma: no cover - the trap
            raise AssertionError("The stored door reached the provider.")

    door = CachedCoinGeckoFactsProvider(
        provider=Explosive(),
        cache=JsonCache(str(tmp_path / "coingecko_facts")),
        acquires=False,
    )

    assert door.claims("HYPE") is None


def test_stored_claims_survive_the_cache_round_trip(
    tmp_path: pathlib.Path,
) -> None:
    claims = CoinGeckoFactsProvider._distill("HYPE", HYPERLIQUID)

    cache = JsonCache(str(tmp_path / "coingecko_facts"))
    cache.write("HYPE", CachedCoinGeckoFactsProvider._encode(claims))

    served = CachedCoinGeckoFactsProvider.stored(cache).claims("HYPE")

    assert served is not None
    assert served.market_cap == claims.market_cap
    assert served.total_supply == claims.total_supply
    assert served.market_volume_24h == claims.market_volume_24h
    assert served.read.observed_at == claims.read.observed_at


# ── the pool is open, at the service seam ───────────────────────────


class FakeClaimSource:
    """A claimant this platform has never heard of."""

    def __init__(self, claims: TokenClaimSet) -> None:
        self._claims = claims

    def claim_set(self, symbol: str) -> TokenClaimSet:
        return self._claims


def claim_set(source: str, market_cap: float, circulating: float) -> TokenClaimSet:
    return TokenClaimSet(
        source=source,
        read=Provenance(
            source=source,
            observed_at=datetime(2026, 8, 10, 9, 0, tzinfo=UTC),
        ),
        symbol_echo="BTC",
        price=market_cap / circulating,
        market_cap=market_cap,
        circulating_supply=circulating,
    )


def test_a_third_unknown_claimant_joins_without_touching_anything() -> None:
    """Acceptance 12, at the seam a real provider would enter through.

    The service takes its claimants as a list; the validator names no
    provider in any establishment rule. A source nobody wrote a line
    for corroborates exactly as the built-in ones do.
    """

    service = TokenFactsService(
        sources=(
            FakeClaimSource(claim_set("Acme Data", 1_300_000_000_000.0, 20_000_000.0)),
            FakeClaimSource(claim_set("Beta Feed", 1_305_000_000_000.0, 20_010_000.0)),
        ),
    )

    outcome = service.established("BTC", "BTC", AssetClass.CRYPTO)

    assert outcome is not None

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.because is not None
    assert "Beta Feed" in market_cap.because


def test_one_claimant_alone_still_only_claims() -> None:
    service = TokenFactsService(
        sources=(
            FakeClaimSource(claim_set("Acme Data", 1_300_000_000_000.0, 20_000_000.0)),
        ),
    )

    outcome = service.established("BTC", "BTC", AssetClass.CRYPTO)

    assert outcome is not None
    assert outcome.established_value("market_cap") is None


def test_the_service_refuses_anything_that_is_not_crypto() -> None:
    """Acceptance 10 and 12: no security is promoted to a token."""

    service = TokenFactsService(
        sources=(FakeClaimSource(claim_set("Acme Data", 1.0, 1.0)),),
    )

    for asset_class in (
        AssetClass.STOCK,
        AssetClass.ETF,
        AssetClass.COMMODITY,
        AssetClass.UNKNOWN,
        None,
    ):
        assert service.established("AAPL", "Apple", asset_class) is None


# ── adapters terminate before canonical facts ───────────────────────


def test_no_canonical_layer_imports_a_provider_response() -> None:
    """Acceptance 2, made structural.

    The validator, the fact objects and the assembly may not name a
    provider module. A claim reaches them as a `TokenClaimSet` or not
    at all — which is what lets a fourth source arrive later without
    touching any of them.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    canonical = (
        "app/domain/token_facts.py",
        "app/domain/token_fact_validation.py",
        "app/api/models/asset_profile_adapter.py",
    )

    offenders = [
        target
        for target in canonical
        if "app.providers" in (root / target).read_text(encoding="utf-8")
    ]

    assert offenders == []
