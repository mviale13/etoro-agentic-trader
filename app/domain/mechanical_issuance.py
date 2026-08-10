"""What supply rule a protocol defines, and what path follows from it.

The other half of the supply vocabulary. S4.6 asked *what does this
number count*; this asks *what rule will create the next ones*, and it
exists because the corpus proved the two questions have different
answers for different kinds of asset.

**A mechanical issuance rule and a vesting schedule are two different
economic objects.** Bitcoin's supply arrives because a consensus rule
pays a subsidy that halves; Arbitrum's arrives because a contract
releases tokens somebody allocated. Only the first is modelled here, and
an allocation-release token gets *no entry* rather than an empty one —
inventing a mechanical rule for a token that has none would be the
placeholder the ruling forbids.

Three things kept apart, because collapsing them is how a projection
becomes a claim about the future:

```text
state    what the protocol has issued, and what it holds back
rule     the mechanism, its parameters, and who can change them
path     what the rule implies from here — MOVRvest's arithmetic,
         under the rule as observed, and never an observation
```

**A projection is not an observed future fact.** Every derived figure
carries the rule version it came from, the state it started at, and the
mutability of the rule — because "Bitcoin will have issued 164,362 more
coins in a year" is only true while nobody changes the rule, and a
governance-adjustable rule and a consensus-fixed one are not
epistemically equivalent merely because both can be projected today.

Nothing here scores, bands or interprets. A published rule is not
thereby a good rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.supply_semantics import PrimaryProvenance


class IssuanceMechanism(StrEnum):
    """How a protocol creates new supply. Named for the mechanism, never
    for the asset, so a second chain sharing one reuses the entry."""

    #: A block reward that steps down on a fixed interval. Bitcoin.
    HALVING_SUBSIDY = "halving_subsidy"

    #: A fixed proportion of a remaining pot, drawn each period. Cardano
    #: takes rho of its reserves per epoch, so issuance decays
    #: geometrically and the pot is never quite empty.
    RESERVE_DRAW = "reserve_draw"

    #: An annual rate that tapers to a floor. Solana starts at 8%,
    #: reduces 15% a year and stops falling at 1.5%.
    TAPERING_INFLATION = "tapering_inflation"

    @property
    def stated(self) -> str:
        return _MECHANISMS[self]

    @property
    def described(self) -> str:
        return _DESCRIBED[self]


_MECHANISMS = {
    IssuanceMechanism.HALVING_SUBSIDY: "Halving subsidy",
    IssuanceMechanism.RESERVE_DRAW: "Reserve draw",
    IssuanceMechanism.TAPERING_INFLATION: "Tapering inflation",
}


_DESCRIBED = {
    IssuanceMechanism.HALVING_SUBSIDY: (
        "a block reward that halves on a fixed interval until it reaches zero"
    ),
    IssuanceMechanism.RESERVE_DRAW: (
        "a fixed proportion of a remaining pot, drawn each period, so "
        "issuance decays and the pot is never quite exhausted"
    ),
    IssuanceMechanism.TAPERING_INFLATION: (
        "an annual issuance rate that reduces by a fixed proportion each "
        "year until it reaches a floor"
    ),
}


class RuleMutability(StrEnum):
    """What it would take to change the rule.

    Recorded and **not scored**. It is here because a reproducible
    projection says nothing about whether the rule will still hold: a
    consensus-fixed schedule and a parameter a governance vote can move
    are not the same claim about the future, and a surface that printed
    both as "the issuance path" would flatten the difference.
    """

    #: Changing it requires changing consensus — a fork the whole network
    #: must adopt.
    PROTOCOL_FIXED = "protocol_fixed"

    #: A protocol parameter, changeable by the chain's own governance
    #: without a fork.
    GOVERNANCE_PARAMETER = "governance_parameter"

    #: This platform has not established what it would take.
    UNKNOWN = "unknown"

    @property
    def stated(self) -> str:
        return _MUTABILITY[self]

    @property
    def because(self) -> str:
        return _MUTABILITY_BECAUSE[self]


_MUTABILITY = {
    RuleMutability.PROTOCOL_FIXED: "Protocol-fixed",
    RuleMutability.GOVERNANCE_PARAMETER: "Governance parameter",
    RuleMutability.UNKNOWN: "Not established",
}


_MUTABILITY_BECAUSE = {
    RuleMutability.PROTOCOL_FIXED: (
        "changing it would require a consensus change the whole network has to adopt"
    ),
    RuleMutability.GOVERNANCE_PARAMETER: (
        "it is a protocol parameter the chain's own governance can change "
        "without a fork, so the path holds only while the parameter does"
    ),
    RuleMutability.UNKNOWN: (
        "what it would take to change this rule has not been established here"
    ),
}


@dataclass(frozen=True, slots=True)
class RuleParameter:
    """One input the rule needs, and where it came from.

    Every parameter names its surface. A rule assembled from parameters
    this platform remembered is the blob-fee failure with a longer
    runway, so the field is not optional and "remembered" is not one of
    the things it can say.
    """

    name: str
    value: float
    unit: str

    #: The endpoint and field it was read from, precisely enough to
    #: fetch again.
    read_from: str

    #: What the parameter means, in the protocol's terms.
    means: str


@dataclass(frozen=True, slots=True)
class IssuanceState:
    """What the protocol has issued as of one observation.

    Kept apart from the rule and from the path — and *within* itself,
    kept honest about which of those two it came from. Bitcoin's emitted
    total is the rule run to the tip, not a figure any source published;
    Cardano's is the ledger's own `supply`. Presenting both as "state"
    would let a projection's own output be read back as the observation
    that grounds it.

    `emitted` is None where nothing here can say it. Solana publishes a
    rate and no supply, and a zero would be a number nobody measured.
    """

    unit: str

    #: The chain position the reading was taken at — a height, an epoch,
    #: a slot. Named because a projection starting from an unstated
    #: position cannot be re-run.
    position: str

    observed_at: datetime

    emitted: float | None = None

    #: Whether `emitted` came from the rule rather than from a source.
    #: True for Bitcoin, and the reason its total does not establish.
    emitted_is_derived: bool = False

    #: The pot the rule still has to draw from, where the mechanism has
    #: one. Bitcoin's is implied by the cap; Cardano publishes it.
    remaining: float | None = None

    #: The rate the protocol is currently issuing at, where it publishes
    #: one, as an annual proportion.
    current_rate: float | None = None


@dataclass(frozen=True, slots=True)
class ProjectedIssuance:
    """What the rule implies at one horizon. MOVRvest's arithmetic.

    Never presented as an observation. The wording a surface must use is
    *under the currently observed issuance rule*, and the fields here
    exist so that sentence can be written truthfully: the rule version,
    the state it started from, and whether the rule can be changed all
    travel with the number.
    """

    #: How far ahead, in words a reader can check — "1 year", "to the
    #: next halving".
    horizon: str

    #: New supply the rule creates over that horizon.
    issuance: float
    unit: str

    #: As a share of what has already been issued.
    share_of_emitted: float

    #: The rule version this was computed under, so a later rule
    #: recomputes rather than overwrites.
    rule_version: str


@dataclass(frozen=True, slots=True)
class MechanicalIssuance:
    """One protocol's issuance rule, its state, and what follows.

    Absent for any asset whose supply arrives by allocation release. That
    is not a gap: Arbitrum has no mechanical rule to read, and an entry
    saying so in the shape of a rule would be a placeholder pretending to
    be evidence.
    """

    symbol: str

    mechanism: IssuanceMechanism

    state: IssuanceState

    #: The rule in one checkable line.
    formula: str

    parameters: tuple[RuleParameter, ...]

    mutability: RuleMutability

    #: Model C provenance for the reading behind it, so the same gate
    #: that judges a supply figure judges this one.
    provenance: PrimaryProvenance

    authority: EvidenceAuthority
    standing: EvidenceStanding

    source: str

    #: What the rule implies from here. Empty where the rule is known and
    #: the path is not — which is a real state, and different from having
    #: no rule.
    path: tuple[ProjectedIssuance, ...] = ()

    #: This platform's account of the standing.
    because: str | None = None

    #: What a reader would otherwise misread. Never empty for a rule
    #: whose projection outruns its evidence.
    caveats: tuple[str, ...] = ()

    @property
    def is_projectable(self) -> bool:
        return bool(self.path)

    @property
    def parameters_are_all_read(self) -> bool:
        """Whether every parameter names a surface it was read from.

        The gate-3 property, asked of the rule rather than of a figure.
        A rule with an unsourced parameter cannot be trusted to project
        even when its arithmetic is perfect.
        """

        return all(parameter.read_from for parameter in self.parameters)
