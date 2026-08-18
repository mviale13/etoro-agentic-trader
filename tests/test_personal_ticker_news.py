"""Personal Ticker News: three gates, one page, one identity decision.

Every case is a shape `MASSIVE_FREE_PERSONAL_NEWS_MEASUREMENT.md`
measured against the live provider, reduced to the smallest payload that
reproduces it. No test opens a socket, reads a `.env`, writes a file or
sleeps in real time.
"""

from __future__ import annotations

import threading
from datetime import date

import pytest

from app.config import Settings
from app.domain.personal_news import (
    LeadStatus,
    NewsOutcome,
    ProviderSentiment,
    provider_sentiment_for,
)
from app.providers.massive_news_provider import (
    MAXIMUM_PAGE,
    MINIMUM_SPACING_SECONDS,
    MassiveNewsProvider,
    MassiveUnavailable,
    RequestScheduler,
    redacted,
)
from app.services.personal_ticker_news_service import (
    PERSONAL_USE_CONFIRMATION,
    PersonalTickerNewsService,
    is_available,
)

KEY = "test-key-never-a-real-one"


def settings(**overrides) -> Settings:
    """Settings that have never seen a `.env`, with the gates open."""

    base = {
        "massive_api_key": KEY,
        "movrvest_personal_news": "true",
        "movrvest_personal_news_use": PERSONAL_USE_CONFIRMATION,
    }
    base.update(overrides)

    return Settings(_env_file=None, **base)


def article(
    identifier: str = "a1",
    tickers: tuple[str, ...] = ("ADBE",),
    published: str = "2026-08-16T10:00:00Z",
    url: str = "https://publisher.example/story",
    title: str = "A headline the provider wrote",
) -> dict:
    return {
        "id": identifier,
        "tickers": list(tickers),
        "title": title,
        "description": "The provider's own summary.",
        "publisher": {"name": "The Motley Fool", "homepage_url": "https://x.example"},
        "author": "A Writer",
        "published_utc": published,
        "article_url": url,
        # Measured in the corpus. Only the exact queried ticker's
        # entry may ever be quoted, and only as a direction.
        "insights": [{"ticker": "ADBE", "sentiment": "positive"}],
        "amp_url": "https://publisher.example/amp",
        "keywords": ["software"],
    }


class StubProvider:
    """A provider that answers from a script and records what was asked."""

    def __init__(
        self,
        page: list[dict] | None = None,
        identities: dict[date | None, object] | None = None,
        news_error: bool = False,
        identity_error: bool = False,
    ) -> None:
        self._page = page if page is not None else [article()]
        self._identities = identities or {}
        self._news_error = news_error
        self._identity_error = identity_error
        self.news_calls: list[tuple[str, int]] = []
        self.identity_calls: list[tuple[str, date | None]] = []

    def news(self, ticker: str, limit: int = MAXIMUM_PAGE) -> list[dict]:
        self.news_calls.append((ticker, limit))

        if self._news_error:
            raise MassiveUnavailable("provider said no")

        return self._page

    def identity(self, ticker: str, on: date | None = None):
        self.identity_calls.append((ticker, on))

        if self._identity_error:
            raise MassiveUnavailable("provider said no")

        return self._identities.get(on)


class Identity:
    def __init__(self, cik: str, name: str = "Some Company") -> None:
        self.cik = cik
        self.name = name


def held(now: str, then: str) -> dict:
    """Identities keyed the way the service asks for them."""

    return {None: Identity(now), date(2026, 8, 16): Identity(then)}


def served(page=None, identities=None, **kwargs) -> tuple:
    stub = StubProvider(page=page, identities=identities, **kwargs)
    service = PersonalTickerNewsService(provider=stub, settings=settings())

    return service, stub


# ── the three runtime gates ─────────────────────────────────────────


def test_the_feature_is_off_unless_it_is_switched_on() -> None:
    """Default configuration runs nothing."""

    assert not is_available(Settings(_env_file=None))


