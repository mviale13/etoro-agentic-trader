"""A conversion is a measurement, and was the one number that was not.

The investor's portfolio total was shown in euros, converted by a
constant written into the source — `EUR_PER_USD = 0.85`, undated, about
1.8% from the market the day this was written, and duplicated as `0.92`
in a second service that disagreed with it. Nothing tested either.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.exchange_rate import ExchangeRate
from app.domain.provenance import Provenance
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.exchange_rate_provider import CachedExchangeRateProvider
from app.services.exchange_rate_service import ExchangeRateService


class CountingRateProvider:
    """Reports how often the market was actually asked."""

    def __init__(self, dollars_per_euro: float = 1.1562) -> None:
        self.calls = 0
        self._rate = 1 / dollars_per_euro

    def usd_to_eur(self) -> ExchangeRate:
        self.calls += 1

        return ExchangeRate(
            base="USD",
            quote="EUR",
            rate=self._rate,
            reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
        )


class FailingRateProvider:
    def __init__(self) -> None:
        self.calls = 0

    def usd_to_eur(self) -> ExchangeRate:
        self.calls += 1

        raise RuntimeError("Yahoo Finance did not answer")


def test_a_rate_never_read_leaves_the_conversion_absent(tmp_path: Path) -> None:
    """Absent, never estimated — the whole point of replacing the constant."""

    service = ExchangeRateService(
        provider=CachedExchangeRateProvider.stored(JsonCache(tmp_path)),
    )

    assert service.rate() is None
    assert service.usd_to_eur(100_000.0) is None


def test_a_page_never_reaches_the_market_for_a_rate(tmp_path: Path) -> None:
    """The read-only door, like every other provider on a page view."""

    provider = CountingRateProvider()

    CachedExchangeRateProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
        acquires=False,
    ).usd_to_eur()

    assert provider.calls == 0


def test_the_rate_is_read_once_a_day(tmp_path: Path) -> None:
    """
    Two runs on the same day convert the same dollars to the same euros.

    Otherwise a portfolio total moves while the portfolio does not.
    """

    provider = CountingRateProvider()
    cache = JsonCache(tmp_path)

    first = CachedExchangeRateProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=cache,
    ).usd_to_eur()

    second = CachedExchangeRateProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=cache,
    ).usd_to_eur()

    assert provider.calls == 1
    assert first is not None and second is not None
    assert first.rate == second.rate


def test_a_replayed_rate_keeps_the_moment_it_was_read(tmp_path: Path) -> None:
    """A figure converted at yesterday's rate says so."""

    cache = JsonCache(tmp_path)
    taken = datetime.now(UTC) - timedelta(days=1)

    cache.write(
        CachedExchangeRateProvider.KEY,
        {
            "base": "USD",
            "quote": "EUR",
            "rate": 0.865,
            "source": "Yahoo Finance",
            "observed_at": taken.isoformat(),
        },
    )

    rate = CachedExchangeRateProvider.stored(cache).usd_to_eur()

    assert rate is not None
    assert rate.reading.observed_at == taken


def test_a_market_that_did_not_answer_leaves_the_last_rate_marked(
    tmp_path: Path,
) -> None:
    """Old evidence is still evidence, and it is never dated today."""

    cache = JsonCache(tmp_path)

    CachedExchangeRateProvider(
        provider=CountingRateProvider(),  # type: ignore[arg-type]
        cache=cache,
    ).usd_to_eur()

    # Make the stored rate look like yesterday's, so it is re-read.
    for path in tmp_path.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["stored_at"] = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        path.write_text(json.dumps(record), encoding="utf-8")

    failing = FailingRateProvider()

    rate = CachedExchangeRateProvider(
        provider=failing,  # type: ignore[arg-type]
        cache=cache,
    ).usd_to_eur()

    assert failing.calls == 1
    assert rate is not None
    assert rate.reading.last_known


def test_dollars_are_converted_at_the_rate_the_market_quoted() -> None:
    """
    Yahoo quotes `EURUSD=X` as dollars per euro; this converts the other
    way, so the inversion happens once rather than at each call site.
    """

    service = ExchangeRateService(
        provider=CountingRateProvider(dollars_per_euro=1.1562),  # type: ignore[arg-type]
    )

    # 100,000 dollars at 1.1562 dollars per euro is 86,490.23 euros —
    # and emphatically not the 85,000 the old constant produced.
    assert service.usd_to_eur(100_000.0) == pytest.approx(86_490.23, abs=0.01)


