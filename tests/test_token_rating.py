"""Another analyst's rating, shown under their name and used for nothing.

A token publishes no financial statements, so four of this platform's
analysts have nothing to read and the dossier said so four times. A
rater who publishes six dimensions and a review date says more than an
empty card — but it is *their* opinion, and the Yahoo boundary applies
to an opinion exactly as it applies to a label: an observation does not
launder a copy into evidence.

So the guard here is not a promise in a docstring. It is a test that the
reasoning path cannot import it.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest

from app.domain.token_rating import RatingDimension, TokenRating
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.token_insight_provider import (
    CachedTokenInsightProvider,
    RatingUnavailable,
    TokenInsightProvider,
)

BITCOIN = {
    "tid": "bitcoin",
    "name": "Bitcoin",
    "symbol": "BTC",
    "rating_level": "AAA",
    "rating_score": "80.63",
    "underlying_technology_security": "86.20%",
    "token_economics": "97.33%",
    "roadmap_progress": "94.67%",
    "team_partners_investors": "77.20%",
    "ecosystem_development": "62.55%",
    "token_performance": "70.00%",
    "review_time": 1729826816000,
    "rating_page": "https://tokeninsight.com/en/coins/bitcoin/rating",
    "rating_report": "https://tokeninsight.com/research/reports/bitcoin",
}


def test_a_published_rating_is_read_with_its_dimensions() -> None:
    rating = TokenInsightProvider._read("BTC", BITCOIN)

    assert rating.level == "AAA"
    assert rating.score == pytest.approx(80.63)
    assert len(rating.dimensions) == 6

    # Percentages arrive as "86.20%" and are numbers by the time anything
    # renders them.
    security = next(
        dimension
        for dimension in rating.dimensions
        if dimension.label == "Technology and security"
    )
    assert security.score == pytest.approx(86.20)


def test_the_review_date_is_the_raters_not_the_readers() -> None:
    """
    A rating reviewed in 2024 is a two-year-old opinion in 2026.

    The record's `update_time` moves every day — it was today when this
    was written — and reading that as the review date would present a
    stale opinion as a fresh one.
    """

    rating = TokenInsightProvider._read("BTC", BITCOIN)

    assert rating.reviewed_at is not None
    assert rating.reviewed_at.year == 2024


def test_a_rating_about_another_token_is_refused() -> None:
    """
    The identity check, before anything is carried.

    A wrong entry in the id table would otherwise print one token's
    rating under another's name, and nothing downstream could see it —
    the lesson `NESN.ZU` taught, applied before it can go wrong.
    """

    with pytest.raises(RatingUnavailable):
        TokenInsightProvider._read("BTC", {**BITCOIN, "symbol": "BCH"})


def test_a_token_the_platform_has_not_verified_is_not_asked_about() -> None:
    """An unmapped symbol is an absence with a reason, never a guess."""

    with pytest.raises(RatingUnavailable) as refused:
        TokenInsightProvider(api_key="present").rating("NOTATOKEN")

    assert "has not verified" in str(refused.value)


def test_no_key_is_a_worded_absence_rather_than_a_crash() -> None:
    with pytest.raises(RatingUnavailable) as refused:
        TokenInsightProvider(api_key="").rating("BTC")

    assert "no published rating" in str(refused.value)


class RefusingProvider:
    """Would spend a credit if it were ever asked."""

    def __init__(self) -> None:
        self.calls = 0

    def rating(self, symbol: str) -> TokenRating:
        self.calls += 1

        raise AssertionError("a surface must never reach the rater")


def test_a_surface_never_reaches_the_rater(tmp_path: pathlib.Path) -> None:
    """The read-only door, and the investor's metered allowance."""

    provider = RefusingProvider()

    stored = CachedTokenInsightProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
        acquires=False,
    )

    assert stored.rating("BTC") is None
    assert provider.calls == 0


def test_a_stored_rating_is_served_with_the_raters_own_date(
    tmp_path: pathlib.Path,
) -> None:
    cache = JsonCache(tmp_path)

    CachedTokenInsightProvider(
        provider=None,  # type: ignore[arg-type]
        cache=cache,
        acquires=False,
    )

    reviewed = datetime(2024, 10, 25, tzinfo=UTC)

    stored = TokenRating(
        symbol="BTC",
        name="Bitcoin",
        level="AAA",
        score=80.63,
        dimensions=(RatingDimension(label="Technology and security", score=86.2),),
        reviewed_at=reviewed,
        page_url="https://tokeninsight.com/en/coins/bitcoin/rating",
        report_url=None,
        reading=TokenInsightProvider._read("BTC", BITCOIN).reading,
    )

    cache.write("BTC", CachedTokenInsightProvider._encode(stored))

    served = CachedTokenInsightProvider.stored(cache).rating("BTC")

    assert served is not None
    assert served.level == "AAA"
    assert served.reviewed_at == reviewed
    assert served.dimensions[0].score == pytest.approx(86.2)


#: Everything that reasons, scores, classifies or decides. A rating is a
#: third party's opinion; if any of these could read it, the platform
#: would be reselling somebody else's judgement as its own.
REASONING = (
    "app/analysts",
    "app/application/brain",
    "app/application/committees",
    "app/application/executive",
    "app/committee",
    "app/domain/business_quality.py",
    "app/domain/playbook.py",
    "app/services/business_quality_service.py",
    "app/services/company_facts_service.py",
    "app/services/company_research_service.py",
    "app/services/company_signal_service.py",
    "app/domain/crypto_quality.py",
    "app/services/crypto_asset_quality_service.py",
    "app/services/playbook_mapping.py",
    "app/services/playbook_selection_service.py",
    "app/services/playbook_selector.py",
    "app/services/quality_signal_service.py",
    "app/services/understanding_engine.py",
)


def test_nothing_that_decides_can_even_import_the_rating() -> None:
    """
    The hard rule, made structural.

    The rating is composed at the API surface and nowhere else, so
    "it never reaches a selector" is a fact about the import graph
    rather than a promise. If a future slice wants it in a score, this
    test is what it has to argue with first.
    """

    root = pathlib.Path(__file__).resolve().parent.parent

    offenders: list[str] = []

    for target in REASONING:
        path = root / target

        if path.is_dir():
            files = sorted(path.rglob("*.py"))
        else:
            files = [path] if path.exists() else []

        for source in files:
            text = source.read_text(encoding="utf-8")

            if "token_insight" in text or "TokenRating" in text:
                offenders.append(str(source.relative_to(root)))

    assert offenders == []
