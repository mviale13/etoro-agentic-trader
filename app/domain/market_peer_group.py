"""Which externally observed group is useful for comparing market performance.

**Not an archetype, and this module cannot see one.** S3 decides what
kind of economic object a token is, from evidence this platform can
re-check. This decides which group of assets it is useful to compare its
*price* against, from a vendor's taxonomy. They answer different
questions and they legitimately differ:

```text
AnalyticalArchetype   what MOVRvest believes this is     ← crypto_archetype.py
MarketPeerGroup       who the market moves it alongside  ← here
```

ETH's archetype is a smart-contract network; its peer group is the
provider's *Layer 1 (L1)* category, which contains Bitcoin, XRP and
Monero. Both statements are true and neither may be used to correct the
other. **A provider category never changes a playbook** — the two
modules do not import each other, and a test enforces it in both
directions.

Every entry below was measured against the provider on 2026-08-10 by
reading the category's own membership, because a category's *name* is
not evidence of what is in it. Two were rejected on that measurement:

- **`smart-contract-platform`** holds **Bitcoin at rank 1**, and
  Dogecoin, XRP and Tron in its top ten. Neither Bitcoin nor Dogecoin
  runs smart contracts, so the label does not describe the membership.
  It is the ruling's own acceptance case, now measured.
- **`layer-2`** holds WETH — wrapped ether, not an asset with
  economics of its own — and the exchange tokens OKB and MNT.

Where the taxonomy cannot support a defensible comparison the answer is
**no peer group**, stated with the reason. A fake comparison is worse
than none: it would put a number on the page that reads like a
measurement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PeerGroup:
    """One externally observed group, and why it is a fair comparison.

    `key` is the provider's own category identifier and is named as
    such. It is a vendor's decision about membership, carried under the
    vendor's name exactly as a third party's rating is.
    """

    #: The provider's category identifier. Never this platform's own.
    key: str

    #: The provider's own name for it.
    name: str

    provider: str

    #: Why this group is a fair comparison for this security.
    selected_because: str

    #: What would make a reader misread the comparison. Measured, not
    #: guessed: a group one member dominates is a group that member is
    #: largely compared with itself.
    caveats: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConsideredPeerGroup:
    """A group weighed and rejected, with what the measurement showed."""

    key: str
    name: str
    rejected_because: str


@dataclass(frozen=True, slots=True)
class PeerGroupSelection:
    """One security's peer group, or the honest absence of one."""

    symbol: str

    group: PeerGroup | None

    #: Why there is none. Set exactly when `group` is None.
    unavailable_because: str | None = None

    considered: tuple[ConsideredPeerGroup, ...] = ()

    @property
    def is_available(self) -> bool:
        return self.group is not None


_COINGECKO = "CoinGecko"

#: The measured rejection every base-layer asset shares.
_SMART_CONTRACT_PLATFORM_REJECTED = ConsideredPeerGroup(
    key="smart-contract-platform",
    name="Smart Contract Platform",
    rejected_because=(
        "read on 2026-08-10, the category's membership is led by Bitcoin "
        "at rank 1, and its top ten includes Dogecoin, XRP and Tron. "
        "Neither Bitcoin nor Dogecoin runs smart contracts, so the "
        "label does not describe what is in it. A group chosen on a name "
        "would have compared Ethereum with assets the name excludes."
    ),
)


