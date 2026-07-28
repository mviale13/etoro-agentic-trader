from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.config import Settings


class EtoroWatchlistBroker:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    def _headers(self) -> dict[str, str]:
        if not self._settings.etoro_api_key or not self._settings.etoro_user_key:
            raise RuntimeError("Missing ETORO_API_KEY or ETORO_USER_KEY")

        return {
            "x-api-key": self._settings.etoro_api_key,
            "x-user-key": self._settings.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
        }

    async def fetch(self) -> dict[str, Any]:
        url = f"{self._settings.etoro_base_url}/api/v1/watchlists"

        if self._client is not None:
            response = await self._client.get(
                url,
                headers=self._headers(),
            )
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url,
                    headers=self._headers(),
                )

        response.raise_for_status()

        body = response.json()

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected eToro watchlist response")

        return body