@pytest.mark.parametrize(
    "closed",
    [
        {"movrvest_personal_news": ""},
        {"movrvest_personal_news": "false"},
        {"movrvest_personal_news_use": ""},
        {"movrvest_personal_news_use": "yes"},
        {"movrvest_personal_news_use": "i_confirm_personal_single_user"},
        {"massive_api_key": ""},
    ],
)
def test_every_gate_refuses_without_touching_the_provider(closed) -> None:
    """A gate that asks first has not gated anything.

    The confirmation is compared exactly: a lowercase spelling of the
    same words is not the phrase, because the point is that somebody
    read it.
    """

    assert not is_available(settings(**closed))

    class Exploding:
        def news(self, *args, **kwargs):
            raise AssertionError("a closed gate reached the provider")

        def identity(self, *args, **kwargs):
            raise AssertionError("a closed gate reached the provider")

    service = PersonalTickerNewsService(settings=settings(**closed))
    service._provider = None  # noqa: SLF001 - the point of the test

    result = service.news_for("ADBE")

    assert result.outcome is NewsOutcome.NOT_ENABLED
    assert "not enabled" in result.stated
    assert result.leads == ()


# ── the identity gate ───────────────────────────────────────────────


def test_a_stable_ticker_displays_its_page() -> None:
    """BA's measured identity: one CIK across seven years."""

    service, stub = served(identities=held("0000012927", "0000012927"))

    result = service.news_for("ADBE")

    assert result.outcome is NewsOutcome.DISPLAY_ONLY
    assert len(result.leads) == 1
    assert result.leads[0].status is LeadStatus.DISPLAY_ONLY
    assert stub.identity_calls == [("ADBE", None), ("ADBE", date(2026, 8, 16))]


def test_bcs_passes_under_its_measured_identity() -> None:
    """Barclays: CIK 0000312069, the same as its 20-F already held."""

    service, _ = served(
        page=[article("b1", tickers=("BCS",))],
        identities=held("0000312069", "0000312069"),
    )

    assert service.news_for("BCS").outcome is NewsOutcome.DISPLAY_ONLY


def test_para_refuses_because_the_ticker_changed_hands() -> None:
    """The measured case, and the reason the whole page is refused.

    `PARA` resolves to Banzai International today and to Paramount
    Global at the oldest returned article's date. A news item carries
    only the symbol, so no article in the window can be attributed —
    and none is shown.
    """

    service, _ = served(
        page=[article("p1", tickers=("PARA",))],
        identities=held(now="0001826011", then="0000813828"),
    )

    result = service.news_for("PARA")

    assert result.outcome is NewsOutcome.ISSUER_REASSIGNED
    assert result.leads == ()
    assert "0001826011" in result.stated
    assert "0000813828" in result.stated


@pytest.mark.parametrize(
    "identities",
    [
        {None: Identity(""), date(2026, 8, 16): Identity("0000796343")},
        {None: Identity("0000796343"), date(2026, 8, 16): Identity("")},
        {None: None, date(2026, 8, 16): Identity("0000796343")},
        {},
    ],
)
def test_an_unidentified_issuer_is_not_a_permissive_default(identities) -> None:
    service, _ = served(identities=identities)

    result = service.news_for("ADBE")

    assert result.outcome is NewsOutcome.IDENTITY_UNRESOLVED
    assert result.leads == ()


def test_nothing_is_displayed_before_identity_is_settled() -> None:
    """The news page is fetched first, but never returned on its own."""

    service, stub = served(identity_error=True)

    result = service.news_for("ADBE")

    assert stub.news_calls, "the page was fetched"
    assert result.outcome is NewsOutcome.PROVIDER_UNAVAILABLE
    assert result.leads == ()


# ── the page, and what may be shown of it ───────────────────────────


def test_the_page_is_capped_and_the_cursor_is_never_followed() -> None:
    """`next_url` returned items newer than page one, with no overlap."""

    service, stub = served(identities=held("1", "1"))
    service.news_for("ADBE")

    assert stub.news_calls == [("ADBE", MAXIMUM_PAGE)]
    assert MAXIMUM_PAGE == 50


