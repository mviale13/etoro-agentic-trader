"""Which economic system belongs to which security.

The identity discipline the filing layer already lives by, applied to
protocol economics: a ticker does not establish an economic entity, and
a shared name establishes it least of all. DefiLlama publishes
*Hyperliquid* the protocol and *Hyperliquid L1* the chain — same token,
same name, fees 224x apart and TVL 5x apart. Reading either as "HYPE's
economics" without saying which was read is the mistake this table
exists to prevent.

Every entry below was verified by hand against the provider during the
S2 measurement: the entity exists, its figures were read, and the basis
for attaching it to the security is stated so it can be argued with.
A security absent from this table has no protocol economics on this
platform — not zero, unmapped.
"""

from __future__ import annotations

from app.domain.protocol_fundamentals import ProtocolEntity, ProtocolEntityKind

#: The entities each security's economics are measured over.
#:
#: More than one is normal and is *not* a modelling failure: a token
#: whose chain and whose application are both real economic systems has
#: two, and collapsing them would be the error. They are shown apart,
#: each naming what it measures.
PROTOCOL_ENTITIES: dict[str, tuple[ProtocolEntity, ...]] = {
    "HYPE": (
        ProtocolEntity(
            key="hyperliquid-protocol",
            name="Hyperliquid",
            kind=ProtocolEntityKind.PROTOCOL,
            measures=(
                "the perpetuals and spot trading venues, and the HLP "
                "vault — the exchange itself, aggregated by the "
                "provider across those three books"
            ),
            mapping_basis=(
                "the venue's own fee methodology names HYPE: the "
                "provider records 99% of perp and spot fees going to "
                "an Assistance Fund that buys the token. The economic "
                "link to the security is stated by the source, not "
                "inferred from the shared name."
            ),
        ),
        ProtocolEntity(
            key="hyperliquid-l1-chain",
            name="Hyperliquid L1",
            kind=ProtocolEntityKind.CHAIN,
            measures=(
                "the layer-1 blockchain the exchange settles on — gas "
                "paid by its users, and the capital held on it"
            ),
            mapping_basis=(
                "the chain's native token is HYPE. A separate entity "
                "from the exchange above and vastly smaller: its gas "
                "fees run three orders of magnitude below the venue's "
                "trading fees, and reading either as the other would "
                "misstate the business by that factor."
            ),
        ),
    ),
    "ETH": (
        ProtocolEntity(
            key="ethereum-chain",
            name="Ethereum",
            kind=ProtocolEntityKind.CHAIN,
            measures="gas paid by users of the chain, and the capital held on it",
            mapping_basis="ETH is the chain's native gas and staking asset.",
        ),
    ),
    "SOL": (
        ProtocolEntity(
            key="solana-chain",
            name="Solana",
            kind=ProtocolEntityKind.CHAIN,
            measures="transaction fees paid by users, and the capital held on it",
            mapping_basis="SOL is the chain's native gas and staking asset.",
        ),
    ),
    "ADA": (
        ProtocolEntity(
            key="cardano-chain",
            name="Cardano",
            kind=ProtocolEntityKind.CHAIN,
            measures="transaction fees paid by users, and the capital held on it",
            mapping_basis="ADA is the chain's native gas and staking asset.",
        ),
    ),
    "ARB": (
        ProtocolEntity(
            key="arbitrum-chain",
            name="Arbitrum",
            kind=ProtocolEntityKind.CHAIN,
            measures="gas paid by users of the rollup, and the capital held on it",
            mapping_basis=(
                "ARB is the rollup's governance token. Note what this "
                "mapping does *not* establish: the chain's gas is paid "
                "in ETH, so its fees are not revenue to ARB holders by "
                "any mechanism the provider records. The entity is the "
                "right one; the value-accrual question is separate and "
                "unanswered."
            ),
            mapping_settled=False,
        ),
    ),
    "BTC": (
        ProtocolEntity(
            key="bitcoin-chain",
            name="Bitcoin",
            kind=ProtocolEntityKind.CHAIN,
            measures="transaction fees paid to miners, and the capital held on it",
            mapping_basis=(
                "BTC is the chain's native asset. The chain's fee "
                "economy is real and is evidence about the network; it "
                "is paid to miners, not to holders, and the provider "
                "records no holder-revenue mechanism for it."
            ),
        ),
    ),
    "TAO": (
        ProtocolEntity(
            key="bittensor-chain",
            name="Bittensor",
            kind=ProtocolEntityKind.CHAIN,
            measures="capital held on the chain",
            mapping_basis=(
                "TAO is the chain's native asset. Its DeFi footprint "
                "is small, and whether capital held on-chain is "
                "meaningful evidence for a network of this kind is a "
                "question for the archetype work, not for acquisition."
            ),
            mapping_settled=False,
        ),
    ),
    "1INCH": (
        ProtocolEntity(
            key="1inch-protocol",
            name="1inch",
            kind=ProtocolEntityKind.PROTOCOL,
            measures=(
                "the aggregator and its swap venues — fees paid by "
                "users routing trades through it"
            ),
            mapping_basis=(
                "1INCH is the protocol's governance token, and the "
                "provider records a fee split for it. The aggregator "
                "holds little capital of its own, so a TVL reading "
                "would measure something other than the business."
            ),
        ),
    ),
}


def entities_for(symbol: str) -> tuple[ProtocolEntity, ...]:
    """The economic systems mapped to this security, or none."""

    return PROTOCOL_ENTITIES.get(symbol.upper().strip(), ())
