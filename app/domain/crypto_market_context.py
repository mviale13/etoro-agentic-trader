"""One security's market context: the environment, and its place in it.

The join S4 exists to make, and the question it lets a future Artificial
CIO eventually answer:

> Is this asset moving because of itself, its peer group, or crypto
> broadly?

Three readings sit side by side and are never merged. The **market** is
what every token trades inside. The **peer group** is who the market
moves this one alongside — a vendor's category, carried under the
vendor's name, and deliberately not this platform's analytical
archetype. The **asset's own return** is the third, and the differences
between it and the other two are arithmetic.

**Nothing here is Asset Quality.** A token that fell less than its peers
is not thereby a better asset, and this object contains no field that
could be read as saying so: no band, no verdict, no ordering. It is
context, and the investor is the one who weighs it.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.crypto_market import (
    Concentration,
    CryptoMarketSnapshot,
    MarketInterval,
    MarketObservation,
    RelativeReturn,
)
from app.domain.market_peer_group import PeerGroupSelection


@dataclass(frozen=True, slots=True)
class CryptoMarketContext:
    """What the market did, what the peers did, and what this asset did."""

    symbol: str

    #: The environment, read once per cycle and shared by every token.
    snapshot: CryptoMarketSnapshot

    #: This asset's own returns, one per interval the provider publishes.
    #: Several have no comparator at all, which is stated rather than
    #: quietly leaving the interval out.
    returns: tuple[MarketObservation, ...] = ()

    peer: PeerGroupSelection | None = None

    #: The peer group's own state, where a group is available.
    peer_observations: tuple[MarketObservation, ...] = ()

    #: The arithmetic, at intervals where both sides were read.
    relative: tuple[RelativeReturn, ...] = ()

    #: How much of each comparator this asset itself is.
    concentrations: tuple[Concentration, ...] = ()

    #: Intervals this asset's return was read at and no comparator was.
    #: Named so a missing row reads as a gap in the comparator rather
    #: than as an asset that did not move.
    uncompared: tuple[MarketInterval, ...] = ()

    #: Why there is no context at all, where there is none.
    unavailable_because: str | None = None

    @property
    def is_read(self) -> bool:
        return bool(self.returns) or self.snapshot.is_read

    @property
    def has_peer_context(self) -> bool:
        return self.peer is not None and self.peer.is_available

    def relative_to(self, comparator: str) -> RelativeReturn | None:
        for item in self.relative:
            if item.comparator == comparator:
                return item

        return None

    def concentration_in(self, comparator: str) -> Concentration | None:
        for item in self.concentrations:
            if item.comparator == comparator:
                return item

        return None