def test_duplicate_provider_ids_go_and_provider_order_stays() -> None:
    """Exact id equality only. Similar headlines are two articles."""

    page = [
        article("a1", published="2026-08-16T10:00:00Z", title="First"),
        article("a2", published="2026-08-16T09:00:00Z", title="First"),
        article("a1", published="2026-08-16T08:00:00Z", title="A repeat"),
        article("a3", published="2026-08-16T07:00:00Z", title="Third"),
    ]
    service, _ = served(page=page, identities=held("1", "1"))

    result = service.news_for("ADBE")

    assert [lead.provider_article_id for lead in result.leads] == ["a1", "a2", "a3"]
    # The near-identical headline survived: it is a different article.
    assert [lead.headline for lead in result.leads] == ["First", "First", "Third"]


def test_an_article_that_does_not_name_the_ticker_is_dropped() -> None:
    page = [
        article("a1", tickers=("ADBE", "MSFT")),
        article("a2", tickers=("MSFT", "NVDA")),
    ]
    service, _ = served(page=page, identities=held("1", "1"))

    result = service.news_for("ADBE")

    assert [lead.provider_article_id for lead in result.leads] == ["a1"]


def test_many_associations_are_disclosed_and_never_rejected() -> None:
    """A measured article carries 44 tickers. It is shown, with a caveat."""

    many = tuple(["ADBE"] + [f"T{n}" for n in range(43)])
    service, _ = served(page=[article("a1", tickers=many)], identities=held("1", "1"))

    lead = service.news_for("ADBE").leads[0]

    assert lead.associated_ticker_count == 44
    assert lead.stated_association() == (
        "This article is associated with 44 tickers; relevance to ADBE "
        "has not been verified."
    )


def test_a_single_association_still_claims_nothing() -> None:
    service, _ = served(identities=held("1", "1"))

    lead = service.news_for("ADBE").leads[0]

    assert lead.associated_ticker_count == 1
    assert "has not been verified" in lead.stated_association()


@pytest.mark.parametrize(
    "url",
    [
        "http://publisher.example/story",
        "javascript:alert(1)",
        "ftp://publisher.example/story",
        "not a url at all",
        "",
        "https://",
    ],
)
def test_only_a_plain_https_publisher_url_may_be_offered(url) -> None:
    service, _ = served(page=[article("a1", url=url)], identities=held("1", "1"))

    assert service.news_for("ADBE").outcome is NewsOutcome.NO_ITEMS_RETURNED


def test_an_empty_page_says_only_what_it_means() -> None:
    service, _ = served(page=[], identities=held("1", "1"))

    result = service.news_for("ADBE")

    assert result.outcome is NewsOutcome.NO_ITEMS_RETURNED
    assert "does not mean no material development occurred" in result.stated


def test_the_provider_failing_is_a_worded_result_not_an_exception() -> None:
    service, _ = served(news_error=True)

    assert service.news_for("ADBE").outcome is NewsOutcome.PROVIDER_UNAVAILABLE


# ── what may never leave the module ─────────────────────────────────


def test_no_lead_carries_reasoning_a_timestamp_it_lacks_or_a_cursor() -> None:
    """The provider's argument stays behind; only its direction is quoted."""

    service, _ = served(identities=held("1", "1"))
    lead = service.news_for("ADBE").leads[0]

    for forbidden in (
        "sentiment_reasoning",
        "insights",
        "updated_at",
        "next_url",
        "request_id",
    ):
        assert not hasattr(lead, forbidden), forbidden

    # The direction itself is carried, and it is the exact ticker's.
    assert lead.provider_sentiment is ProviderSentiment.POSITIVE


def test_the_route_payload_carries_nothing_it_may_not() -> None:
    from fastapi.testclient import TestClient

    from app.api.main import app

    with TestClient(app) as client:
        payload = client.get("/personal-news/ADBE").json()

    # Off by default, so this is the unavailable wording rather than news.
    assert payload["outcome"] == NewsOutcome.NOT_ENABLED.value
    assert payload["displayable"] is False
    assert payload["heading"] == "Ticker News"
    assert "have not been assessed or verified by MOVRvest" in payload["explanation"]

    flattened = str(payload).casefold()

    # `sentiment_reasoning` and not `sentiment`: the disclosure names
    # the icons, so the word itself is expected. What may never appear
    # is the provider's argument, its raw payload, or a credential.
    for forbidden in (
        "sentiment_reasoning",
        "insights",
        "next_url",
        "apikey",
        "authorization",
    ):
        assert forbidden not in flattened, forbidden


