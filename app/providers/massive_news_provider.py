"""Massive's two permitted endpoints, behind one process-wide limiter.

Stocks Basic allows five requests a minute, and Massive returns **no
rate-limit header of any kind** — measured over 30 responses in
`MASSIVE_FREE_PERSONAL_NEWS_MEASUREMENT.md`. So the allowance cannot be
observed from a response and has to be counted here, on this side of the
wire, by a scheduler that every caller shares.

Three rules the measurement earned, each enforced below rather than
documented and hoped for:

- **One scheduler for the process.** Two callers asking about two
  tickers are two requests against one allowance. A per-instance limiter
  would pace each of them perfectly and still burst.
- **No retry, ever.** A 429 is an answer, and asking again is how a
  personal allowance becomes an abuse complaint.
- **`next_url` is not followed.** The provider's own cursor returned
  items *newer* than the first page's newest, with zero overlap, and
  dropped the page size. It is not a continuation and this module does
  not treat it as one.

The key travels in an `Authorization` header and nowhere else — never a
query string, never a URL, never an argument. `repr` is overridden on
everything that holds it, and provider text is redacted before it can
reach an exception or a log.
"""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx

BASE = "https://api.polygon.io"

#: Stocks Basic permits five calls a minute. Thirteen seconds is that
#: allowance with the rounding in the provider's favour, and it is the
#: spacing the measurement itself ran at without a single 429.
MINIMUM_SPACING_SECONDS = 13.0

#: The largest first page this feature asks for. There is no second
#: page: see the module docstring on `next_url`.
MAXIMUM_PAGE = 50

TIMEOUT_SECONDS = 30.0

#: Anything shaped like a credential, removed before provider text is
#: shown, logged or raised. Deliberately blunt: a redactor that tries to
#: be precise about which long token was the key is a redactor that
#: misses one.
_CREDENTIAL = re.compile(
    r"(?i)(api[_-]?key|bearer|authorization)[=:\s]+\S+|\b[A-Za-z0-9_\-]{24,}\b"
)


def redacted(text: str) -> str:
    """Provider text with anything credential-shaped removed."""

    return _CREDENTIAL.sub("[REDACTED]", text)


class MassiveUnavailable(RuntimeError):
    """Massive could not be read, worded without any credential in it."""

    def __init__(self, reason: str) -> None:
        super().__init__(redacted(reason))


class RequestScheduler:
    """One allowance, one queue, one clock.

    Concurrent callers block on the same lock, so the spacing holds
    across threads rather than only within one. The clock and the sleep
    are injected so a test can pin the spacing without spending it.
    """

    def __init__(
        self,
        spacing: float = MINIMUM_SPACING_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._spacing = spacing
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last_start: float | None = None
        self._count = 0

    @property
    def requests_made(self) -> int:
        """What has been spent, because the provider will not say."""

        return self._count

    def wait_turn(self) -> None:
        """Block until this caller may start a request, then claim it."""

        with self._lock:
            if self._last_start is not None:
                elapsed = self._clock() - self._last_start

                if elapsed < self._spacing:
                    self._sleep(self._spacing - elapsed)

            self._last_start = self._clock()
            self._count += 1


#: The process-wide scheduler. Module level on purpose — the allowance
#: belongs to the key, not to whoever happened to construct a client.
SCHEDULER = RequestScheduler()


@dataclass(frozen=True, slots=True)
class TickerIdentity:
    """Who a symbol belonged to, on a date the provider was asked about."""

    ticker: str
    name: str
    cik: str
    composite_figi: str
    share_class_figi: str
    asked_for: date | None


class MassiveNewsProvider:
    """The two endpoints this feature is permitted to call, and no others.

    `/v2/reference/news` and `/v3/reference/tickers/{ticker}`. No
    Benzinga endpoint, no other Massive endpoint, no SDK, no MCP, no
    WebSocket, and no publisher article is ever fetched — the article URL
    is handed to the reader's own browser and this platform never opens
    it.
    """

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        scheduler: RequestScheduler | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client
        self._scheduler = scheduler or SCHEDULER

    def __repr__(self) -> str:
        """Never the key, however this object is printed or logged."""

        return f"{type(self).__name__}(api_key=[REDACTED])"

    __str__ = __repr__

    def news(self, ticker: str, limit: int = MAXIMUM_PAGE) -> list[dict[str, Any]]:
        """One page of articles the provider associates with this ticker.

        `next_url` is read from the payload and discarded, which is a
        decision rather than an omission.
        """

        payload = self._get(
            "/v2/reference/news",
            {
                "ticker": ticker,
                "limit": min(limit, MAXIMUM_PAGE),
                "order": "desc",
                "sort": "published_utc",
            },
        )

        results = payload.get("results")

        return list(results) if isinstance(results, list) else []

    def identity(self, ticker: str, on: date | None = None) -> TickerIdentity | None:
        """Who held this symbol, on that date or today.

        `None` where the provider has no record — which the caller must
        treat as unresolved rather than as permission.
        """

        payload = self._get(
            f"/v3/reference/tickers/{ticker}",
            {"date": on.isoformat()} if on is not None else {},
        )

        found = payload.get("results")

        if not isinstance(found, dict):
            return None

        return TickerIdentity(
            ticker=str(found.get("ticker", "")),
            name=str(found.get("name", "")),
            cik=str(found.get("cik", "") or ""),
            composite_figi=str(found.get("composite_figi", "") or ""),
            share_class_figi=str(found.get("share_class_figi", "") or ""),
            asked_for=on,
        )

    # ── the wire ────────────────────────────────────────────────────

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """One authenticated request, paced, unretried, never echoed."""

        self._scheduler.wait_turn()

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "MOVRvest personal",
        }

        try:
            if self._client is not None:
                response = self._client.get(BASE + path, params=params, headers=headers)
            else:
                response = self._live(BASE + path, params, headers)
        except Exception as error:
            # The exception's own text may carry the request; it is
            # rebuilt from the type alone rather than passed through.
            raise MassiveUnavailable(
                f"the request did not complete ({type(error).__name__})"
            ) from None

        if response.status_code == 429:
            raise MassiveUnavailable(
                "the personal request allowance for this minute is spent"
            )

        if response.status_code != 200:
            raise MassiveUnavailable(
                f"Massive answered {response.status_code}: "
                f"{redacted(response.text)[:200]}"
            )

        try:
            payload = response.json()
        except ValueError:
            raise MassiveUnavailable("Massive's answer was not readable") from None

        return payload if isinstance(payload, dict) else {}

    def _live(
        self, url: str, params: dict[str, Any], headers: dict[str, str]
    ) -> httpx.Response:
        """The one place this module opens a connection of its own.

        Separated from `_get` so the suite can block *this* and leave the
        pacing, the status handling and the redaction testable with an
        injected client. A guard on `_get` would have blocked the
        behaviour as well as the wire, which is how a seam ends up
        untested and trusted.
        """

        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            return client.get(url, params=params, headers=headers)


def now_utc() -> datetime:
    return datetime.now(UTC)
