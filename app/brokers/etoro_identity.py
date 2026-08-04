"""Who the configured credentials belong to, and what they may do."""

from __future__ import annotations

from typing import Any

import httpx

from app.brokers.etoro_client import EtoroClient
from app.config import Settings
from app.domain.api_grant import ApiGrant


class EtoroIdentityBroker:
    """
    Read `GET /api/v1/me`.

    The cheapest question the platform can ask about itself: are these
    credentials valid, which accounts do they reach, and — the one that
    matters before any execution path is ever written — do they carry
    write scope.
    """

    PATH = "/api/v1/me"

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        api: EtoroClient | None = None,
    ) -> None:
        self._api = api or EtoroClient(settings, client=client)

    async def fetch(self) -> ApiGrant:
        body: Any = await self._api.get(self.PATH, endpoint="me")

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected eToro identity response")

        return ApiGrant.from_payload(body)
