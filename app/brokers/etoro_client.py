"""One door to the eToro API, and one place that records what it said."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.config import Settings
from app.infrastructure.evidence import VersionedSnapshotStore


@dataclass
class RateBudget:
    """
    What eToro says is left of the request allowance.

    Nothing here is assumed. eToro reports `ratelimit-limit`,
    `ratelimit-remaining` and `ratelimit-reset` on every response, and this
    only ever repeats back what those headers said. A response that carries
    no such headers leaves the budget unknown, and an unknown budget is not
    throttled against — inventing a limit would be as wrong here as
    inventing a price.
    """

    limit: int | None = None
    remaining: int | None = None
    resets_at: datetime | None = None

    def observe(
        self,
        headers: Any,
        now: datetime | None = None,
    ) -> None:
        """Read the allowance out of a response."""

        moment = now or datetime.now(UTC)

        self.limit = self._integer(headers.get("ratelimit-limit")) or self.limit

        remaining = self._integer(headers.get("ratelimit-remaining"))

        if remaining is not None:
            self.remaining = remaining

        reset_in = self._integer(headers.get("ratelimit-reset"))

        if reset_in is not None:
            self.resets_at = moment + timedelta(seconds=reset_in)

    def pause_needed(
        self,
        now: datetime | None = None,
    ) -> float:
        """
        Seconds to wait before spending another request.

        Zero whenever the allowance is unknown or not yet exhausted. This
        waits for the window to turn over rather than pacing requests
        across it: the platform makes a burst of calls per cycle and then
        goes quiet, so the honest constraint is the ceiling, not a rhythm.
        """

        if self.remaining is None or self.remaining > 0:
            return 0.0

        if self.resets_at is None:
            return 0.0

        moment = now or datetime.now(UTC)

        return max(0.0, (self.resets_at - moment).total_seconds())

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None


class EtoroClient:
    """
    Every eToro request goes through here, and every response is kept.

    Before this, each broker built its own headers, spent the shared
    request allowance without knowing what was left of it, and decided for
    itself whether the response was worth keeping — so `/pnl` was archived
    and `/watchlists` was read and thrown away.

    A response is evidence whatever its status. A 429 is the most useful
    reply the platform can receive about its own request budget, and
    discarding it would leave the one question this class exists to answer
    unanswerable after the fact.
    """

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        evidence_store: VersionedSnapshotStore | None = None,
        budget: RateBudget | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._settings = settings
        self._client = client
        self._store = evidence_store or VersionedSnapshotStore()
        self._budget = budget or RateBudget()
        self._timeout = timeout
        self._gate = asyncio.Lock()

    @property
    def budget(self) -> RateBudget:
        return self._budget

    async def get(
        self,
        path: str,
        *,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Fetch, archive, and return the decoded body."""

        headers = self._headers()
        url = f"{self._settings.etoro_base_url}{path}"

        await self._await_allowance()

        started = time.perf_counter()

        if self._client is not None:
            response = await self._client.get(url, headers=headers, params=params)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers, params=params)

        latency_ms = (time.perf_counter() - started) * 1000

        self._budget.observe(response.headers)

        self._capture(
            endpoint=endpoint,
            path=path,
            params=params,
            response=response,
            request_id=headers["x-request-id"],
            latency_ms=latency_ms,
        )

        response.raise_for_status()

        return response.json()

    async def _await_allowance(self) -> None:
        """Wait for the window to turn over if the allowance is spent."""

        async with self._gate:
            pause = self._budget.pause_needed()

            if pause > 0:
                await asyncio.sleep(pause)

                # The window has turned over. What is left is unknown until
                # a response says so, which is different from knowing it is
                # full.
                self._budget.remaining = None

    def _capture(
        self,
        *,
        endpoint: str,
        path: str,
        params: dict[str, Any] | None,
        response: httpx.Response,
        request_id: str,
        latency_ms: float,
    ) -> None:
        try:
            payload: Any = response.json()
        except ValueError:
            payload = {"unparsed_body": response.text}

        self._store.save(
            broker="etoro",
            environment=self._settings.trading_mode,
            endpoint=endpoint,
            payload=payload,
            metadata={
                "http_method": "GET",
                "http_status": response.status_code,
                "request_path": path,
                # Named in the API inventory and previously unrecorded. A
                # paginated capture that does not say which page it holds
                # is a corrupted archive.
                "query_parameters": dict(params or {}),
                "request_id": request_id,
                "latency_ms": round(latency_ms, 3),
                "response_headers": dict(response.headers),
            },
        )

    def _headers(self) -> dict[str, str]:
        if not self._settings.etoro_api_key or not self._settings.etoro_user_key:
            raise RuntimeError(
                "Missing ETORO_API_KEY or ETORO_USER_KEY in the local .env file"
            )

        return {
            "x-api-key": self._settings.etoro_api_key,
            "x-user-key": self._settings.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
        }
