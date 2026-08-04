"""The record of what actually happened, as eToro holds it."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date
from typing import Any

import httpx

from app.brokers.etoro_client import EtoroClient
from app.config import Settings


def require_trading_account(mode: str) -> str:
    """
    The account these paths address, or a refusal.

    `paper` and `approval` are MOVRvest's own modes, not eToro accounts.
    Reading a live account while configured for either would report one
    account's history under another's name.
    """

    if mode in ("demo", "real"):
        return mode

    raise RuntimeError(
        "Trading history requires TRADING_MODE=demo or TRADING_MODE=real"
    )


class EtoroHistoryBroker:
    """
    Read the histories the platform has never had: trades, balances, cash.

    Every decision so far rests on a snapshot of now — today's positions,
    today's prices. None of it can say what the account did, which is what
    scoring a past decision against its outcome will eventually need.

    Pagination is walked deliberately and never without a ceiling. The
    read budget is 60 requests a minute pooled across most endpoints, so a
    loop that follows "next" until it runs out is one that spends someone
    else's allowance too.
    """

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        api: EtoroClient | None = None,
    ) -> None:
        self._settings = settings
        self._api = api or EtoroClient(settings, client=client)

    def _trades_path(self) -> str:
        # Unlike `/pnl`, the real variant carries no account segment at
        # all — it is the absence of `demo` that selects it.
        mode = require_trading_account(self._settings.trading_mode)

        return (
            "/api/v1/trading/info/trade/demo/history"
            if mode == "demo"
            else "/api/v1/trading/info/trade/history"
        )

    async def trades(
        self,
        since: date,
        page: int = 1,
        page_size: int = 100,
    ) -> Any:
        """
        One page of closed trades from `since` onward.

        `minDate` is required by the API and has no default here. A window
        the caller did not choose would silently decide how much history
        the archive holds.
        """

        # Returned as a JSON array, not an object. Coercing every body to
        # a dict rejected a perfectly good 200 carrying an empty list —
        # the broker does not get to decide what shape the API replies in.
        return await self._api.get(
            self._trades_path(),
            endpoint="trade-history",
            params={
                "minDate": since.isoformat(),
                "page": page,
                "pageSize": page_size,
            },
        )

    async def all_trades(
        self,
        since: date,
        page_size: int = 100,
        max_pages: int = 10,
    ) -> AsyncIterator[Any]:
        """
        Walk the pages, up to a ceiling the caller sets.

        Each page is archived separately with the page number it carried,
        so the capture can be replayed and its completeness checked rather
        than assumed.
        """

        for page in range(1, max_pages + 1):
            body = await self.trades(since, page=page, page_size=page_size)

            yield body

            if not self._has_more(body, page_size):
                return

    async def balances(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        display_currency: str = "USD",
    ) -> Any:
        """Historical balance snapshots, which nothing has ever recorded."""

        params: dict[str, Any] = {"displayCurrency": display_currency}

        if from_date is not None:
            params["fromDate"] = from_date.isoformat()

        if to_date is not None:
            params["toDate"] = to_date.isoformat()

        return await self._api.get(
            "/api/v1/balances/history",
            endpoint="balance-history",
            params=params,
        )

    async def cash_transactions(
        self,
        account_id: str,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> Any:
        """
        Deposits, withdrawals, dividends, fees — paginated by cursor.

        `account_id` is a cash account identifier, and is **not** the CID
        from `/api/v1/me`: passing the demo CID returns
        `400 "The value ... is not valid"`. Which route lists the cash
        account ids has not been established, so no caller supplies one
        yet and none is guessed at here.

        A different pagination style from the trade history, which is why
        the archive records the query it was fetched with rather than
        assuming one shape.
        """

        params: dict[str, Any] = {"pageSize": page_size}

        if page_token is not None:
            params["pageToken"] = page_token

        return await self._api.get(
            f"/api/v1/money/accounts/cash/{account_id}/transactions",
            endpoint="cash-transactions",
            params=params,
        )

    @staticmethod
    def _has_more(body: Any, page_size: int) -> bool:
        """
        Whether a further page is worth a request.

        A short page is the last page. Where the shape is unrecognised this
        stops rather than guessing — an extra request costs the shared
        budget, and a wrong guess about "next" loops.
        """

        if isinstance(body, list):
            return len(body) >= page_size

        if not isinstance(body, dict):
            return False

        for key in ("items", "trades", "data", "results"):
            value = body.get(key)

            if isinstance(value, list):
                return len(value) >= page_size

        return False
