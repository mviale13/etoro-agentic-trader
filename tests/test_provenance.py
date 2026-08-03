"""Every reading knows when it was taken, and who reported it."""

from datetime import UTC, datetime, timedelta

from app.domain.company_facts import CompanyFacts
from app.domain.provenance import Provenance, oldest

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def reading(source: str, minutes_ago: int) -> Provenance:
    return Provenance(
        source=source,
        observed_at=NOW - timedelta(minutes=minutes_ago),
    )


def test_a_reading_knows_how_old_it_is() -> None:
    assert reading("Yahoo Finance", 15).age(NOW) == timedelta(minutes=15)


def test_freshness_is_decided_by_the_caller_not_the_fetcher() -> None:
    """
    A price is worthless at fifteen minutes; an asset class is not.

    Only the code using a reading knows which it is holding, so the limit
    is asked for rather than baked in where the value was fetched.
    """

    quote = reading("Yahoo Finance", 15)

    assert quote.is_older_than(timedelta(minutes=5), NOW)
    assert not quote.is_older_than(timedelta(days=30), NOW)


def test_a_collection_is_only_as_fresh_as_its_stalest_part() -> None:
    """Not the age of whichever part was written last."""

    stale = reading("Yahoo Finance", 1_440)
    fresh = reading("eToro", 1)

    assert oldest(fresh, stale) is stale
    assert oldest(None, fresh) is fresh
    assert oldest(None, None) is None


def facts(**overrides: object) -> CompanyFacts:
    return CompanyFacts(
        **{  # type: ignore[arg-type]
            "instrument_id": 1,
            "symbol": "TEST",
            "name": "Test",
            "asset_type": "stock",
            "exchange": "4",
            **overrides,
        }
    )


def test_evidence_is_dated_by_its_stalest_half_not_its_freshest() -> None:
    """
    One date used to cover the lot, and it was the fundamentals' date.

    A price fifteen minutes old sat beside it, dated by implication to
    whenever the fundamentals were read.
    """

    dated = facts(
        price_reading=reading("Yahoo Finance", 14),
        fundamentals_reading=reading("Yahoo Finance", 1_440),
    )

    assert dated.observed_at == NOW - timedelta(minutes=1_440)


def test_the_two_halves_are_dated_separately() -> None:
    """They are two requests and they age at different rates."""

    dated = facts(
        price_reading=reading("Yahoo Finance", 14),
        fundamentals_reading=reading("Yahoo Finance", 1_440),
    )

    assert dated.price_reading is not None
    assert dated.fundamentals_reading is not None
    assert dated.price_reading.observed_at > dated.fundamentals_reading.observed_at


def test_evidence_carrying_no_reading_claims_no_age() -> None:
    """Which is not the same as being fresh."""

    assert facts().observed_at is None


def test_an_age_is_stated_as_the_investor_should_read_it() -> None:
    """
    Coarse on purpose.

    "14 minutes ago" is what matters about a price. The second it was taken
    is not, and printing it would suggest a precision the number lacks.
    """

    assert reading("Yahoo Finance", 0).stated(NOW) == "Yahoo Finance, just now"
    assert reading("Yahoo Finance", 1).stated(NOW) == "Yahoo Finance, 1 minute ago"
    assert reading("Yahoo Finance", 14).stated(NOW) == "Yahoo Finance, 14 minutes ago"
    assert reading("Yahoo Finance", 180).stated(NOW) == "Yahoo Finance, 3 hours ago"
    assert reading("eToro", 1_440).stated(NOW) == "eToro, yesterday"
    assert reading("eToro", 5_760).stated(NOW) == "eToro, 4 days ago"
