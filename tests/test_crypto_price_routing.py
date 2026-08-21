"""A token is priced by the sources that know which token it is.

The measured defect, from the cycle recorded on 2026-08-20: *"HYPE: no
price came back"* and *"TAO: no price came back"* — in a cycle whose own
store held an established, corroborated price for both, $73.44 and
$210.74, each tied to the crypto-native identifier the platform verified
by hand. What came back with nothing was Yahoo, and Yahoo's `HYPE-USD`
is **Supreme Finance USD** while its `TAO-USD` is **Together As One
USD**: two other tokens, sharing a ticker and a currency suffix.

Three separate rules are tested here, because they fail separately:

- which source may price a cryptocurrency at all;
- whether the vendor's pair listing is this token, which decides
  whether its *series* — the day's move, the volatility, the drawdown —
  may be read as this token's;
- that neither question is asked about an equity or a fund, whose
  routing is untouched.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.evidence_standing import EvidenceStanding
from app.domain.market_acquisition import MarketAcquisition
from app.domain.provider_identity import crypto_listing
from app.domain.token_facts import TokenFact, TokenMarketFacts


def _run(service: Any) -> MarketAcquisition:
    acquired: MarketAcquisition = asyncio.run(service.acquire())

    return acquired


# ── the rule, against the live corpus ───────────────────────────────

#: Every mapped token, as the two sides actually name it. Read from
#: the live store on 2026-08-20: the broker's name from the watchlist,
#: the vendor's from its own `{SYMBOL}-USD` payload, the identifier
#: from `COINGECKO_IDS`. Three of the five agree; two do not, and the
#: two are the securities the cycle reported as unpriced.
LIVE_LISTINGS = (
    ("BTC", "Bitcoin", "Bitcoin USD", "bitcoin", True),
    ("ETH", "Ethereum", "Ethereum USD", "ethereum", True),
    ("SOL", "Solana", "Solana USD", "solana", True),
    ("HYPE", "Hyperliquid", "Supreme Finance USD", "hyperliquid", False),
    ("TAO", "Bittensor", "Together As One USD", "bittensor", False),
)


@pytest.mark.parametrize(
    ("symbol", "broker_name", "vendor_name", "provider_id", "agrees"),
    LIVE_LISTINGS,
)
def test_the_rule_reads_the_live_book_correctly(
    symbol: str,
    broker_name: str,
    vendor_name: str,
    provider_id: str,
    agrees: bool,
) -> None:
    listing = crypto_listing(
        symbol=symbol,
        vendor_symbol=f"{symbol}-USD",
        vendor_name=vendor_name,
        token_names=(broker_name, provider_id),
    )

    assert listing.agrees is agrees
    assert listing.because


def test_either_independent_name_is_enough() -> None:
    """The broker's name and the identifier are two routes, not one.

    A broker spelling a token differently from its own project — *1inch
    Network* against `1inch` — is not a collision, and one route
    matching settles it. Both routes match for every major.
    """

    listing = crypto_listing(
        symbol="1INCH",
        vendor_symbol="1INCH-USD",
        vendor_name="1inch USD",
        token_names=("1inch Network", "1inch"),
    )

    assert listing.agrees


def test_a_listing_nothing_names_does_not_pass() -> None:
    """S5.1's gate rule: what cannot be evaluated fails.

    Holding no vendor name is precisely the state this platform was in
    about `HYPE-USD` before it looked at one.
    """

    listing = crypto_listing(
        symbol="ADA",
        vendor_symbol="ADA-USD",
        vendor_name=None,
        token_names=("Cardano", "cardano"),
    )

    assert not listing.agrees
    assert "no vendor name" in listing.because


def test_the_rule_matches_whole_names_and_never_fragments() -> None:
    """`_forms` learned this the expensive way; it is not relearned here.

    Matched by containment, *"Bit"* would name Bitcoin and *"Sol"*
    would name Solana. Names are compared for equality once the
    currency word is dropped, and nothing else is inferred from them.
    """

    assert not crypto_listing(
        symbol="BTC",
        vendor_symbol="BTC-USD",
        vendor_name="Bitcoin Cash USD",
        token_names=("Bitcoin", "bitcoin"),
    ).agrees

    assert not crypto_listing(
        symbol="ETH",
        vendor_symbol="ETH-USD",
        vendor_name="Ethereum Classic USD",
        token_names=("Ethereum", "ethereum"),
    ).agrees


def test_punctuation_and_case_are_not_identity() -> None:
    listing = crypto_listing(
        symbol="BTC",
        vendor_symbol="BTC-USD",
        vendor_name="BITCOIN  usd",
        token_names=("bit-coin",),
    )

    assert listing.agrees


# ── acquisition: what "priced" means for a token ────────────────────


def _facts(
    symbol: str,
    provider_id: str,
    price: float,
    standing: EvidenceStanding = EvidenceStanding.ESTABLISHED,
) -> TokenMarketFacts:
    """The judged pool for one token, as the gate hands it over."""

    return TokenMarketFacts(
        symbol=symbol,
        provider_id=provider_id,
        facts=(
            TokenFact(
                fact="price",
                standing=standing,
                value=price,
                source="TokenInsight",
                observed_at=datetime(2026, 8, 20, 14, 29, tzinfo=UTC),
            ),
        ),
        rejected=(),
    )


class JudgedTokensStub:
    """The consumption seam, answering from a canned pool."""

    def __init__(self, pool: dict[str, TokenMarketFacts]) -> None:
        self._pool = pool
        self.asked: list[str] = []

    def established(self, symbol: str, name: str, asset_class: object) -> object:
        self.asked.append(symbol)

        return self._pool.get(symbol.upper())


def test_a_token_is_priced_by_the_pool_and_not_by_the_pair_listing() -> None:
    """The correction, at the point the cycle counts prices.

    The vendor returns nothing for either ticker — exactly what it did
    on 2026-08-20 — and both tokens are priced anyway, because the
    figure never depended on the vendor.
    """

    from tests.test_market_acquisition import make_crypto_cycle

    service, judged = make_crypto_cycle(
        pool={
            "HYPE": _facts("HYPE", "hyperliquid", 73.43639113145252),
            "TAO": _facts("TAO", "bittensor", 210.74316718972827),
        },
        vendor_names={
            "HYPE-USD": "Supreme Finance USD",
            "TAO-USD": "Together As One USD",
        },
    )

    acquired = _run(service)

    by_symbol = {security.symbol: security for security in acquired.securities}

    assert by_symbol["HYPE"].priced
    assert by_symbol["TAO"].priced
    assert acquired.unpriced == ()
    assert judged.asked == ["HYPE", "TAO"]


def test_a_refused_listing_is_reported_as_itself() -> None:
    """Two facts, two sentences. The cycle said one thing about both.

    A refused listing is not an unpriced security, and the wording that
    reaches the investor must not merge them: HYPE has a price, and it
    has no vendor history.
    """

    from tests.test_market_acquisition import make_crypto_cycle

    service, _ = make_crypto_cycle(
        pool={"HYPE": _facts("HYPE", "hyperliquid", 73.43639113145252)},
        vendor_names={"HYPE-USD": "Supreme Finance USD"},
    )

    acquired = _run(service)

    refused = acquired.refused_listings

    assert [security.symbol for security in refused] == ["HYPE"]
    assert "Supreme Finance USD" in refused[0].listing_refused
    assert acquired.unpriced == ()


def test_a_token_the_pool_could_not_settle_stays_unpriced() -> None:
    """Absence is reported as absence, and never filled from the pair.

    Invariant 1 on the one figure that had been escaping it. The pool
    holds a figure here — one claimant's, uncorroborated — and a claim
    is not a price: `established_value` withholds it, and the vendor's
    number for the ticker, which is another token's, does not step in.
    """

    from tests.test_market_acquisition import make_crypto_cycle

    service, _ = make_crypto_cycle(
        pool={
            "HYPE": _facts(
                "HYPE",
                "hyperliquid",
                73.43639113145252,
                standing=EvidenceStanding.CLAIMED,
            )
        },
        vendor_names={"HYPE-USD": "Supreme Finance USD"},
    )

    acquired = _run(service)

    assert [security.symbol for security in acquired.unpriced] == ["HYPE"]


def test_an_agreeing_listing_refuses_nothing() -> None:
    from tests.test_market_acquisition import make_crypto_cycle

    service, _ = make_crypto_cycle(
        pool={"BTC": _facts("BTC", "bitcoin", 72_664.79)},
        vendor_names={"BTC-USD": "Bitcoin USD"},
        names={"BTC": "Bitcoin"},
    )

    acquired = _run(service)

    assert acquired.refused_listings == ()
    assert acquired.unpriced == ()


def test_an_equity_is_priced_exactly_as_it_was() -> None:
    """The boundary: none of this reaches a company or a fund.

    An equity trades under its own ticker at a named venue, so the
    question the crypto path asks does not arise for it — and the
    quote batch stays the only thing that prices it.
    """

    from tests.test_market_acquisition import HoldingStub, make_cycle

    service, _ = make_cycle(holdings=(HoldingStub(1, "AAPL"),))

    acquired = _run(service)

    by_symbol = {security.symbol: security for security in acquired.securities}

    assert by_symbol["AAPL"].priced
    assert by_symbol["AAPL"].listing_refused == ""
    assert acquired.refused_listings == ()


# ── the cycle's own wording ─────────────────────────────────────────


def test_the_cycle_words_the_two_refusals_apart() -> None:
    from app.domain.market_acquisition import AcquiredSecurity, MarketAcquisition

    acquired = MarketAcquisition(
        securities=(
            AcquiredSecurity(
                symbol="HYPE",
                priced=True,
                fundamentals=True,
                calendar=None,
                listing_refused=(
                    "the vendor lists HYPE-USD as Supreme Finance USD, "
                    "which is a different token from HYPE"
                ),
            ),
            AcquiredSecurity(
                symbol="KO",
                priced=False,
                fundamentals=True,
                calendar=True,
            ),
        ),
        instruments=(),
        vix=None,
    )

    assert [security.symbol for security in acquired.unpriced] == ["KO"]
    assert [security.symbol for security in acquired.refused_listings] == ["HYPE"]

    # And the sentence the investor reads about each.
    unpriced = tuple(f"{s.symbol}: no price came back" for s in acquired.unpriced)
    listings = tuple(
        f"{s.symbol}: {s.listing_refused}" for s in acquired.refused_listings
    )

    assert unpriced == ("KO: no price came back",)
    assert "no price came back" not in listings[0]