def test_every_figure_on_one_page_uses_one_rate() -> None:
    """
    A caller converting several amounts reads the rate once.

    Three figures converted by three separate reads could straddle a
    refresh and stop adding up on the page they appear on together.
    """

    provider = CountingRateProvider()
    service = ExchangeRateService(provider=provider)  # type: ignore[arg-type]

    rate = service.rate()

    for amount in (100_000.0, 20_000.0, 80_000.0):
        service.usd_to_eur(amount, rate)

    assert provider.calls == 1


class TestTheTranslationSeam:
    """The foreign→USD pairs (fx-translation@1): direct quotes, four only."""

    def test_to_usd_is_the_direct_quote_and_never_inverted(self, monkeypatch) -> None:
        """`CHFUSD=X` is already dollars per franc.

        The display pair inverts exactly once for its USD→EUR
        direction; this seam inverts zero times. Both facts asserted
        against one mocked close, so a future refactor that unified
        them wrongly fails on the spot.
        """

        from app.providers.exchange_rate_provider import ExchangeRateProvider

        monkeypatch.setattr(ExchangeRateProvider, "_close", lambda self, pair: 1.2402)

        provider = ExchangeRateProvider()

        direct = provider.to_usd("CHF")

        assert direct.base == "CHF"
        assert direct.quote == "USD"
        assert direct.rate == 1.2402

        inverted_for_display = provider.usd_to_eur()

        assert inverted_for_display.rate == 1 / 1.2402

    def test_the_seam_reads_only_the_measured_four(self, monkeypatch) -> None:
        from app.providers.exchange_rate_provider import ExchangeRateProvider

        monkeypatch.setattr(ExchangeRateProvider, "_close", lambda self, pair: 1.0)

        provider = ExchangeRateProvider()

        for base in ("CHF", "DKK", "EUR", "GBP"):
            assert provider.to_usd(base).quote == "USD"

        with pytest.raises(ValueError, match="not a translation"):
            provider.to_usd("JPY")

    def test_a_replayed_pair_keeps_its_direction_and_its_date(
        self, tmp_path: Path
    ) -> None:
        class OnePairProvider:
            def __init__(self) -> None:
                self.calls = 0

            def to_usd(self, base: str) -> ExchangeRate:
                self.calls += 1

                return ExchangeRate(
                    base=base,
                    quote="USD",
                    rate=1.2716,
                    reading=Provenance(
                        source="Yahoo Finance",
                        observed_at=datetime.now(UTC),
                    ),
                )

        provider = OnePairProvider()

        cached = CachedExchangeRateProvider(
            provider=provider,  # type: ignore[arg-type]
            cache=JsonCache(tmp_path),
        )

        first = cached.to_usd("GBP")
        replayed = cached.to_usd("GBP")

        assert provider.calls == 1
        assert replayed is not None and first is not None
        assert replayed.base == "GBP"
        assert replayed.quote == "USD"
        assert replayed.rate == 1.2716
        assert replayed.reading.observed_at == first.reading.observed_at

    def test_the_stored_door_never_acquires_a_pair(self, tmp_path: Path) -> None:
        class CountingPairProvider:
            def __init__(self) -> None:
                self.calls = 0

            def to_usd(self, base: str) -> ExchangeRate:
                self.calls += 1

                raise AssertionError("the stored door reached the market")

        provider = CountingPairProvider()

        stored = CachedExchangeRateProvider(
            provider=provider,  # type: ignore[arg-type]
            cache=JsonCache(tmp_path),
            acquires=False,
        )

        assert stored.to_usd("CHF") is None
        assert provider.calls == 0

    def test_an_unmeasured_currency_is_absent_at_the_cached_door_too(
        self, tmp_path: Path
    ) -> None:
        cached = CachedExchangeRateProvider(
            provider=CountingRateProvider(),  # type: ignore[arg-type]
            cache=JsonCache(tmp_path),
        )

        assert cached.to_usd("JPY") is None
