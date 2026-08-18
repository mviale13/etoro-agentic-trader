"""Personal Ticker News — three gates, one page, one identity decision.

The feature is private, personal and single-user, and it stays off. It
runs only when a build has enabled it, an operator has confirmed the
personal-use boundary in the provider's own terms, and a key exists.
Any of those missing is a worded unavailable state and **no provider
call is attempted** — a gate that only refuses after asking has not
gated anything.

The flow is fixed by `MASSIVE_FREE_PERSONAL_NEWS_MEASUREMENT.md`:

```text
one page, at most 50, next_url ignored
    ↓
the oldest published_utc on that page
    ↓
who holds the ticker today, and who held it then
    ↓
same CIK, or nothing is shown
```

**Identity is decided before anything is displayed**, and it is decided
for the whole page. A news item carries the bare symbol and no CIK, so
where the window spans a reassignment there is no way to say which
company any individual article belongs to — and the honest response is
to show none of them rather than to show them under a name that may be
wrong.

**This is a window-boundary test, not per-article identity resolution.**
An article published within days of a reassignment can still sit on the
permitted side of it. Closing that would cost one reference call for
every distinct article date, which the five-a-minute allowance cannot
pay. The limit is stated rather than hidden.

Nothing here writes to disk, reaches a model, creates a
`CompanyDevelopment`, or is read by any scoring, committee, decision or
recommendation path.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from app.config import Settings, get_settings
from app.domain.personal_news import (
    LeadStatus,
    NewsOutcome,
    PersonalNewsLead,
    PersonalNewsResult,
)
from app.providers.massive_news_provider import (
    MassiveNewsProvider,
    MassiveUnavailable,
    now_utc,
)

#: The exact words an operator must set to confirm that this install is
#: the single personal non-commercial user the provider's Individuals
#: terms describe. Exact rather than truthy, because "yes" would be
#: something a person could set without reading what they agreed to.
PERSONAL_USE_CONFIRMATION = "I_CONFIRM_PERSONAL_SINGLE_USER"

#: What turns the feature on at all. Off unless it says one of these.
_ENABLED = ("true", "1", "on", "yes")


def _enabled(settings: Settings) -> bool:
    return settings.movrvest_personal_news.strip().casefold() in _ENABLED


def _confirmed(settings: Settings) -> bool:
    return settings.movrvest_personal_news_use.strip() == PERSONAL_USE_CONFIRMATION


def is_available(settings: Settings | None = None) -> bool:
    """Whether all three gates are open, asked without calling anything."""

    settings = settings or get_settings()

    return (
        _enabled(settings)
        and _confirmed(settings)
        and bool(settings.massive_api_key.strip())
    )


def _safe_article_url(url: str) -> bool:
    """Whether this is a plain HTTPS address a browser may be handed.

    The link is opened by the reader, externally, and is never fetched,
    proxied or resolved here — so the only question is whether it is a
    well-formed HTTPS URL with a host. Anything else is dropped rather
    than rendered as an inert or dangerous link.
    """

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    return parsed.scheme == "https" and bool(parsed.netloc)


def _published(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


class PersonalTickerNewsService:
    """Recent articles Massive associates with one ticker, or a reason."""

    def __init__(
        self,
        provider: MassiveNewsProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider

    def _open(self) -> MassiveNewsProvider | None:
        if self._provider is not None:
            return self._provider

        if not is_available(self._settings):
            return None

        return MassiveNewsProvider(self._settings.massive_api_key.strip())

    def news_for(self, ticker: str) -> PersonalNewsResult:
        """One asking of one ticker. Never raises; always words itself."""

        symbol = ticker.upper().strip()
        asked_at = now_utc()

        if self._provider is None and not is_available(self._settings):
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.NOT_ENABLED,
                retrieved_at=asked_at,
            )

        provider = self._open()

        if provider is None:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.NOT_ENABLED,
                retrieved_at=asked_at,
            )

        try:
            page = provider.news(symbol)
        except MassiveUnavailable:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.PROVIDER_UNAVAILABLE,
                retrieved_at=asked_at,
            )

        leads = self._leads(symbol, page)

        if not leads:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.NO_ITEMS_RETURNED,
                retrieved_at=asked_at,
            )

        oldest = min(lead.published_at for lead in leads).date()

        try:
            today = provider.identity(symbol)
            then = provider.identity(symbol, on=oldest)
        except MassiveUnavailable:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.PROVIDER_UNAVAILABLE,
                retrieved_at=asked_at,
            )

        return self._decided(symbol, leads, today, then, asked_at, oldest)

    def _decided(
        self,
        symbol: str,
        leads: tuple[PersonalNewsLead, ...],
        today: object,
        then: object,
        asked_at: datetime,
        oldest: date,
    ) -> PersonalNewsResult:
        """The identity gate, applied to the whole page before display."""

        now_cik = getattr(today, "cik", "") or ""
        then_cik = getattr(then, "cik", "") or ""

        if not now_cik or not then_cik:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.IDENTITY_UNRESOLVED,
                retrieved_at=asked_at,
                identity_now=now_cik,
                identity_at_oldest=then_cik,
            )

        if now_cik != then_cik:
            return PersonalNewsResult(
                queried_ticker=symbol,
                outcome=NewsOutcome.ISSUER_REASSIGNED,
                retrieved_at=asked_at,
                identity_now=now_cik,
                identity_at_oldest=then_cik,
            )

        return PersonalNewsResult(
            queried_ticker=symbol,
            outcome=NewsOutcome.DISPLAY_ONLY,
            retrieved_at=asked_at,
            leads=leads,
            identity_now=now_cik,
            identity_at_oldest=then_cik,
        )

    def _leads(
        self, symbol: str, page: list[dict[str, Any]]
    ) -> tuple[PersonalNewsLead, ...]:
        """The provider's page, in the provider's order, minus what cannot show.

        Three removals and no fourth. An item is dropped where the
        queried ticker is not among its associations, where its provider
        id has already appeared on this page, or where its article URL is
        not a plain HTTPS address. **Nothing is dropped for naming too
        many tickers** — that count is disclosed, and no measurement
        earned a threshold.

        De-duplication is exact provider id and nothing else. Two
        articles with similar headlines are two articles; deciding they
        describe one development is the judgment this feature does not
        make.
        """

        seen: set[str] = set()
        kept: list[PersonalNewsLead] = []

        for item in page:
            identifier = str(item.get("id", "") or "")

            if not identifier or identifier in seen:
                continue

            associated = tuple(
                str(symbol_seen)
                for symbol_seen in (item.get("tickers") or [])
                if isinstance(symbol_seen, str)
            )

            if symbol not in associated:
                continue

            url = str(item.get("article_url", "") or "")

            if not _safe_article_url(url):
                continue

            published = _published(str(item.get("published_utc", "") or ""))

            if published is None:
                continue

            publisher = item.get("publisher")
            name = (
                str(publisher.get("name", "") or "")
                if isinstance(publisher, dict)
                else ""
            )

            seen.add(identifier)
            kept.append(
                PersonalNewsLead(
                    provider_article_id=identifier,
                    queried_ticker=symbol,
                    associated_tickers=associated,
                    headline=str(item.get("title", "") or ""),
                    provider_summary=str(item.get("description", "") or ""),
                    publisher_name=name,
                    author=str(item.get("author", "") or ""),
                    published_at=published,
                    article_url=url,
                    status=LeadStatus.DISPLAY_ONLY,
                )
            )

        return tuple(kept)