# ── the shared limiter ──────────────────────────────────────────────


class FakeClock:
    """A monotonic clock a test owns, and a sleep that only advances it."""

    def __init__(self) -> None:
        self.now = 1_000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def test_the_limiter_paces_without_spending_real_time() -> None:
    clock = FakeClock()
    scheduler = RequestScheduler(spacing=13.0, clock=clock, sleep=clock.sleep)

    scheduler.wait_turn()
    assert clock.slept == [], "the first request waits for nothing"

    scheduler.wait_turn()
    assert clock.slept == [13.0]

    clock.now += 20.0
    scheduler.wait_turn()
    assert clock.slept == [13.0], "a caller that arrived late waits no more"

    assert scheduler.requests_made == 3


def test_the_spacing_is_at_least_thirteen_seconds() -> None:
    assert MINIMUM_SPACING_SECONDS >= 13.0


def test_concurrent_callers_queue_behind_one_allowance() -> None:
    """Two tickers are two requests against one key, not two allowances."""

    clock = FakeClock()
    scheduler = RequestScheduler(spacing=13.0, clock=clock, sleep=clock.sleep)
    started: list[float] = []

    # All four release together, so they genuinely contend for the lock.
    ready = threading.Barrier(4)

    def caller() -> None:
        ready.wait(timeout=5)
        scheduler.wait_turn()
        started.append(clock.now)

    threads = [threading.Thread(target=caller) for _ in range(4)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=10)

    assert all(not thread.is_alive() for thread in threads), "a caller never returned"
    assert scheduler.requests_made == 4

    # Four requests, three waits, and every wait the full spacing —
    # which is what a per-instance limiter would not have produced.
    assert clock.slept == [13.0, 13.0, 13.0]
    assert len(started) == 4


def test_a_shared_module_scheduler_exists() -> None:
    from app.providers import massive_news_provider

    assert isinstance(massive_news_provider.SCHEDULER, RequestScheduler)
    assert MassiveNewsProvider(KEY)._scheduler is massive_news_provider.SCHEDULER  # noqa: SLF001


# ── the credential ──────────────────────────────────────────────────


def test_the_key_never_appears_in_a_representation() -> None:
    provider = MassiveNewsProvider("super-secret-key-value-1234567890")

    assert "super-secret" not in repr(provider)
    assert "super-secret" not in str(provider)
    assert "[REDACTED]" in repr(provider)


def test_provider_text_is_redacted_before_it_can_be_raised() -> None:
    leaked = "Bearer abcdefghijklmnopqrstuvwxyz123456 rejected"

    assert "abcdefghijklmnopqrstuvwxyz123456" not in redacted(leaked)
    assert "abcdefghijklmnopqrstuvwxyz123456" not in str(MassiveUnavailable(leaked))


def test_the_key_travels_in_a_header_and_never_in_a_url() -> None:
    """Recorded at the wire, without a socket and without a real key."""

    seen: dict = {}

    class Recorder:
        def get(self, url, params=None, headers=None):
            seen["url"] = url
            seen["params"] = params or {}
            seen["headers"] = headers or {}

            class Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"results": []}

            return Response()

    clock = FakeClock()
    provider = MassiveNewsProvider(
        KEY,
        client=Recorder(),
        scheduler=RequestScheduler(clock=clock, sleep=clock.sleep),
    )
    provider.news("ADBE")

    assert seen["headers"]["Authorization"] == f"Bearer {KEY}"
    assert KEY not in seen["url"]
    assert KEY not in str(seen["params"])
    assert "apiKey" not in seen["params"]
    assert "apikey" not in str(seen["params"]).casefold()


