"""Which quantity each source is actually reporting, per security.

The table that turns a label collision into a set of distinct facts.
Every entry was verified by hand against the ledger or the protocol
during the S4.6 measurement, in the same discipline as
`PROTOCOL_ENTITIES` and `PEER_GROUPS`: the basis is stated so it can be
argued with, and a source absent from a security's row is mapped to
nothing rather than guessed.

**Cardano is the case that proves the vocabulary.** Its ledger publishes
four quantities, and three vendors were each reporting a different one
to within a rounding error:

```text
TokenInsight  38,803,572,882   = ledger `supply`                0.000%
CoinGecko     37,353,519,634   = `circulation + reward`         0.015%
Yahoo         36,550,320,128   = ledger `circulation`         0.0000%  ← S1 rejected
```

None of them was wrong. The label was.

**An undisclosed methodology is not a different methodology.** Where a
vendor publishes no exclusion set — which is most of them — the mapping
says so, and `compare` then treats it as a claim to the same fact. That
is what keeps HYPE honestly conflicted rather than letting three numbers
coexist by being equally unexplained.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.supply_semantics import SupplyConcept, SupplyMethodology

#: The protocol's own constant, reported by whoever reports it. A cap is
#: the one supply quantity that is not anybody's methodology: it is
#: enforced or it does not exist.
PROTOCOL_CAP = SupplyMethodology(
    key="protocol-cap",
    defined_by="the protocol",
    stated="the maximum the protocol will ever allow to exist",
    disclosed=True,
    includes=("every token the protocol can ever issue",),
)

#: What a chain says exists right now.
PROTOCOL_EMITTED = SupplyMethodology(
    key="protocol-emitted",
    defined_by="the protocol",
    stated="tokens the ledger records as existing",
    disclosed=True,
    includes=("every token issued and not destroyed",),
    excludes=("tokens the protocol has not issued yet",),
)

CARDANO_SUPPLY = SupplyMethodology(
    key="cardano-ledger-supply",
    defined_by="the Cardano ledger",
    stated="everything issued out of reserves",
    disclosed=True,
    includes=("circulation", "the treasury", "undistributed rewards"),
    excludes=("reserves — ada not yet issued",),
)

CARDANO_CIRCULATION = SupplyMethodology(
    key="cardano-ledger-circulation",
    defined_by="the Cardano ledger",
    stated="the ledger's own circulation quantity",
    disclosed=True,
    includes=("ada held in ordinary accounts",),
    excludes=("the treasury", "undistributed rewards", "reserves"),
)

CARDANO_CIRCULATION_AND_REWARDS = SupplyMethodology(
    key="cardano-circulation-and-rewards",
    defined_by="a vendor counting rewards as circulating",
    stated="circulation plus rewards earned and not yet withdrawn",
    disclosed=True,
    includes=("circulation", "undistributed rewards"),
    excludes=("the treasury", "reserves"),
)

HYPERLIQUID_EXCLUSIONS = SupplyMethodology(
    key="hyperliquid-protocol-exclusions",
    defined_by="the Hyperliquid protocol",
    stated=(
        "emitted supply after the protocol's own named exclusions — a "
        "foundation address, the Assistance Fund and two burn addresses"
    ),
    disclosed=True,
    includes=("tokens already emitted",),
    excludes=(
        "0x43e9…a251, a foundation address",
        "0xfefe…fefe, the Assistance Fund",
        "the zero address and the burn address",
        "future emissions, which the protocol's own totalSupply counts",
    ),
)


def undisclosed(vendor: str) -> SupplyMethodology:
    """A vendor that publishes a circulating figure and not its definition.

    Deliberately not a per-vendor constant: there is nothing to
    distinguish one unexplained definition from another, and giving each
    its own key would let two vendors coexist purely because they are
    both silent.
    """

    return SupplyMethodology(
        key="undisclosed",
        defined_by=vendor,
        stated=(
            f"{vendor} publishes a circulating figure and not the balances it excludes"
        ),
        disclosed=False,
    )


@dataclass(frozen=True, slots=True)
class SourceMapping:
    """What one source's number, under one of its labels, actually counts."""

    #: The fact name in `app.domain.token_facts.TOKEN_FACTS`.
    fact: str

    concept: SupplyConcept

    methodology: SupplyMethodology

    #: Why this platform believes the mapping. Empty for the default
    #: reading of an undisclosed vendor label, which asserts nothing.
    basis: str = ""

    #: What the source called it, where that differs from the concept.
    reported_as: str | None = None

    caveats: tuple[str, ...] = ()


