"""The Fresh Quote Ribbon's contract: display plumbing, never evidence.

Everything here runs against a stub transport and a temp evidence root —
no wire, no spend, no writes to anything real.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import Settings
from app.domain.fresh_quote import (
    ClockKind,
    FreshQuote,
    QuoteStatus,
)
from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)
from app.services.fresh_quote_service import FreshQuoteService

RECEIVED = datetime(2026, 8, 25, 14, 15, 52, tzinfo=UTC)


# ── the status rule ─────────────────────────────────────────────────


def test_current_needs_the_sources_own_clock_inside_the_window() -> None:
    assert (
        FreshQuote.status_of(
            RECEIVED - timedelta(seconds=119), RECEIVED, ClockKind.SOURCE_STATED
        )
        is QuoteStatus.CURRENT
    )

    assert (
        FreshQuote.status_of(
            RECEIVED - timedelta(seconds=121), RECEIVED, ClockKind.SOURCE_STATED
        )
        is QuoteStatus.STALE
    )


def test_a_receipt_only_quote_is_never_current() -> None:
    """Recency of receipt is not recency of observation. A quote whose
    provider stated no time is STALE however fresh the delivery."""

    assert (
        FreshQuote.status_of(None, RECEIVED, ClockKind.RECEIPT_ONLY)
        is QuoteStatus.STALE
    )

    # Even a fabricated recent source moment cannot rescue the wrong
    # clock kind.
    assert (
        FreshQuote.status_of(RECEIVED, RECEIVED, ClockKind.RECEIPT_ONLY)
        is QuoteStatus.STALE
    )


def test_the_stated_sentence_never_says_live() -> None:
    for quote in (
        FreshQuote.answered(
            symbol="DIS",
            asset_class=__import__(
                "app.domain.fresh_quote", fromlist=["AssetClass"]
            ).AssetClass.SECURITY,
            provider="eToro",
            identity="1016",
            label="Walt Disney",
            price=110.8,
            bid=110.8,
            ask=110.82,
            source_as_of=RECEIVED - timedelta(hours=3),
            received_at=RECEIVED,
        ),
        FreshQuote.identity_refused(
            "ZZZZ",
            __import__(
                "app.domain.fresh_quote", fromlist=["AssetClass"]
            ).AssetClass.SECURITY,
            "eToro",
        ),
    ):
        assert "live" not in quote.stated.lower()
        assert "real-time" not in quote.stated.lower()


# ── fixtures: a stored catalog and a stub transport ─────────────────


def seeded_store(tmp_path: Path) -> VersionedSnapshotStore:
    """A catalog the way real cycles record one: a watchlists capture
    naming four symbols, an instruments capture naming BNP.PA."""

    store = VersionedSnapshotStore(tmp_path)

    store.save(
        broker="etoro",
        environment="demo",
        endpoint="watchlists",
        payload={
            "watchlists": [
                {
                    "items": [
                        {
                            "itemId": 1016,
                            "market": {
                                "id": "1016",
                                "symbolName": "DIS",
                                "displayName": "Walt Disney",
                            },
                        },
                        {
                            "itemId": 1004,
                            "market": {
                                "id": "1004",
                                "symbolName": "MSFT",
                                "displayName": "Microsoft",
                            },
                        },
                        {
                            "itemId": 100446,
                            "market": {
                                "id": "100446",
                                "symbolName": "HYPE",
                                "displayName": "Hyperliquid",
                            },
                        },
                        {
                            "itemId": 100418,
                            "market": {
                                "id": "100418",
                                "symbolName": "TAO",
                                "displayName": "Bittensor",
                            },
                        },
                    ],
                },
            ],
        },
        metadata={},
    )

    store.save(
        broker="etoro",
        environment="demo",
        endpoint="marketDataInstruments",
        payload={
            "instrumentDisplayDatas": [
                {
                    "instrumentID": 1238,
                    "symbolFull": "BNP.PA",
                    "instrumentDisplayName": "BNP Paribas SA",
                },
            ],
        },
        metadata={},
    )

    return store


class StubResponse:
    def __init__(self, body: dict[str, Any], status: int = 200) -> None:
        self._body = body
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._body


class StubClient:
    """A transport that answers like the measured rates route and
    counts how often it was asked."""

    def __init__(self, rows: list[dict[str, Any]] | Exception) -> None:
        self.rows = rows
        self.calls = 0
        self.last_params: dict[str, Any] | None = None
        self.last_headers: dict[str, str] | None = None

    async def get(self, url: str, **kwargs: Any) -> StubResponse:
        self.calls += 1
        self.last_params = kwargs.get("params")
        self.last_headers = kwargs.get("headers")

        if isinstance(self.rows, Exception):
            raise self.rows

        return StubResponse({"rates": self.rows})


def row(instrument_id: int, price: float, as_of: datetime) -> dict[str, Any]:
    """A rates row exactly as Stage 0 measured one."""

    return {
        "instrumentID": instrument_id,
        "ask": price + 0.02,
        "bid": price,
        "lastExecution": price,
        "conversionRateAsk": 1.0,
        "conversionRateBid": 1.0,
        "date": as_of.isoformat().replace("+00:00", "Z"),
        "priceRateID": 1,
    }


def settings() -> Settings:
    return Settings(
        etoro_api_key="test-api-key",
        etoro_user_key="test-user-key",
        trading_mode="demo",
    )


def service(
    tmp_path: Path,
    client: StubClient,
    *,
    ttl: float = 60.0,
    clock: Any = None,
) -> FreshQuoteService:
    return FreshQuoteService(
        settings(),
        client=client,  # type: ignore[arg-type]
        store=seeded_store(tmp_path),
        ttl_seconds=ttl,
        clock=clock,
    )


def fresh_rows() -> list[dict[str, Any]]:
    now = datetime.now(UTC)

    return [
        row(1016, 110.8, now),
        row(1004, 487.4, now),
        row(1238, 104.76, now),
        row(100446, 80.86, now),
        row(100418, 235.44, now),
    ]


# ── identity ────────────────────────────────────────────────────────


def test_identity_resolves_from_stored_captures_and_batches_one_call(
    tmp_path: Path,
) -> None:
    client = StubClient(fresh_rows())
    quotes = asyncio.run(
        service(tmp_path, client).quotes(("DIS", "HYPE", "TAO", "BNP.PA"))
    )

    assert client.calls == 1
    by_symbol = {q.movrvest_symbol: q for q in quotes}

    assert by_symbol["DIS"].provider_instrument_identity == "1016"
    assert by_symbol["DIS"].provider_label == "Walt Disney"
    assert by_symbol["HYPE"].provider_instrument_identity == "100446"
    assert by_symbol["HYPE"].provider_label == "Hyperliquid"
    assert by_symbol["TAO"].provider_instrument_identity == "100418"
    assert by_symbol["TAO"].provider_label == "Bittensor"
    assert by_symbol["BNP.PA"].provider_instrument_identity == "1238"

    # Crypto and securities are told apart by the corpus declaration.
    assert by_symbol["HYPE"].asset_class.value == "crypto"
    assert by_symbol["DIS"].asset_class.value == "security"


def test_an_unknown_symbol_is_refused_not_guessed(tmp_path: Path) -> None:
    client = StubClient(fresh_rows())
    quotes = asyncio.run(service(tmp_path, client).quotes(("ZZZZNOTASYMBOL",)))

    assert len(quotes) == 1
    assert quotes[0].status is QuoteStatus.IDENTITY_REFUSED
    assert quotes[0].price is None
    assert "stored broker catalog" in quotes[0].stated


def test_a_silently_omitted_row_is_unavailable(tmp_path: Path) -> None:
    """Stage 0: the rates route drops unknown ids without a marker. A
    symbol asked for and missing from the answer is a typed absence."""

    rows = [r for r in fresh_rows() if r["instrumentID"] != 100418]
    client = StubClient(rows)

    quotes = asyncio.run(service(tmp_path, client).quotes(("TAO", "DIS")))
    by_symbol = {q.movrvest_symbol: q for q in quotes}

    assert by_symbol["TAO"].status is QuoteStatus.UNAVAILABLE
    assert by_symbol["TAO"].price is None
    assert by_symbol["DIS"].status is QuoteStatus.CURRENT


# ── clocks ──────────────────────────────────────────────────────────


def test_a_fresh_source_clock_is_current_and_an_old_one_is_stale(
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    client = StubClient(
        [
            row(1016, 110.8, now - timedelta(seconds=30)),
            row(1004, 487.4, now - timedelta(hours=22)),
        ]
    )

    quotes = asyncio.run(service(tmp_path, client).quotes(("DIS", "MSFT")))
    by_symbol = {q.movrvest_symbol: q for q in quotes}

    assert by_symbol["DIS"].status is QuoteStatus.CURRENT
    assert by_symbol["DIS"].clock_kind is ClockKind.SOURCE_STATED

    assert by_symbol["MSFT"].status is QuoteStatus.STALE
    assert by_symbol["MSFT"].price == 487.4


def test_a_naive_source_time_is_refused_and_the_quote_never_current(
    tmp_path: Path,
) -> None:
    """A time with no zone is a claim with no zone. The quote survives,
    on the receipt clock, and the receipt clock cannot make it current."""

    naive = dict(row(1016, 110.8, datetime.now(UTC)))
    naive["date"] = "2026-08-25T14:15:52.9629221"  # no Z, no offset

    quotes = asyncio.run(service(tmp_path, StubClient([naive])).quotes(("DIS",)))

    assert quotes[0].clock_kind is ClockKind.RECEIPT_ONLY
    assert quotes[0].status is QuoteStatus.STALE
    assert quotes[0].source_as_of is None
    assert quotes[0].received_at is not None


# ── the cache and the single flight ─────────────────────────────────


def test_two_reads_inside_the_ttl_cost_one_provider_call(
    tmp_path: Path,
) -> None:
    moments = iter([0.0, 0.0, 10.0, 10.0, 10.0])
    client = StubClient(fresh_rows())
    svc = service(tmp_path, client, ttl=60.0, clock=lambda: next(moments))

    asyncio.run(svc.quotes(("DIS",)))
    asyncio.run(svc.quotes(("HYPE",)))

    assert client.calls == 1


def test_the_ttl_expiring_permits_exactly_one_more_call(tmp_path: Path) -> None:
    times = [0.0]
    client = StubClient(fresh_rows())
    svc = service(tmp_path, client, ttl=60.0, clock=lambda: times[0])

    asyncio.run(svc.quotes(("DIS",)))
    times[0] = 61.0
    asyncio.run(svc.quotes(("DIS",)))
    asyncio.run(svc.quotes(("MSFT",)))

    assert client.calls == 2


def test_concurrent_views_coalesce_onto_one_request(tmp_path: Path) -> None:
    """Acceptance 6: many simultaneous views, one provider request."""

    class SlowClient(StubClient):
        async def get(self, url: str, **kwargs: Any) -> StubResponse:
            await asyncio.sleep(0.02)

            return await super().get(url, **kwargs)

    client = SlowClient(fresh_rows())
    svc = service(tmp_path, client)

    async def storm() -> None:
        await asyncio.gather(
            *(svc.quotes(("DIS", "HYPE")) for _ in range(8)),
        )

    asyncio.run(storm())

    assert client.calls == 1


# ── failure is local ────────────────────────────────────────────────


def test_a_provider_failure_yields_unavailable_and_raises_nothing(
    tmp_path: Path,
) -> None:
    client = StubClient(RuntimeError("connection refused"))

    quotes = asyncio.run(service(tmp_path, client).quotes(("DIS", "HYPE")))

    assert [q.status for q in quotes] == [
        QuoteStatus.UNAVAILABLE,
        QuoteStatus.UNAVAILABLE,
    ]
    assert all(q.price is None for q in quotes)


def test_a_failing_provider_is_asked_once_per_window_not_per_view(
    tmp_path: Path,
) -> None:
    moments = [0.0]
    client = StubClient(RuntimeError("connection refused"))
    svc = service(tmp_path, client, ttl=60.0, clock=lambda: moments[0])

    asyncio.run(svc.quotes(("DIS",)))
    moments[0] = 5.0
    asyncio.run(svc.quotes(("DIS",)))

    assert client.calls == 1


# ── nothing is written, nothing decisive is produced ────────────────


def test_a_quote_read_writes_nothing_anywhere(tmp_path: Path) -> None:
    """The evidence root gains no file from serving quotes: the store
    is read for identity and never written."""

    client = StubClient(fresh_rows())
    svc = service(tmp_path, client)

    before = sorted(p for p in tmp_path.rglob("*") if p.is_file())
    asyncio.run(svc.quotes(("DIS", "HYPE", "BNP.PA")))
    after = sorted(p for p in tmp_path.rglob("*") if p.is_file())

    assert before == after


def test_no_credential_reaches_the_quote_object(tmp_path: Path) -> None:
    client = StubClient(fresh_rows())
    quotes = asyncio.run(service(tmp_path, client).quotes(("DIS",)))

    blob = json.dumps(
        [
            {
                "stated": q.stated,
                "provider": q.provider,
                "label": q.provider_label,
                "identity": q.provider_instrument_identity,
            }
            for q in quotes
        ]
    )

    assert "test-api-key" not in blob
    assert "test-user-key" not in blob

    # And the credential did travel to the provider, where it belongs.
    assert client.last_headers is not None
    assert client.last_headers["x-api-key"] == "test-api-key"


def test_currency_delay_and_market_status_stay_unknown(tmp_path: Path) -> None:
    """Stage 0: the route states none of the three. Unknown stays
    unknown — a conversion rate of 1.0 is not a currency name."""

    client = StubClient(fresh_rows())
    quotes = asyncio.run(service(tmp_path, client).quotes(("DIS", "BNP.PA")))

    for quote in quotes:
        assert quote.currency is None
        assert quote.delay_status.value == "unknown"
        assert quote.market_status.value == "unknown"
