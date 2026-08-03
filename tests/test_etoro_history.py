"""Reading the record of what actually happened."""

import asyncio
import json
from datetime import date

import httpx
import pytest

from app.brokers.etoro_client import EtoroClient
from app.brokers.etoro_history import EtoroHistoryBroker, require_trading_account
from app.config import Settings
from app.infrastructure.evidence import VersionedSnapshotStore

SINCE = date(2026, 1, 1)


def broker(tmp_path, handler, mode: str = "demo") -> EtoroHistoryBroker:
    settings = Settings(
        etoro_api_key="k",
        etoro_user_key="u",
        trading_mode=mode,  # type: ignore[arg-type]
    )

    return EtoroHistoryBroker(
        settings,
        api=EtoroClient(
            settings,
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            evidence_store=VersionedSnapshotStore(root=tmp_path),
        ),
    )


def pages(*bodies):
    def handle(request: httpx.Request) -> httpx.Response:
        handle.seen.append(request)  # type: ignore[attr-defined]
        body = bodies[min(len(handle.seen) - 1, len(bodies) - 1)]  # type: ignore[attr-defined]

        return httpx.Response(200, json=body)

    handle.seen = []  # type: ignore[attr-defined]

    return handle


def test_the_demo_and_real_paths_differ_by_a_missing_segment(tmp_path) -> None:
    """
    Unlike `/pnl`, the real variant carries no account segment at all.

    It is the absence of `demo` that selects the real account, which is
    the kind of asymmetry that gets a live account read by accident.
    """

    demo = pages({"items": []})
    real = pages({"items": []})

    asyncio.run(broker(tmp_path, demo, "demo").trades(SINCE))
    asyncio.run(broker(tmp_path, real, "real").trades(SINCE))

    assert demo.seen[0].url.path == "/api/v1/trading/info/trade/demo/history"  # type: ignore[attr-defined]
    assert real.seen[0].url.path == "/api/v1/trading/info/trade/history"  # type: ignore[attr-defined]


def test_a_mode_that_is_not_an_etoro_account_is_refused() -> None:
    """`paper` and `approval` are MOVRvest's modes, not eToro's."""

    assert require_trading_account("demo") == "demo"

    for mode in ("paper", "approval"):
        with pytest.raises(RuntimeError, match="TRADING_MODE"):
            require_trading_account(mode)


def test_the_window_is_the_callers_and_is_recorded(tmp_path) -> None:
    """
    `minDate` is required and has no default here.

    A window nobody chose would silently decide how much history the
    archive holds — and the capture records the query, so what was asked
    for can be checked afterwards.
    """

    handler = pages({"items": []})

    asyncio.run(broker(tmp_path, handler).trades(SINCE))

    assert handler.seen[0].url.params["minDate"] == "2026-01-01"  # type: ignore[attr-defined]

    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())

    assert saved["metadata"]["query_parameters"]["minDate"] == "2026-01-01"


def test_pages_are_walked_but_never_without_a_ceiling(tmp_path) -> None:
    """
    The read budget is pooled across most endpoints.

    A loop that follows "next" until it runs out spends an allowance the
    rest of the platform is also drawing on.
    """

    handler = pages({"items": [1, 2]})

    async def walk():
        return [
            page
            async for page in broker(tmp_path, handler).all_trades(
                SINCE, page_size=2, max_pages=3
            )
        ]

    collected = asyncio.run(walk())

    assert len(collected) == 3
    assert [r.url.params["page"] for r in handler.seen] == ["1", "2", "3"]  # type: ignore[attr-defined]


def test_a_short_page_is_the_last_page(tmp_path) -> None:
    handler = pages({"items": [1, 2]}, {"items": [3]})

    async def walk():
        return [
            page
            async for page in broker(tmp_path, handler).all_trades(
                SINCE, page_size=2, max_pages=9
            )
        ]

    assert len(asyncio.run(walk())) == 2


def test_a_trade_page_may_be_a_bare_list(tmp_path) -> None:
    """
    It is. The live API returns a JSON array for trade history.

    Coercing every body to an object rejected a perfectly good 200
    carrying an empty list — the broker does not get to decide what shape
    the API replies in.
    """

    handler = pages([1, 2], [3])

    async def walk():
        return [
            page
            async for page in broker(tmp_path, handler).all_trades(
                SINCE, page_size=2, max_pages=9
            )
        ]

    collected = asyncio.run(walk())

    assert collected == [[1, 2], [3]]


def test_an_unrecognised_shape_stops_rather_than_guessing(tmp_path) -> None:
    """An extra request costs the shared budget; a wrong guess loops."""

    handler = pages({"somethingElse": [1, 2, 3]})

    async def walk():
        return [
            page
            async for page in broker(tmp_path, handler).all_trades(
                SINCE, page_size=2, max_pages=9
            )
        ]

    assert len(asyncio.run(walk())) == 1


def test_cash_transactions_paginate_by_cursor_not_page_number(tmp_path) -> None:
    """A different style from the trade history, on the same archive."""

    handler = pages({"transactions": []})

    asyncio.run(broker(tmp_path, handler).cash_transactions("acc-1", page_token="abc"))

    request = handler.seen[0]  # type: ignore[attr-defined]

    assert request.url.path == "/api/v1/money/accounts/cash/acc-1/transactions"
    assert request.url.params["pageToken"] == "abc"


def test_a_balance_window_is_optional_and_omitted_when_absent(tmp_path) -> None:
    handler = pages({"balances": []})

    asyncio.run(broker(tmp_path, handler).balances())

    params = handler.seen[0].url.params  # type: ignore[attr-defined]

    assert params["displayCurrency"] == "USD"
    assert "fromDate" not in params
