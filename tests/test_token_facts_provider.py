"""The factual half of the TokenInsight integration, and strictly that.

Distillation is tested against the provider's real payload shape (the
2026-08-10 probe), identity is refused before anything is carried, and
the structural separation from the rating — an opinion — is enforced on
the import graph, the same way the rating's own boundary is.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

from app.infrastructure.cache.json_cache import JsonCache
from app.providers.token_facts_provider import (
    CachedTokenFactsProvider,
    TokenFactsProvider,
)

#: The provider's answer for Hyperliquid, in the shape the coin
#: endpoint actually returns — top-level identity, market_data with a
#: per-currency price list.
HYPERLIQUID = {
    "id": "hyperliquid",
    "symbol": "HYPE",
    "name": "Hyperliquid",
    "rank": 9,
    "market_data": {
        "max_supply": 1_000_000_000,
        "circulating_supply": 336_685_219.0,
        "circulating_supply_percentage": 0.3366852190,
        "last_updated": 1786338257000,
        "price": [
            {
                "currency": "usd",
                "price_latest": 54.23,
                "market_cap": 18_256_170_748.0,
                "fully_diluted_valuation": 54_223_261_723.0,
                "price_change_percentage_24h": -0.0091,
                "vol_spot_24h": 11_780_956.17,
                "vol_spot_change_percentage_24h": -0.3007,
            }
        ],
    },
}


def test_the_payload_distills_into_unjudged_claims() -> None:
    claims = TokenFactsProvider._distill("HYPE", "hyperliquid", HYPERLIQUID)

    assert claims.symbol == "HYPE"
    assert claims.provider_id == "hyperliquid"
    assert claims.source == "TokenInsight"
    assert claims.price == 54.23
    assert claims.market_cap == 18_256_170_748.0
    assert claims.circulating_supply == 336_685_219.0
    assert claims.max_supply == 1_000_000_000.0
    assert claims.fully_diluted_valuation == 54_223_261_723.0
    assert claims.rank == 9.0
    assert claims.spot_volume_24h == 11_780_956.17
    assert claims.spot_volume_change_24h == -0.3007
    assert claims.price_change_24h == -0.0091

    # Dated by the provider's own data timestamp, not the read.
    assert claims.read.observed_at == datetime.fromtimestamp(1786338257, tz=UTC)


def test_an_answer_about_another_token_is_refused() -> None:
    """The identity check before anything is carried — the NESN.ZU lesson."""

    import pytest

    from app.providers.token_facts_provider import TokenFactsUnavailable

    wrong = dict(HYPERLIQUID, symbol="SUPREME")

    with pytest.raises(TokenFactsUnavailable) as refused:
        TokenFactsProvider._distill("HYPE", "hyperliquid", wrong)

    assert "SUPREME" in str(refused.value)


def test_a_provider_zero_is_an_absence_in_the_claims_too() -> None:
    """No trading token's market value or supply is genuinely zero."""

    zeroed = dict(
        HYPERLIQUID,
        market_data={
            "max_supply": 0,
            "circulating_supply": 0,
            "price": [
                {
                    "currency": "usd",
                    "price_latest": 0,
                    "market_cap": 0,
                    "vol_spot_24h": 0,
                    # A change of exactly zero is a legitimate value:
                    # unchanged is not unreported.
                    "vol_spot_change_percentage_24h": 0,
                }
            ],
        },
    )

    claims = TokenFactsProvider._distill("HYPE", "hyperliquid", zeroed)

    assert claims.market_cap is None
    assert claims.circulating_supply is None
    assert claims.max_supply is None
    assert claims.price is None
    assert claims.spot_volume_24h is None

    assert claims.spot_volume_change_24h == 0.0


def test_the_stored_door_never_reaches_the_network(
    tmp_path: pathlib.Path,
) -> None:
    """A surface reads what was acquired, and acquires nothing."""

    class Explosive(TokenFactsProvider):
        def claims(self, symbol: str):  # pragma: no cover - the trap
            raise AssertionError("The stored door reached the provider.")

    cache = JsonCache(str(tmp_path / "token_facts"))

    door = CachedTokenFactsProvider(
        provider=Explosive(),
        cache=cache,
        acquires=False,
    )

    assert door.claims("HYPE") is None


def test_stored_claims_survive_the_cache_round_trip(
    tmp_path: pathlib.Path,
) -> None:
    claims = TokenFactsProvider._distill("HYPE", "hyperliquid", HYPERLIQUID)

    cache = JsonCache(str(tmp_path / "token_facts"))
    cache.write("HYPE", CachedTokenFactsProvider._encode(claims))

    served = CachedTokenFactsProvider.stored(cache).claims("HYPE")

    assert served is not None
    assert served.market_cap == claims.market_cap
    assert served.circulating_supply == claims.circulating_supply
    assert served.spot_volume_change_24h == claims.spot_volume_change_24h
    assert served.read.observed_at == claims.read.observed_at


# ── the structural separation from the rating ───────────────────────

#: The factual stream and the opinion stream share a vendor and nothing
#: else. If either could reach the other's objects, accepting facts
#: would quietly promote the opinion — the exact move the rating's own
#: boundary forbids.
FACTUAL = (
    "app/domain/token_facts.py",
    "app/domain/token_fact_validation.py",
    "app/providers/token_facts_provider.py",
    "app/services/token_facts_service.py",
)

OPINION_MARKS = ("TokenRating", "RatingDimension", "/rating/", "rating_level")


def test_the_factual_stream_never_touches_the_rating() -> None:
    root = pathlib.Path(__file__).resolve().parent.parent

    offenders: list[str] = []

    for target in FACTUAL:
        text = (root / target).read_text(encoding="utf-8")

        if any(mark in text for mark in OPINION_MARKS):
            offenders.append(target)

    assert offenders == []


def test_the_rating_never_touches_the_factual_stream() -> None:
    root = pathlib.Path(__file__).resolve().parent.parent

    text = (root / "app/providers/token_insight_provider.py").read_text(
        encoding="utf-8"
    )

    assert "token_facts" not in text
    assert "TokenMarketFacts" not in text