def test_a_429_stops_without_a_retry() -> None:
    calls: list[int] = []

    class Limited:
        def get(self, url, params=None, headers=None):
            calls.append(1)

            class Response:
                status_code = 429
                text = "rate limited"

            return Response()

    clock = FakeClock()
    provider = MassiveNewsProvider(
        KEY,
        client=Limited(),
        scheduler=RequestScheduler(clock=clock, sleep=clock.sleep),
    )

    with pytest.raises(MassiveUnavailable):
        provider.news("ADBE")

    assert calls == [1], "a 429 was retried"


def test_a_429_reaches_the_reader_as_a_worded_result() -> None:
    service, _ = served(news_error=True)

    result = service.news_for("ADBE")

    assert result.outcome is NewsOutcome.PROVIDER_UNAVAILABLE
    assert "Nothing was retried" in result.stated


# ── isolation ───────────────────────────────────────────────────────


def test_the_provider_writes_nothing(tmp_path, monkeypatch) -> None:
    """A whole reading, with the filesystem watching."""

    import builtins

    opened: list = []
    real_open = builtins.open

    def watched(path, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened.append((str(path), mode))

        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", watched)

    service, _ = served(identities=held("1", "1"))
    service.news_for("ADBE")

    assert opened == []


def test_no_decision_path_imports_personal_news() -> None:
    """The feature is a display surface and reaches no judgment.

    Searched in the source rather than the import graph, because the
    next aggregate would arrive as a local import inside a function and
    a module-level graph would not see it.
    """

    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    forbidden = (
        "services/business_quality",
        "domain/business_quality",
        "services/recommendation",
        "domain/recommendation",
        "application/committees",
        "committee",
        "services/artificial_cio",
        "domain/company_development",
        "services/company_development",
        "domain/decision",
        "services/decision",
    )

    offenders = []

    for path in root.rglob("*.py"):
        relative = str(path.relative_to(root))

        if not any(relative.startswith(area) for area in forbidden):
            continue

        source = path.read_text()

        if "personal_ticker_news" in source or "personal_news" in source:
            offenders.append(relative)

    assert offenders == [], offenders


# ── the provider's sentiment: quoted narrowly, propagated nowhere ────


def insight(ticker: str, sentiment: str) -> dict:
    return {"ticker": ticker, "sentiment": sentiment, "sentiment_reasoning": "why"}


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        ("positive", ProviderSentiment.POSITIVE),
        ("bullish", ProviderSentiment.POSITIVE),
        ("POSITIVE", ProviderSentiment.POSITIVE),
        ("  Bullish ", ProviderSentiment.POSITIVE),
        ("negative", ProviderSentiment.NEGATIVE),
        ("bearish", ProviderSentiment.NEGATIVE),
        ("BEARISH", ProviderSentiment.NEGATIVE),
    ],
)
def test_two_spellings_of_one_direction_normalise_to_it(printed, expected) -> None:
    """`positive`/`bullish` and `negative`/`bearish` share one field."""

    assert provider_sentiment_for("ADBE", [insight("ADBE", printed)]) is expected


@pytest.mark.parametrize(
    "printed",
    ["neutral", "mixed", "unknown", "", "somewhat positive", "positive-ish"],
)
def test_anything_that_is_not_a_direction_is_no_icon(printed) -> None:
    assert provider_sentiment_for("ADBE", [insight("ADBE", printed)]) is None


@pytest.mark.parametrize(
    "insights",
    [
        None,
        [],
        "positive",
        [{"ticker": "ADBE"}],
        [{"sentiment": "positive"}],
        ["positive"],
    ],
)
def test_a_missing_or_malformed_insight_is_no_icon(insights) -> None:
    assert provider_sentiment_for("ADBE", insights) is None


def test_only_the_exact_queried_tickers_insight_is_read() -> None:
    """An article naming many companies carries many opinions.

    The one that may be shown is the one about the company being asked
    about — never a neighbour's, and never the first in the list.
    """

    insights = [
        insight("MSFT", "negative"),
        insight("NVDA", "bearish"),
        insight("ADBE", "positive"),
        insight("AAPL", "bearish"),
    ]

    assert provider_sentiment_for("ADBE", insights) is ProviderSentiment.POSITIVE
    assert provider_sentiment_for("MSFT", insights) is ProviderSentiment.NEGATIVE
    assert provider_sentiment_for("KO", insights) is None