#: The peer group each corpus security is compared against.
#:
#: Hand-assigned and hand-verified against the provider's own category
#: membership, in the same discipline as `PROTOCOL_ENTITIES`: the
#: reason is stated so it can be argued with, and a security absent from
#: this table has no peer group rather than a guessed one.
PEER_GROUPS: dict[str, PeerGroupSelection] = {
    "BTC": PeerGroupSelection(
        symbol="BTC",
        group=None,
        unavailable_because=(
            "Every candidate group that contains Bitcoin is dominated by "
            "it. The provider's Layer 1 category is 80.2% of the whole "
            "tracked market and Bitcoin is the majority of that, so the "
            "comparison would be Bitcoin against itself twice over. The "
            "broad market comparison is kept instead, with Bitcoin's own "
            "share of it stated beside it — which is the same caveat, "
            "measured rather than hidden."
        ),
        considered=(
            _SMART_CONTRACT_PLATFORM_REJECTED,
            ConsideredPeerGroup(
                key="layer-1",
                name="Layer 1 (L1)",
                rejected_because=(
                    "Bitcoin leads it, and the category is 80.2% of the "
                    "tracked market. Comparing the largest constituent "
                    "with an aggregate it dominates measures almost "
                    "nothing."
                ),
            ),
        ),
    ),
    "ETH": PeerGroupSelection(
        symbol="ETH",
        group=PeerGroup(
            key="layer-1",
            name="Layer 1 (L1)",
            provider=_COINGECKO,
            selected_because=(
                "base-layer networks are what the market prices Ethereum "
                "alongside, and the category's membership — read on "
                "2026-08-10 — is base layers: Bitcoin, BNB, XRP, Solana, "
                "Tron, Cardano, Monero. It is a market peer group and "
                "not an analytical one: MOVRvest reads Ethereum as a "
                "smart-contract network, and this category deliberately "
                "contains chains that are not."
            ),
            caveats=(
                "Bitcoin leads this category and the category is 80.2% "
                "of the whole tracked market, so this comparison is "
                "closer to a comparison with the market than the name "
                "suggests.",
            ),
        ),
        considered=(_SMART_CONTRACT_PLATFORM_REJECTED,),
    ),
    "SOL": PeerGroupSelection(
        symbol="SOL",
        group=PeerGroup(
            key="layer-1",
            name="Layer 1 (L1)",
            provider=_COINGECKO,
            selected_because=(
                "the same base-layer group Ethereum is compared against, "
                "and Solana is one of its ten largest members."
            ),
            caveats=(
                "Bitcoin leads this category and the category is 80.2% "
                "of the whole tracked market.",
            ),
        ),
        considered=(_SMART_CONTRACT_PLATFORM_REJECTED,),
    ),
    "ADA": PeerGroupSelection(
        symbol="ADA",
        group=PeerGroup(
            key="layer-1",
            name="Layer 1 (L1)",
            provider=_COINGECKO,
            selected_because=(
                "the same base-layer group, in which Cardano sits tenth "
                "by capitalisation."
            ),
            caveats=(
                "Bitcoin leads this category and the category is 80.2% "
                "of the whole tracked market.",
            ),
        ),
        considered=(_SMART_CONTRACT_PLATFORM_REJECTED,),
    ),
    "ARB": PeerGroupSelection(
        symbol="ARB",
        group=PeerGroup(
            key="rollup",
            name="Rollup",
            provider=_COINGECKO,
            selected_because=(
                "a 30-member group whose largest holdings — Arbitrum, "
                "Immutable, Optimism, Starknet — are rollup tokens, "
                "which is what Arbitrum is compared against by anyone "
                "trading the sector."
            ),
            caveats=(
                "Arbitrum is among the largest members, so part of the "
                "group's own move is its own.",
            ),
        ),
        considered=(
            ConsideredPeerGroup(
                key="layer-2",
                name="Layer 2 (L2)",
                rejected_because=(
                    "read on 2026-08-10, its top ten includes WETH — "
                    "wrapped ether, which has no economics of its own "
                    "and simply tracks Ethereum — and the exchange "
                    "tokens OKB and MNT. A group containing a wrapper of "
                    "another asset is not a scaling peer set."
                ),
            ),
        ),
    ),
    "HYPE": PeerGroupSelection(
        symbol="HYPE",
        group=PeerGroup(
            key="decentralized-perpetuals",
            name="Perpetuals",
            provider=_COINGECKO,
            selected_because=(
                "Hyperliquid is a perpetuals venue, and this group is "
                "the venues it competes with for the same flow — Aster, "
                "Jupiter, dYdX. The provider's Layer 1 category also "
                "contains it, and would compare an exchange with "
                "settlement layers rather than with its competitors."
            ),
            caveats=(
                "Hyperliquid is the largest member by a wide margin, so "
                "this group's move is substantially its own — the share "
                "is stated beside the comparison.",
            ),
        ),
        considered=(
            ConsideredPeerGroup(
                key="layer-1",
                name="Layer 1 (L1)",
                rejected_because=(
                    "it does contain Hyperliquid, and it would compare a "
                    "trading venue against base-layer networks. The "
                    "chain is one of two economic entities behind this "
                    "token and the venue earns 99.6% of the fees."
                ),
            ),
            ConsideredPeerGroup(
                key="exchange-based-tokens",
                name="Exchange-based Tokens",
                rejected_because=(
                    "it is led by centralised-exchange tokens, whose "
                    "business, custody model and regulatory exposure are "
                    "not Hyperliquid's."
                ),
            ),
        ),
    ),
    "1INCH": PeerGroupSelection(
        symbol="1INCH",
        group=PeerGroup(
            key="dex-aggregator",
            name="Dex Aggregator",
            provider=_COINGECKO,
            selected_because=(
                "a 31-member group of routing protocols — Jupiter, "
                "1inch, and smaller aggregators — which is exactly the "
                "business 1inch is in, and the one group whose members "
                "share its economics rather than its theme."
            ),
        ),
        considered=(
            ConsideredPeerGroup(
                key="decentralized-exchange",
                name="Decentralized Exchange (DEX)",
                rejected_because=(
                    "an aggregator routes to venues rather than running "
                    "one, which is the same distinction that made this "
                    "platform decline a venue's questions for it in S3."
                ),
            ),
        ),
    ),
    "TAO": PeerGroupSelection(
        symbol="TAO",
        group=None,
        unavailable_because=(
            "No group in the provider's taxonomy is an economic peer set "
            "for this network. Its Artificial Intelligence category — "
            "read on 2026-08-10 — is led by Chainlink, an oracle "
            "network, then two general-purpose layer-1s and a rendering "
            "marketplace. Those share a theme rather than a business, "
            "and a return computed over them would measure a narrative. "
            "This platform already declined to classify TAO from an AI "
            "label; comparing it against one would be the same mistake "
            "with a number attached. Only the broad market comparison is "
            "offered."
        ),
        considered=(
            ConsideredPeerGroup(
                key="artificial-intelligence",
                name="Artificial Intelligence (AI)",
                rejected_because=(
                    "its largest members are an oracle network, two "
                    "general-purpose layer-1s and a rendering "
                    "marketplace. A marketing theme is not a peer group."
                ),
            ),
        ),
    ),
}


def peer_group_for(symbol: str) -> PeerGroupSelection:
    """This security's peer group, or the honest absence of one."""

    normalized = symbol.upper().strip()

    selection = PEER_GROUPS.get(normalized)

    if selection is not None:
        return selection

    return PeerGroupSelection(
        symbol=normalized,
        group=None,
        unavailable_because=(
            f"No peer group has been verified for {normalized}. A "
            "category matching its name would be a guess about what is "
            "inside it, and this platform reads the membership before "
            "using a group."
        ),
    )


#: Every provider category this platform reads, deduplicated.
#:
#: The acquisition batch's own list: one call per group, so a group used
#: by three securities costs one read rather than three.
def acquired_groups() -> tuple[PeerGroup, ...]:
    """The peer groups an acquisition cycle reads, each once."""

    seen: dict[str, PeerGroup] = {}

    for selection in PEER_GROUPS.values():
        if selection.group is not None:
            seen.setdefault(selection.group.key, selection.group)

    return tuple(seen.values())
