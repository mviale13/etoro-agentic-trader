"""Classifying an eToro instrument, and pricing it under the right ticker."""

from app.domain.asset_class import AssetClass
from app.providers.yahoo_market_provider import YahooInstrument


def test_etoro_asset_types_are_classified() -> None:
    assert AssetClass.from_etoro(5) is AssetClass.STOCK
    assert AssetClass.from_etoro(6) is AssetClass.ETF
    assert AssetClass.from_etoro(10) is AssetClass.CRYPTO
    assert AssetClass.from_etoro(2) is AssetClass.COMMODITY


def test_an_unseen_asset_type_is_unknown_rather_than_guessed() -> None:
    assert AssetClass.from_etoro(9999) is AssetClass.UNKNOWN


def test_only_companies_have_company_fundamentals() -> None:
    assert AssetClass.STOCK.has_company_fundamentals
    assert AssetClass.ETF.has_company_fundamentals

    assert not AssetClass.CRYPTO.has_company_fundamentals
    assert not AssetClass.COMMODITY.has_company_fundamentals
    assert not AssetClass.UNKNOWN.has_company_fundamentals


def test_crypto_is_priced_against_a_currency() -> None:
    """The bare ticker returns nothing; Yahoo quotes crypto as a pair."""

    instrument = YahooInstrument.for_security(
        "BTC",
        "Bitcoin",
        AssetClass.CRYPTO,
    )

    assert instrument.yahoo_symbol == "BTC-USD"


def test_a_security_keeps_its_own_symbol() -> None:
    """Evidence must come back under the ticker the investor knows."""

    instrument = YahooInstrument.for_security(
        "BTC",
        "Bitcoin",
        AssetClass.CRYPTO,
    )

    assert instrument.movrvest_symbol == "BTC"


def test_everything_else_trades_under_its_own_ticker() -> None:
    instrument = YahooInstrument.for_security(
        "MSFT",
        "Microsoft",
        AssetClass.STOCK,
    )

    assert instrument.yahoo_symbol == "MSFT"
    assert instrument.movrvest_symbol == "MSFT"


def test_a_venue_the_two_vendors_name_differently_is_translated() -> None:
    """
    Nestlé is `NESN.ZU` at the broker and `NESN.SW` at Yahoo.

    Asked for under the broker's word it came back with a single empty
    field — which the platform reported as a company with no measured
    quality, no price and no published earnings date, for a security it
    could have read in full the whole time.
    """

    instrument = YahooInstrument.for_security(
        "NESN.ZU",
        "Nestle SA",
        AssetClass.STOCK,
    )

    assert instrument.yahoo_symbol == "NESN.SW"

    # And reported back under the symbol the investor watches.
    assert instrument.movrvest_symbol == "NESN.ZU"


def test_every_other_venue_on_the_book_is_passed_through_untouched() -> None:
    """
    The suffixes measured against Yahoo before Zurich was translated.

    Each of these returned a full payload under the broker's own word, so
    translating them would move a security to a venue nobody checked —
    which is the way this kind of table goes wrong.
    """

    for symbol in (
        "UMI.BR",
        "VOW3.DE",
        "NOVO-B.CO",
        "AIR.PA",
        "BP.L",
        "GRE.MC",
        "LDO.MI",
    ):
        assert (
            YahooInstrument.for_security(
                symbol,
                symbol,
                AssetClass.STOCK,
            ).yahoo_symbol
            == symbol
        )


def test_a_venue_is_translated_only_at_the_suffix() -> None:
    """A ticker that merely contains the letters is not a Zurich listing."""

    for symbol in ("ZU", "ZUO", "AZU", "ZU.L"):
        assert (
            YahooInstrument.for_security(
                symbol,
                symbol,
                AssetClass.STOCK,
            ).yahoo_symbol
            == symbol
        )
