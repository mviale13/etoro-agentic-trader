"""Assessing a token on what a token has."""

from datetime import UTC, datetime, timedelta

from app.domain.company_facts import CompanyFacts
from app.domain.finding import Sense, statements, statements_where
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
    assert statements(signal.evidence) == ("Insufficient quality data.",)


def test_a_token_is_never_called_a_company() -> None:
    """The company signal's vocabulary does not appear here."""

    lines = statements(build().evidence)

    assert not any("company" in line.lower() for line in lines)
    assert any("Network value" in line for line in lines)
