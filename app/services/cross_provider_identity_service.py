"""What each provider says a symbol is, before anything joins them.

The service half of `app/domain/provider_identity.py`. It reads the
identity evidence this platform *already holds* — the broker's
watchlist entry and the data vendor's own quote metadata — and states
what the join is worth. It acquires nothing, resolves nothing, and
builds no security master.

Its output is decision-neutral by construction: nothing consumes it in
this slice. What it changes is that the question can now be asked at
all, and that a conflict has somewhere to be recorded rather than
being silently absorbed by a shared ticker string.
"""

from __future__ import annotations

from typing import Any

from app.domain.provider_identity import (
    CrossProviderIdentity,
    ProviderIdentityClaim,
    join_identity,
    vendor_claim,
)
from app.domain.provider_translations import ETORO
from app.domain.watchlist_item import WatchlistItem


class CrossProviderIdentityService:
    """State what the held evidence supports about one symbol's identity."""

    def identity(
        self,
        symbol: str,
        item: WatchlistItem | None = None,
        info: dict[str, Any] | None = None,
    ) -> CrossProviderIdentity:
        """Both providers' accounts of one symbol, and their standing."""

        claims: list[ProviderIdentityClaim] = []

        if item is not None:
            claims.append(self.from_broker(item))

        if info is not None:
            claims.append(self.from_vendor(symbol, info))

        return join_identity(symbol, tuple(claims))

    @staticmethod
    def from_broker(item: WatchlistItem) -> ProviderIdentityClaim:
        """The broker's account, in the broker's own words.

        `taxonomy` carries the raw `assetTypeId` as a string rather
        than the `AssetClass` it is mapped to. That is deliberate and
        load-bearing: this layer records what eToro said, and what
        eToro's 5 *means* is a vocabulary translation standing at
        ASSUMED one layer away. Translating here would let the
        assumption in through the identity door.
        """

        return ProviderIdentityClaim(
            provider=ETORO,
            symbol=item.symbol,
            instrument_id=str(item.instrument_id) if item.instrument_id else None,
            name=item.name or None,
            taxonomy=str(item.asset_type_id) if item.asset_type_id else None,
            # The broker publishes a numeric venue id and no vocabulary
            # to read it with. Carried as the raw token, never as a
            # venue name this platform invented.
            exchange=str(item.exchange_id) if item.exchange_id else None,
            # eToro publishes no ISIN on any reachable payload. Absent,
            # and left absent.
            isin=None,
        )

    @staticmethod
    def from_vendor(symbol: str, info: dict[str, Any]) -> ProviderIdentityClaim:
        """The data vendor's account of the same symbol.

        Delegates to the domain's `vendor_claim`, which acquisition
        also uses to store the claim beside the fundamentals it arrived
        with — one implementation of what the vendor's payload says
        about identity, wherever the question is asked from.
        """

        return vendor_claim(symbol, info)
