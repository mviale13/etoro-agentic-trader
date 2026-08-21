"""The factual half of the TokenInsight integration, and strictly that.

Distillation is tested against the provider's real payload shape (the
2026-08-10 probe), identity is refused before anything is carried, and
the structural separation from the rating — an opinion — is enforced on
the import graph, the same way the rating's own boundary is.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

from app.infrastructure.cache.json_cache import JsonCache
from app.providers.token_facts_provider import (
    CachedTokenFactsProvider,
    TokenFactsProvider,
    _receipt_clock,
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

    assert claims.symbol_echo == "HYPE"
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

    # Dated by the read, and *declared* to be dated by the read.
    #
    # This assertion used to read "dated by the provider's own data
    # timestamp, not the read" and pinned `last_updated` as the
    # observation time. The 2026-08-21 measurement withdrew that: the
    # field does not advance with the price it sits beside, so it never
    # described this figure.
    assert claims.read.observation_stated is False
    assert claims.read.observed_at != datetime.fromtimestamp(1786338257, tz=UTC)
    assert claims.read.observed_at.tzinfo is not None


def test_the_frozen_provider_timestamp_reaches_nothing() -> None:
    """`last_updated` is not read as an observation time — at all.

    The measurement, live on 2026-08-21: over one 90-second window
    `price_latest` moved 73.06613809983222 → 73.0488279001271 while
    `market_data.last_updated` did not advance, and it stood 16.5 hours
    behind the fetch across five assets stamped within 49 seconds of
    each other. A batch stamp, not a per-quote clock.

    So the test is not that a different field is preferred — it is that
    this value cannot appear anywhere in the claim, however the payload
    moves it.
    """

    moved = {
        **HYPERLIQUID,
        "market_data": {
            **HYPERLIQUID["market_data"],  # type: ignore[dict-item]
            "last_updated": 1_786_338_257_000,
            "price": [
                {
                    **HYPERLIQUID["market_data"]["price"][0],  # type: ignore[index]
                    "price_latest": 73.0488279001271,
                }
            ],
        },
    }

    claims = TokenFactsProvider._distill("HYPE", "hyperliquid", moved)

    frozen = datetime.fromtimestamp(1786338257, tz=UTC)

    assert claims.price == 73.0488279001271
    assert claims.read.observed_at != frozen
    assert claims.read.observation_stated is False

    # And the reading says "received", never a bare age that an
    # investor would read as the price's own.
    assert "received" in claims.read.stated()


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

    # The qualifier survives the store. A round trip that dropped it
    # would restore exactly the claim schema 2 withdrew.
    assert served.read.observation_stated is False


def test_a_schema_one_record_comes_forward_on_the_receipt_clock(
    tmp_path: pathlib.Path,
) -> None:
    """The migration keeps the figures and drops the false timestamp.

    A schema-1 record's `observed_at` is `market_data.last_updated`.
    It cannot become an observation time (it never was one) and it must
    not be relabelled a receipt time (it is not that either). What the
    record does hold honestly is `stored_at` — the moment MOVRvest
    wrote the response down — so that is what the entry ages on.
    """

    written = "2026-08-21T06:59:42.550069+00:00"
    frozen = "2026-08-20T14:29:38+00:00"

    legacy = JsonCache(str(tmp_path / "token_facts"), schema=1)
    legacy.write(
        "HYPE",
        {
            "symbol": "HYPE",
            "provider_id": "hyperliquid",
            "source": "TokenInsight",
            "observed_at": frozen,
            "price": 72.73774324560395,
            "market_cap": 24_600_288_707.6,
            "circulating_supply": 336_685_219.0,
            "max_supply": 1_000_000_000.0,
            "fully_diluted_valuation": None,
            "rank": 9.0,
            "spot_volume_24h": 110_882_604.5,
            "spot_volume_change_24h": -0.0194,
            "price_change_24h": 0.0177,
        },
    )

    # Rewrite `stored_at` so the entry's receipt moment is the one the
    # live record carried, rather than this test's clock.
    path = next((tmp_path / "token_facts").glob("HYPE.*.json"))
    record = json.loads(path.read_text(encoding="utf-8"))
    record["stored_at"] = written
    path.write_text(json.dumps(record), encoding="utf-8")

    served = CachedTokenFactsProvider.stored(
        JsonCache(
            str(tmp_path / "token_facts"),
            schema=2,
            migrations={1: _receipt_clock},
            accepts_unversioned=True,
        )
    ).claims("HYPE")

    assert served is not None

    # The evidence survives — the migration costs no re-acquisition.
    assert served.price == 72.73774324560395
    assert served.circulating_supply == 336_685_219.0

    # The false timestamp does not.
    assert served.read.observed_at != datetime.fromisoformat(frozen)
    assert served.read.observed_at == datetime.fromisoformat(written)
    assert served.read.observation_stated is False


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