def test_another_tickers_insight_never_stands_in_for_a_missing_one() -> None:
    """The queried ticker has no insight, so there is no icon."""

    assert provider_sentiment_for("ADBE", [insight("MSFT", "positive")]) is None


@pytest.mark.parametrize(
    "insights",
    [
        [insight("ADBE", "positive"), insight("ADBE", "negative")],
        [insight("ADBE", "bullish"), insight("ADBE", "bearish")],
        [insight("ADBE", "positive"), insight("ADBE", "neutral")],
        [insight("ADBE", "neutral"), insight("ADBE", "bearish")],
    ],
)
def test_the_exact_ticker_disagreeing_with_itself_is_no_icon(insights) -> None:
    """Taking the first would hide it; taking a majority would decide it."""

    assert provider_sentiment_for("ADBE", insights) is None


def test_the_exact_ticker_agreeing_with_itself_is_still_read() -> None:
    repeated = [insight("ADBE", "positive"), insight("ADBE", "bullish")]

    assert provider_sentiment_for("ADBE", repeated) is ProviderSentiment.POSITIVE


def test_sentiment_is_never_inferred_from_the_words_of_an_article() -> None:
    """No insight, however the headline and summary read."""

    page = [
        {
            **article("a1"),
            "title": "Adobe soars on a stunning, record-breaking quarter",
            "description": "Excellent results beat every expectation.",
            "insights": [],
        }
    ]
    service, _ = served(page=page, identities=held("1", "1"))

    assert service.news_for("ADBE").leads[0].provider_sentiment is None


def test_sentiment_changes_neither_the_order_nor_the_membership() -> None:
    """The provider's order survives, and nothing is filtered by mood."""

    page = [
        {**article("a1"), "insights": [insight("ADBE", "negative")]},
        {**article("a2"), "insights": [insight("ADBE", "positive")]},
        {**article("a3"), "insights": []},
        {**article("a4"), "insights": [insight("ADBE", "bearish")]},
    ]
    service, _ = served(page=page, identities=held("1", "1"))

    leads = service.news_for("ADBE").leads

    assert [lead.provider_article_id for lead in leads] == ["a1", "a2", "a3", "a4"]
    assert [lead.provider_sentiment for lead in leads] == [
        ProviderSentiment.NEGATIVE,
        ProviderSentiment.POSITIVE,
        None,
        ProviderSentiment.NEGATIVE,
    ]


def test_the_icon_says_whose_classification_it_is() -> None:
    service, _ = served(identities=held("1", "1"))
    lead = service.news_for("ADBE").leads[0]

    assert lead.stated_sentiment() == "Massive sentiment: positive"


def test_the_disclosure_is_written_by_the_backend() -> None:
    from datetime import UTC, datetime

    from app.domain.personal_news import PersonalNewsResult

    result = PersonalNewsResult(
        queried_ticker="ADBE",
        outcome=NewsOutcome.DISPLAY_ONLY,
        retrieved_at=datetime(2026, 8, 18, tzinfo=UTC),
    )

    assert result.sentiment_notice == (
        "Sentiment icons, where present, show Massive's classification "
        "for this ticker. They are not MOVRvest analysis."
    )


def test_the_payload_carries_a_direction_and_never_the_reasoning() -> None:
    from fastapi.testclient import TestClient

    from app.api.main import app

    with TestClient(app) as client:
        payload = client.get("/personal-news/ADBE").json()

    assert "sentiment_notice" in payload
    assert "not MOVRvest analysis" in payload["sentiment_notice"]
    assert "sentiment_reasoning" not in str(payload)


# ── the event loop ──────────────────────────────────────────────────


def test_the_route_is_synchronous_so_it_cannot_block_the_event_loop() -> None:
    """Three paced requests are ~26 seconds of blocking sleep.

    On an `async def` path operation that happens on the event loop and
    stops the whole API. Declared `def`, FastAPI runs it in its worker
    threadpool instead.
    """

    import inspect

    from app.api.routes.personal_news import get_personal_ticker_news

    assert not inspect.iscoroutinefunction(get_personal_ticker_news)


