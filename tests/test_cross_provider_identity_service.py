"""Reading the identity evidence this platform already holds.

The service is decision-neutral and consumed by nothing in this slice.
What these tests fix is the *shape* of its answers — in particular
that the live corpus's two interesting cases come out as what they
are, and that neither is special-cased.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.provenance import Provenance
from app.domain.provider_identity import IdentityStanding
from app.domain.watchlist_item import WatchlistItem
from app.services.cross_provider_identity_service import (
    CrossProviderIdentityService,
)

READING = Provenance(source="eToro", observed_at=datetime(2026, 8, 15, tzinfo=UTC))


def _item(
    symbol: str,
    name: str,
    instrument_id: int = 1,
    asset_type_id: int = 5,
) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=name,
        asset_type_id=asset_type_id,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=0,
        avatar_url=None,
        reading=READING,
    )


class TestTheBrokersAccount:
    def test_the_raw_taxonomy_token_is_carried_untranslated(self) -> None:
        """`5` is evidence about eToro, not an AssetClass.

        Translating here would let the vocabulary assumption in
        through the identity door — the same conflation one layer
        down that made a fund receive company questions.
        """

        claim = CrossProviderIdentityService.from_broker(
            _item("SPCX", "Space Exploration Technologies Corp")
        )

        assert claim.taxonomy == "5"
        assert claim.provider == "eToro"

    def test_no_isin_is_invented(self) -> None:
        claim = CrossProviderIdentityService.from_broker(_item("BP.L", "BP plc"))

        assert claim.isin is None


class TestTheLiveConflict:
    """SPCX, from the evidence actually held — and not special-cased."""

    def test_the_spcx_join_is_unresolved_rather_than_decided(self) -> None:
        identity = CrossProviderIdentityService().identity(
            "SPCX",
            item=_item("SPCX", "Space Exploration Technologies Corp", 15618),
            info={
                "symbol": "SPCX",
                "longName": "SPAC and New Issue ETF",
                "quoteType": "ETF",
            },
        )

        assert identity.standing is IdentityStanding.UNRESOLVED
        assert not identity.establishes_identity

    def test_neither_account_is_dropped(self) -> None:
        identity = CrossProviderIdentityService().identity(
            "SPCX",
            item=_item("SPCX", "Space Exploration Technologies Corp", 15618),
            info={"symbol": "SPCX", "longName": "SPAC and New Issue ETF"},
        )

        assert len(identity.claims) == 2
        assert identity.providers == ("eToro", "Yahoo Finance")

    def test_an_ordinary_security_is_assumed_not_established(self) -> None:
        """The live state of every other security: joined on a symbol.

        The important half of the SPCX result. If only the conflicting
        case were flagged, the boundary would be a special case; what
        it actually says is that *every* join on this platform rests
        on symbol equality, and none of them is established.
        """

        identity = CrossProviderIdentityService().identity(
            "AAPL",
            item=_item("AAPL", "Apple Inc"),
            info={"symbol": "AAPL", "longName": "Apple Inc.", "quoteType": "EQUITY"},
        )

        assert identity.standing is IdentityStanding.ASSUMED
        assert not identity.establishes_identity

    def test_one_provider_alone_is_never_corroborated(self) -> None:
        identity = CrossProviderIdentityService().identity(
            "AAPL", item=_item("AAPL", "Apple Inc")
        )

        assert identity.standing is IdentityStanding.ASSUMED

    def test_agreeing_fund_names_corroborate_without_establishing(self) -> None:
        """Both call it a fund: better than assumed, short of proven."""

        identity = CrossProviderIdentityService().identity(
            "IB01.L",
            item=_item(
                "IB01.L", "iShares $ Treasury Bond 0-1yr UCITS ETF", 1, asset_type_id=6
            ),
            info={
                "symbol": "IB01.L",
                "longName": "iShares USD Treasury Bond 0-1yr UCITS ETF",
                "quoteType": "ETF",
            },
        )

        assert identity.standing is IdentityStanding.CORROBORATED
        assert identity.establishes_identity


class TestFormsAreWordsNotSubstrings:
    """#110's boundary lesson, applied to the form lexer.

    `etf` is a substring of n**etf**lix, so substring matching read
    Netflix as a fund on both providers' side and *corroborated* the
    join on a manufactured agreement — measured live as the corpus's
    only accidental hit. A form is a word, and only a word.
    """

    def test_netflix_is_not_a_fund_on_either_side(self) -> None:
        identity = CrossProviderIdentityService().identity(
            "NFLX",
            item=_item("NFLX", "Netflix, Inc."),
            info={
                "symbol": "NFLX",
                "longName": "Netflix, Inc.",
                "quoteType": "EQUITY",
            },
        )

        # Honest, not manufactured: nothing in either name states a
        # form, so nothing cross-checks the join.
        assert identity.standing is IdentityStanding.ASSUMED

    def test_a_hyphenated_form_word_still_counts(self) -> None:
        """SE's live shape: 'Sea Ltd-ADR' states a form; 'Sea Limited'
        does not — a stated form against silence stays unresolved."""

        identity = CrossProviderIdentityService().identity(
            "SE",
            item=_item("SE", "Sea Ltd-ADR"),
            info={
                "symbol": "SE",
                "longName": "Sea Limited",
                "quoteType": "EQUITY",
            },
        )

        assert identity.standing is IdentityStanding.UNRESOLVED
