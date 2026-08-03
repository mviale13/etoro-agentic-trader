"""The investor's watchlists, as eToro returns them."""

from __future__ import annotations

from typing import Any

import httpx

from app.brokers.etoro_client import EtoroClient
from app.config import Settings


class EtoroWatchlistBroker:
    """
    Read the watchlists, and keep what was read.

    This fetched and discarded. The watchlists are the only description
    the platform has of an instrument — its symbol, its name, its asset
    type, its exchange — so every decision about a security rests on a
    payload that was never archived, and no past state of it can be
    recovered.
    """

    PATH = "/api/v1/watchlists"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        api: EtoroClient | None = None,
    ) -> None:
        self._settings = settings
        self._api = api or EtoroClient(settings, client=client)

    async def fetch(self) -> dict[str, Any]:
        body = await self._api.get(self.PATH, endpoint="watchlists")

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected eToro watchlist response")

        return body
