"""What is known about a token's market facts, judged on read.

The consumption seam for crypto market evidence, and the claimant
registry: every source that can contribute claims about a token is an
adapter here, producing a `TokenClaimSet` and nothing else. The pool of
sets goes to the deterministic gate, which judges standings on read —
so a rule improved later re-judges every stored claim without a single
reacquisition, and a new claimant is a new adapter in this list, never
a change to the validator, the dossier, the scores or the canonical
fact schema.

Authority is scoped by provider × asset class × fact type, and no
claimant has global authority: the crypto-native provider and CoinGecko
are peers in the pool; the generalist contributes the token fields it
happens to carry, as one more voice. Establishment itself belongs to
the gate — agreement inside one provider is not corroboration.

Read-only by construction: every adapter opens its store's `stored`
door, so a page view composing token facts acquires nothing.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.token_fact_validation import TokenClaimSet, judge
from app.domain.token_facts import TokenMarketFacts
from app.domain.valuation_snapshot import ValuationSnapshot
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.coingecko_facts_provider import CachedCoinGeckoFactsProvider
from app.providers.token_facts_provider import CachedTokenFactsProvider
from app.providers.yahoo_market_provider import YahooInstrument


class ClaimSource(Protocol):
    """One claimant: asked for a token, answers with a set or nothing."""

    def claim_set(self, symbol: str) -> TokenClaimSet | None: ...


class StoredClaimsReader(Protocol):
    """A cached provider's read-only door."""

    def claims(self, symbol: str) -> TokenClaimSet | None: ...


class NativeClaimSource:
    """The crypto-native provider's stored claims, as a pool claimant."""

    def __init__(self, reader: StoredClaimsReader | None = None) -> None:
        self._reader: StoredClaimsReader = reader or CachedTokenFactsProvider.stored()

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        try:
            return self._reader.claims(symbol)
        except Exception:
            return None


class CoinGeckoClaimSource:
    """CoinGecko's stored claims, as a pool claimant."""

    def __init__(self, reader: StoredClaimsReader | None = None) -> None:
        self._reader: StoredClaimsReader = (
            reader or CachedCoinGeckoFactsProvider.stored()
        )

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        try:
            return self._reader.claims(symbol)
        except Exception:
            return None


class StoredValuationReader(Protocol):
    def snapshot(self, symbol: str) -> ValuationSnapshot: ...


class GeneralistClaimSource:
    """The generalist's stored token fields, as one more voice.

    Zeros are normalised to absence before the set is built — a
    provider reporting zero is a provider reporting nothing, which is
    the rule everything downstream already lives by. Its inception
    field is carried so the gate can reject it semantically, on the
    record, rather than have it silently ignored.
    """

    def __init__(self, valuations: StoredValuationReader | None = None) -> None:
        self._valuations: StoredValuationReader = (
            valuations or CachedValueProvider.stored()
        )

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        instrument = YahooInstrument.for_security(symbol, symbol, AssetClass.CRYPTO)

        try:
            snapshot = self._valuations.snapshot(instrument.yahoo_symbol)
        except Exception:
            return None

        market_cap = snapshot.market_cap or None
        circulating = snapshot.circulating_supply or None
        inception = snapshot.inception

        if market_cap is None and circulating is None and inception is None:
            return None

        reading = snapshot.reading

        if reading is None:
            return None

        return TokenClaimSet(
            source=reading.source or "Yahoo Finance",
            read=reading,
            market_cap=market_cap,
            circulating_supply=circulating,
            inception=inception,
        )


class TokenFactsService:
    """Every market fact held about one token, with its standing."""

    def __init__(
        self,
        sources: tuple[ClaimSource, ...] | None = None,
    ) -> None:
        # The claimant registry. Order is display preference only —
        # the gate takes no authority from it.
        self._sources: tuple[ClaimSource, ...] = sources or (
            NativeClaimSource(),
            CoinGeckoClaimSource(),
            GeneralistClaimSource(),
        )

    def established(
        self,
        symbol: str,
        name: str,
        asset_class: AssetClass | None,
    ) -> TokenMarketFacts | None:
        """The judged facts for a token, or None for anything else.

        Only a security positively classified as crypto is answered.
        An UNKNOWN security is not promoted to a token by any heuristic
        — saying so here is what keeps that a rule rather than a habit.
        """

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        pool = tuple(
            claims
            for source in self._sources
            if (claims := source.claim_set(normalized)) is not None
        )

        return judge(normalized, pool)