#: How each vendor's labels read when nothing security-specific is known.
#:
#: The honest default: a vendor's "circulating supply" is an estimate
#: under a definition it does not publish, and its "total supply" is its
#: view of what exists. Neither is promoted to a ledger quantity without
#: a measurement saying so.
def _default(vendor: str) -> tuple[SourceMapping, ...]:
    return (
        SourceMapping(
            fact="circulating_supply",
            concept=SupplyConcept.CIRCULATING_ESTIMATE,
            methodology=undisclosed(vendor),
            reported_as="circulating supply",
        ),
        SourceMapping(
            fact="total_supply",
            concept=SupplyConcept.EMITTED_SUPPLY,
            methodology=SupplyMethodology(
                key="vendor-emitted",
                defined_by=vendor,
                stated=f"{vendor}'s view of the tokens that exist",
                disclosed=False,
            ),
            reported_as="total supply",
        ),
        SourceMapping(
            fact="max_supply",
            concept=SupplyConcept.MAX_SUPPLY,
            methodology=PROTOCOL_CAP,
            reported_as="max supply",
            basis="the protocol's own constant, reported by the vendor",
        ),
    )


#: Security-specific mappings, each measured. Where a security has an
#: entry for a vendor, it replaces that vendor's default reading of the
#: named fact; every other label falls through to the default.
MEASURED: dict[str, dict[str, tuple[SourceMapping, ...]]] = {
    "ADA": {
        "TokenInsight": (
            SourceMapping(
                fact="circulating_supply",
                concept=SupplyConcept.EMITTED_SUPPLY,
                methodology=CARDANO_SUPPLY,
                reported_as="circulating supply",
                basis=(
                    "measured 2026-08-10: 38,803,572,882 against the "
                    "ledger's own `supply` of 38,803,572,882.17 — 0.000%. "
                    "It is not a circulating estimate at all; it is "
                    "everything the ledger has issued."
                ),
            ),
        ),
        "CoinGecko": (
            SourceMapping(
                fact="circulating_supply",
                concept=SupplyConcept.CIRCULATING_ESTIMATE,
                methodology=CARDANO_CIRCULATION_AND_REWARDS,
                reported_as="circulating supply",
                basis=(
                    "measured 2026-08-10: 37,353,519,634 against the "
                    "ledger's circulation plus rewards of 37,348,055,948 "
                    "— 0.015%, with the readings hours apart."
                ),
            ),
            SourceMapping(
                fact="total_supply",
                concept=SupplyConcept.EMITTED_SUPPLY,
                methodology=SupplyMethodology(
                    key="vendor-emitted",
                    defined_by="CoinGecko",
                    stated="CoinGecko's view of the tokens that exist",
                    disclosed=False,
                ),
                reported_as="total supply",
                caveats=(
                    "45,000,000,000 exactly, which is Cardano's protocol "
                    "maximum rather than what has been issued. The "
                    "ledger's own supply was 38,803,572,882 when this "
                    "was measured — so this figure conflicts with the "
                    "chain, and the conflict is real.",
                ),
            ),
        ),
        "Yahoo Finance": (
            SourceMapping(
                fact="circulating_supply",
                concept=SupplyConcept.CIRCULATING_ESTIMATE,
                methodology=CARDANO_CIRCULATION,
                reported_as="circulating supply",
                basis=(
                    "measured 2026-08-10: 36,550,320,128 against the "
                    "ledger's own `circulation` of 36,550,320,207 — "
                    "0.0000%. This platform rejected this reading in S1 "
                    "for disagreeing with the others, and it was the one "
                    "that matched a ledger quantity exactly."
                ),
            ),
        ),
    },
    "ARB": {
        "TokenInsight": (
            SourceMapping(
                fact="circulating_supply",
                concept=SupplyConcept.CIRCULATING_ESTIMATE,
                methodology=undisclosed("TokenInsight"),
                reported_as="circulating supply",
                caveats=(
                    "1,275,000,000 exactly — a round number to seven "
                    "significant figures, and the documented float at "
                    "launch. A measured quantity does not usually land on "
                    "one. This is consistent with a frozen input and is "
                    "not proof of one: the decisive test is whether it "
                    "moves across dated readings.",
                ),
            ),
        ),
    },
    "TAO": {
        "CoinGecko": (
            SourceMapping(
                fact="total_supply",
                concept=SupplyConcept.EMITTED_SUPPLY,
                methodology=SupplyMethodology(
                    key="vendor-emitted",
                    defined_by="CoinGecko",
                    stated="CoinGecko's view of the tokens that exist",
                    disclosed=False,
                ),
                reported_as="total supply",
                caveats=(
                    "21,000,000 exactly, which is Bittensor's protocol "
                    "maximum rather than what has been issued. The chain's "
                    "own TotalIssuance was 11,218,142 when this was "
                    "measured.",
                ),
            ),
        ),
    },
}


def mappings_for(symbol: str, source: str) -> tuple[SourceMapping, ...]:
    """How to read one source's supply labels for one security.

    Measured entries first, then the vendor's default reading for every
    label the measurement did not cover.
    """

    measured = MEASURED.get(symbol.upper().strip(), {}).get(source, ())

    covered = {item.fact for item in measured}

    return measured + tuple(
        item for item in _default(source) if item.fact not in covered
    )
