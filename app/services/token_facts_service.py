"""What is known about a token's market facts, judged on read.

The consumption seam for crypto market evidence. The stores hold raw
claims — the crypto-native provider's distilled reading, and the
generalist's stored fundamentals — and the standing of every fact is
derived here, on read, through the deterministic validation gate. Facts
are never judged at acquisition time: a rule improved later re-judges
every stored claim without re-spending a credit, exactly as consensus
is derived over stored observations rather than baked into them.

Authority is scoped by provider × asset class × fact type, and this
service is where that scoping lives: it answers only for CRYPTO, it
reads the native provider for token facts, and it reads the generalist
only as a cross-source voice — never as the token's authority.

Read-only by construction. Both stores are opened through their
`stored` doors, so a page view composing token facts acquires nothing.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.token_fact_validation import (
    GeneralistTokenClaims,
    NativeTokenClaims,
    judge,
)
from app.domain.token_facts import TokenMarketFacts
from app.domain.valuation_snapshot import ValuationSnapshot
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.token_facts_provider import CachedTokenFactsProvider
from app.providers.yahoo_market_provider import YahooInstrument


class NativeClaimsProvider(Protocol):
    def claims(self, symbol: str) -> NativeTokenClaims | None: ...


class StoredValuationProvider(Protocol):
    def snapshot(self, symbol: str) -> ValuationSnapshot: ...


class TokenFactsService:
    """Every market fact held about one token, with its standing."""

    def __init__(
        self,
        native: NativeClaimsProvider | None = None,
        valuations: StoredValuationProvider | None = None,
    ) -> None:
        self._native = native or CachedTokenFactsProvider.stored()
        self._valuations = valuations or CachedValueProvider.stored()

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

        return judge(
            normalized,
            self._native_claims(normalized),
            self._generalist_claims(normalized, name),
        )

    def _native_claims(self, symbol: str) -> NativeTokenClaims | None:
        try:
            return self._native.claims(symbol)
        except Exception:
            # A store that cannot be read holds nothing readable. The
            # gate words the absence.
            return None

    def _generalist_claims(
        self,
        symbol: str,
        name: str,
    ) -> GeneralistTokenClaims | None:
        """The generalist's stored token claims, as claims and no more.

        Zeros are normalised to absence before judging — a provider
        reporting zero is a provider reporting nothing, which is the
        rule everything downstream already lives by.
        """

        instrument = YahooInstrument.for_security(symbol, name, AssetClass.CRYPTO)

        try:
            snapshot = self._valuations.snapshot(instrument.yahoo_symbol)
        except Exception:
            return None

        reading = snapshot.reading

        market_cap = snapshot.market_cap or None
        circulating = snapshot.circulating_supply or None
        inception = snapshot.inception

        if market_cap is None and circulating is None and inception is None:
            return None

        return GeneralistTokenClaims(
            source=reading.source if reading is not None else "Yahoo Finance",
            observed_at=reading.observed_at if reading is not None else None,
            market_cap=market_cap,
            circulating_supply=circulating,
            inception=inception,
        )
