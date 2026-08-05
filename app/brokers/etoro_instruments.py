"""Instrument metadata, as eToro returns it."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx

from app.brokers.etoro_client import EtoroClient
from app.config import Settings


class EtoroInstrumentsBroker:
    """
    Ask the broker to describe instruments by id.

    The watchlists are the usual source of an instrument's identity, but
    they only describe what the investor watches. A holding can exist on
    no watchlist at all, and this endpoint is the broker's own catalog
    entry for it — symbol, display name, instrument type — measured at
    the same source the position itself comes from.
    """

    PATH = "/api/v1/market-data/instruments"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        api: EtoroClient | None = None,
    ) -> None:
        self._settings = settings
        self._api = api or EtoroClient(settings, client=client)

    async def fetch(self, instrument_ids: Sequence[int]) -> dict[str, Any]:
        body = await self._api.get(
            self.PATH,
            endpoint="marketDataInstruments",
            params={
                "instrumentIds": ",".join(
                    str(instrument_id) for instrument_id in instrument_ids
                ),
            },
        )

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected eToro instruments response")

        return body
