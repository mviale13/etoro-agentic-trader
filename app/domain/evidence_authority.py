"""Where a fact came from — a second axis, never a second standing.

`EvidenceStanding` answers *how far can this be trusted*. This answers
*what kind of thing is it*, and the two are independent on purpose:

```text
standing    ESTABLISHED · CLAIMED · CONFLICTED · REJECTED · ABSENT
authority   what was observed, by whom, and who else could reproduce it
```

Overloading standing with provenance would have been the easy move and
the wrong one. `ESTABLISHED` must keep meaning **MOVRvest considers this
sufficiently grounded for canonical use** — not *"came from a
blockchain"*. Authority explains *why* a standing rule applies, and it
is what makes the corroboration question answerable at all: two vendors
disagreeing about Cardano's supply and two vendors disagreeing about
"the total crypto market cap" are not the same situation, and only the
first has a resolution.

**Primary is not a synonym for true.** The S4.5 measurement produced two
demonstrations of that, both from canonical state:

- Ethereum's blob base fee is computed from `excessBlobGas` and a
  protocol constant that changes at forks. Using the constant this
  platform knew, the answer came out **4.2 × 10¹⁵ wei against a true
  4.97 × 10⁶** — wrong by a factor of 850 million, from perfectly
  canonical inputs, by a computation that looked deterministic.
- Hyperliquid's own API publishes `totalSupply` that **includes tokens
  not yet emitted**. Any reading of it as "tokens that exist" is wrong
  by 412 million, and nothing about the source says so.

So a primary computation earns its standing through the same gate every
other fact does — identity, semantics, arithmetic — plus one more that
only it can offer: **reproducibility**. See
`app/domain/primary_computation.py`.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceAuthority(StrEnum):
    """What kind of source a fact came from, and who could check it."""

    #: Read directly from canonical protocol state or a protocol-owned
    #: surface: a chain's own RPC, its ledger's accounting endpoint, the
    #: protocol's own API. The subject *is* the source.
    PRIMARY_OBSERVATION = "primary_observation"

    #: This platform's own deterministic computation over primary
    #: observations. Reproducible by anyone with the same access and the
    #: recorded rule — which is the property that distinguishes it from
    #: every class below.
    PRIMARY_DERIVED = "primary_derived"

    #: A third party's deterministic computation over canonical state,
    #: which this platform cannot currently reproduce. Bitcoin's fee
    #: total is the corpus case: a block carries no fee figure, and
    #: recovering one needs the value of every input, which needs an
    #: indexed node. Someone computed it correctly; we are taking their
    #: word for the arithmetic, not for the observation.
    SECONDARY_COMPUTATION = "secondary_computation"

    #: A vendor's reported figure over a perimeter it chose. DefiLlama's
    #: protocol revenue, TokenInsight's market value. Corroboration by a
    #: second independent vendor is meaningful and is the current rule.
    SECONDARY_AGGREGATE = "secondary_aggregate"

    #: A figure whose *universe is the vendor's own definition*, so a
    #: second vendor computing it is computing a different quantity
    #: rather than checking this one. "Total crypto market
    #: capitalisation", a category aggregate, a rank, breadth. For these
    #: cross-provider corroboration is not merely unavailable — it is
    #: **category-inapplicable**, and pursuing it would manufacture a
    #: consensus about a question with no source-independent answer.
    PROVIDER_SCOPED_AGGREGATE = "provider_scoped_aggregate"

    #: Another party's judgment, carried under their name. A rating, a
    #: grade, a dimension score. Never evidence about the asset; only
    #: evidence about what that party thinks.
    ATTRIBUTED_OPINION = "attributed_opinion"

    @property
    def stated(self) -> str:
        return _LABELS[self]

    @property
    def described(self) -> str:
        """What this class is, in one sentence an investor can read."""

        return _DESCRIBED[self]

    @property
    def corroboration(self) -> str:
        """What would have to happen for this to establish.

        The practical output of the whole axis: it says what kind of
        work would move a fact, so an acquisition demand can be aimed at
        the thing that would actually settle it rather than at another
        website.
        """

        return _CORROBORATION[self]

    @property
    def is_primary(self) -> bool:
        return self in (
            EvidenceAuthority.PRIMARY_OBSERVATION,
            EvidenceAuthority.PRIMARY_DERIVED,
        )

    @property
    def can_be_corroborated(self) -> bool:
        """Whether a second source could even mean anything here.

        False for a provider-scoped aggregate and for an opinion. A
        surface that hides this reads their permanent ceiling as a gap
        somebody could close.
        """

        return self not in (
            EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
            EvidenceAuthority.ATTRIBUTED_OPINION,
        )


_LABELS = {
    EvidenceAuthority.PRIMARY_OBSERVATION: "Primary observation",
    EvidenceAuthority.PRIMARY_DERIVED: "Computed from primary state",
    EvidenceAuthority.SECONDARY_COMPUTATION: "Third party's computation",
    EvidenceAuthority.SECONDARY_AGGREGATE: "Provider aggregate",
    EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE: "Provider-scoped aggregate",
    EvidenceAuthority.ATTRIBUTED_OPINION: "Attributed opinion",
}


_DESCRIBED = {
    EvidenceAuthority.PRIMARY_OBSERVATION: (
        "read directly from the protocol's own state or its own API — "
        "the subject is the source"
    ),
    EvidenceAuthority.PRIMARY_DERIVED: (
        "computed by MOVRvest from primary observations, by a recorded "
        "rule anyone with the same access could run again"
    ),
    EvidenceAuthority.SECONDARY_COMPUTATION: (
        "computed by a third party from canonical state, and not "
        "reproducible here without infrastructure this platform does "
        "not run"
    ),
    EvidenceAuthority.SECONDARY_AGGREGATE: (
        "a vendor's reported figure over a perimeter the vendor chose"
    ),
    EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE: (
        "a figure whose universe is the vendor's own definition, so no "
        "source-independent value exists to be checked against"
    ),
    EvidenceAuthority.ATTRIBUTED_OPINION: (
        "another party's judgment, carried under their name and never "
        "as evidence about the asset"
    ),
}


_CORROBORATION = {
    EvidenceAuthority.PRIMARY_OBSERVATION: (
        "a second independent access path to the same canonical state — "
        "another node, another endpoint — agreeing on the reading."
    ),
    EvidenceAuthority.PRIMARY_DERIVED: (
        "a recorded rule, the raw inputs, and a second run reaching the "
        "same figure. Whether that is enough to establish without a "
        "vendor is the ruling this slice exists to inform."
    ),
    EvidenceAuthority.SECONDARY_COMPUTATION: (
        "either a second party computing it the same way, or this "
        "platform gaining the access to reproduce it — which would move "
        "the fact to a different class rather than corroborating it."
    ),
    EvidenceAuthority.SECONDARY_AGGREGATE: (
        "a second independent vendor reporting the same quantity over a "
        "comparable perimeter. The rule S1 established, unchanged."
    ),
    EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE: (
        "nothing. There is no source-independent value here, so the "
        "honest ceiling is a permanently attributed observation — "
        "*CoinGecko's universe total*, never *the* total."
    ),
    EvidenceAuthority.ATTRIBUTED_OPINION: (
        "nothing, and nothing should. It is already exactly what it claims to be."
    ),
}