def test_the_scheduler_stayed_synchronous_and_shared() -> None:
    """The fix is where the route runs, not what the limiter is."""

    import inspect

    from app.providers import massive_news_provider

    assert not inspect.iscoroutinefunction(RequestScheduler.wait_turn)
    assert isinstance(massive_news_provider.SCHEDULER, RequestScheduler)


# ── the dossier render ──────────────────────────────────────────────


def dossier_page() -> str:
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[1]
        / "apps/web/movrvest-web/app/dossiers/[symbol]/page.tsx"
    ).read_text()


def ticker_news_component() -> str:
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[1]
        / "apps/web/movrvest-web/components/dossier/TickerNews.tsx"
    ).read_text()


def test_the_dossier_never_awaits_the_news_before_it_renders() -> None:
    """The investment case must not wait on a discovery surface.

    One reading is three requests paced thirteen seconds apart, so an
    await here would hold the whole page behind roughly half a minute of
    something that reaches no part of it.
    """

    page = dossier_page()

    assert "getPersonalNews" not in page, "the page fetches the news itself"
    assert "await getPersonalNews" not in page


def test_the_news_is_streamed_behind_its_own_suspense_boundary() -> None:
    page = dossier_page()

    assert "<Suspense fallback={<TickerNewsFallback />}>" in page
    assert "<TickerNews symbol={dossier.symbol} />" in page

    # The fetch lives in the streamed component, not on the page.
    assert "await getPersonalNews" in ticker_news_component()


def test_the_fallback_is_quiet_and_says_only_that_it_is_loading() -> None:
    component = ticker_news_component()

    assert "Loading ticker news…" in component


def test_a_news_failure_cannot_affect_the_dossier() -> None:
    """A failed read renders nothing, and nothing above it is touched."""

    component = ticker_news_component()

    assert "if (!news) {" in component
    assert "return null;" in component


def test_the_rows_are_native_disclosure_controls() -> None:
    """`<details>`/`<summary>`: keyboard and screen-reader operable
    without a line of JavaScript."""

    component = ticker_news_component()

    assert "<details" in component
    assert "<summary" in component
    assert "useState" not in component, "an accordion was scripted"


def test_the_headline_does_not_depend_on_colour_or_the_icon() -> None:
    """The icon is decorative; its meaning is in the backend's words."""

    component = ticker_news_component()

    assert 'aria-hidden="true"' in component
    assert "sr-only" in component
    assert "{lead.sentimentLabel}" in component
    assert "{lead.headline}" in component


def test_the_news_reaches_no_dossier_payload_or_decision_object() -> None:
    """It is fetched beside the case, never inside it."""

    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dossier_client = (root / "apps/web/movrvest-web/lib/api/dossier.ts").read_text()

    assert "personal-news" not in dossier_client
    assert "PersonalNews" not in dossier_client

    backend = (root / "app/api/routes/executive.py").read_text()

    assert "personal_news" not in backend
    assert "personal_ticker_news" not in backend


def test_provider_sentiment_reaches_no_decision_bearing_module() -> None:
    """Massive's classification is quoted on one surface and nowhere else."""

    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    allowed = {
        "domain/personal_news.py",
        "services/personal_ticker_news_service.py",
        "api/routes/personal_news.py",
    }

    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if str(path.relative_to(root)) not in allowed
        and (
            "ProviderSentiment" in path.read_text()
            or "provider_sentiment" in path.read_text()
        )
    ]

    assert offenders == [], offenders


def test_the_row_divider_is_structural_and_not_a_first_child_rule() -> None:
    """Every `<details>` is the only child of its own `<li>`.

    So a `first:` rule on the row matches every row, and the divider it
    was meant to suppress on the first item disappears from all of them.
    The list owns the separation instead.
    """

    component = ticker_news_component()

    assert "divide-y divide-slate-100" in component
    assert "first:border-t-0" not in component
