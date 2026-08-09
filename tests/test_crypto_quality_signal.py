"""Assessing a token on what a token has."""

from datetime import UTC, datetime, timedelta

from app.domain.company_facts import CompanyFacts
from app.domain.finding import Sense, statements, statements_where
from app.domain.provenance import Provenance
from app.services.crypto_quality_signal_service import (
    CryptoQualitySignalService,
)

BITCOIN = {
    "market_cap": 1_269_000_000_000.0,
    "volume_24h": 20_300_000_000.0,
    "circulating_supply": 20_065_192.0,
    "max_supply": 21_000_000.0,
    "inception": datetime(2010, 7, 13, tzinfo=UTC),
}


def facts(**overrides: object) -> CompanyFacts:
    return CompanyFacts(
        **{  # type: ignore[arg-type]
            "instrument_id": 1,
            "symbol": "TOKEN",
            "name": "Token",
            "asset_type": "crypto",
            "exchange": "8",
            **BITCOIN,
            **overrides,
        }
    )


def build(**overrides: object):
    return CryptoQualitySignalService().build(facts(**overrides))


def test_a_large_liquid_fully_issued_token_scores_well() -> None:
    signal = build()

    assert signal.quality == "HIGH"
    assert statements_where(signal.evidence, Sense.ADVERSE) == ()


def test_a_token_still_mostly_unissued_is_marked_down() -> None:
    """
    The holder is diluted by a schedule rather than by a decision.

    A token 20% issued has five times its float still to come, and that is
    a fact about the asset rather than about the market.
    """

    signal = build(circulating_supply=200_000_000.0, max_supply=1_000_000_000.0)

    adverse = statements_where(signal.evidence, Sense.ADVERSE)

    assert any("diluted as the rest is issued" in line for line in adverse)


def test_a_token_nobody_trades_is_marked_down() -> None:
    """For an asset with no earnings, whether you can leave is most of it."""

    signal = build(volume_24h=100_000.0)

    adverse = statements_where(signal.evidence, Sense.ADVERSE)

    assert any("hard to leave" in line for line in adverse)


def test_a_token_with_no_stated_cap_is_not_scored_on_issuance() -> None:
    """No cap means no schedule to be diluted by, and no measurement."""

    signal = build(max_supply=None)

    assert not any("eventual supply" in line for line in statements(signal.evidence))

    # Still assessable on the three readings that exist, and judged
    # against those rather than marked down for the missing one.
    assert signal.quality != "UNKNOWN"
    assert len(signal.evidence) == 3


def test_a_brand_new_token_has_little_record_to_go_on() -> None:
    signal = build(inception=datetime.now(UTC) - timedelta(days=200))

    adverse = statements_where(signal.evidence, Sense.ADVERSE)

    assert any("little of its record" in line for line in adverse)


def test_a_token_the_provider_says_nothing_about_scores_nothing() -> None:
    """Absent evidence is absent here too — never a default score."""

    signal = build(
        market_cap=None,
        volume_24h=None,
        circulating_supply=None,
        max_supply=None,
        inception=None,
    )

    assert signal.quality == "UNKNOWN"
    assert statements(signal.evidence) == (
        "This platform has read nothing about this token's network, so its "
        "quality is not assessed.",
    )


def test_a_token_is_never_called_a_company() -> None:
    """The company signal's vocabulary does not appear here."""

    lines = statements(build().evidence)

    assert not any("company" in line.lower() for line in lines)
    assert any("market value" in line for line in lines)


def test_a_scale_reading_is_the_providers_claim_and_says_so() -> None:
    """
    The scale figure is one field read from one source, and it is worded
    as that source's claim rather than as a network measurement.

    "Network value is only $8,105" stood as Hyperliquid's invalidation
    condition — a provider error dressed in this platform's most
    authoritative vocabulary. The reading is kept; the dressing is not.
    """

    signal = build(
        fundamentals_reading=Provenance(
            source="Yahoo Finance",
            observed_at=datetime.now(UTC),
        ),
    )

    lines = statements(signal.evidence)

    assert any(
        line.startswith("Yahoo Finance reports a market value") for line in lines
    )
    assert not any("Network value" in line for line in lines)


def test_an_unattributed_scale_reading_still_names_a_source() -> None:
    """A reading with no named source is still somebody's claim."""

    lines = statements(build().evidence)

    assert any(
        line.startswith("The data provider reports a market value") for line in lines
    )


def test_a_provider_zero_is_an_absence_and_never_a_market_value() -> None:
    """
    Bittensor came back with a market cap of exactly 0.

    It was read as a measurement: banded adverse, printed on the research
    page as "Network value is only $0.00bn", and carried into the token's
    quality. A network cannot be worth nothing while it trades, so a zero
    here is the provider having no figure — and absent evidence is
    reported as absent, never as a zero somebody could mistake for a
    reading.
    """

    signal = build(market_cap=0.0, volume_24h=144.0)

    assert not any("market value" in line for line in statements(signal.evidence))
    assert not any("$0.00bn" in line for line in statements(signal.evidence))


def test_a_market_value_is_shown_at_a_unit_that_shows_it() -> None:
    """
    Hyperliquid came back as 8,105 dollars, which printed as "$0.00bn".

    That reads as a rounding of something real. Shown at a unit where it
    is still visible, the investor sees a provider figure that is plainly
    wrong instead of a zero this platform appeared to have measured.
    """

    signal = build(market_cap=8_105.0, volume_24h=2_670.0)

    assert any("$8,105" in line for line in statements(signal.evidence))


def test_one_reading_is_a_gap_rather_than_a_verdict() -> None:
    """
    The rule `MINIMUM_ANSWERED` already states for a business.

    A token whose only readable fact was its age was banded on that
    alone — MEDIUM quality for not having disappeared yet, feeding a
    conviction. One reading is as easily a gap as a verdict.
    """

    signal = build(
        market_cap=0.0,
        volume_24h=0.0,
        circulating_supply=0.0,
        max_supply=None,
        inception=datetime.now(UTC) - timedelta(days=365 * 4),
    )

    assert signal.quality == "UNKNOWN"


def test_two_readings_are_enough_to_band() -> None:
    """The floor is a minimum, not a demand for the whole set."""

    signal = build(
        market_cap=50_000_000_000.0,
        volume_24h=0.0,
        circulating_supply=0.0,
        max_supply=None,
        inception=datetime(2010, 7, 13, tzinfo=UTC),
    )

    assert signal.quality != "UNKNOWN"
