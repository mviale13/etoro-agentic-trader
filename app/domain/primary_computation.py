"""The reproducibility contract: enough to run the computation again.

A deterministic computation does not become established because one
Python function returned a number. It becomes checkable when a competent
stranger could obtain the same figure — and that requires the platform to
have written down what it read, from where, over what interval, in what
units, under which rule, and at which version of that rule.

```text
surface   which canonical source, on which network
entity    what the figure is measured over
window    which blocks or which moment, and how long that was
inputs    the raw observations, named so they can be fetched again
formula   the transformation, in one checkable line
rule      the version of this platform's rule that produced it
```

**The version matters more than it looks.** A rule improved later must be
able to recompute the same historical interval *without pretending the
original observation never existed* — the same discipline the knowledge
store already lives by, where an observation is appended and a consensus
is derived on read. A figure whose rule version is unrecorded cannot be
re-judged; it can only be replaced.

**Nothing here changes a standing.** A `PrimaryComputation` carries its
authority and its standing side by side, and the standing rule is
untouched by this slice: with one access path and no ruling on primary
authority, a computation is `CLAIMED` — attributed, dated, reproducible,
and consumed by nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding


@dataclass(frozen=True, slots=True)
class SourceSurface:
    """One place canonical state can be read, and how canonical it is.

    `canonical` is a claim about the *state*, not about the operator: a
    public RPC endpoint is a stranger's machine serving a ledger anyone
    can verify, while a vendor's API is a stranger's machine serving a
    figure only that vendor computed. `because` states which of those
    this is, so the distinction never rests on the word "on-chain".
    """

    key: str
    name: str

    #: The chain or protocol whose state this serves.
    network: str

    #: The endpoint family. Never a credential, and never a full URL
    #: with a key in it.
    endpoint: str

    canonical: bool

    because: str


@dataclass(frozen=True, slots=True)
class ObservationWindow:
    """Exactly what interval a figure covers.

    A flow needs a window and a level needs a moment, and the two are
    different objects here rather than one with an optional field —
    which is the same rule the market family enforces on its intervals.
    """

    #: "blocks", "epoch", or "instant".
    kind: str

    observed_at: datetime

    #: Inclusive block range, where the window is a range of blocks.
    first_block: int | None = None
    last_block: int | None = None

    #: The chain's own timestamps at each end.
    first_timestamp: int | None = None
    last_timestamp: int | None = None

    @property
    def seconds(self) -> int | None:
        if self.first_timestamp is None or self.last_timestamp is None:
            return None

        return self.last_timestamp - self.first_timestamp

    @property
    def blocks(self) -> int | None:
        if self.first_block is None or self.last_block is None:
            return None

        return self.last_block - self.first_block + 1

    @property
    def stated(self) -> str:
        """The window as a surface prints it, worded here once."""

        if self.kind == "instant":
            return f"at {self.observed_at:%Y-%m-%d %H:%M} UTC"

        if self.blocks is not None:
            span = f", {self.seconds}s" if self.seconds is not None else ""

            return (
                f"blocks {self.first_block:,}–{self.last_block:,} "
                f"({self.blocks} blocks{span})"
            )

        return self.kind


@dataclass(frozen=True, slots=True)
class PrimaryComputation:
    """One figure computed from canonical state, with everything to redo it."""

    key: str
    label: str

    surface: SourceSurface

    #: What the figure is measured over, in this platform's own words.
    entity: str

    window: ObservationWindow

    value: float
    unit: str

    #: The transformation in one checkable line.
    formula: str

    #: The version of this platform's rule. A later rule recomputes the
    #: same interval rather than overwriting what this one said.
    rule_version: str

    authority: EvidenceAuthority
    standing: EvidenceStanding

    #: The raw observations this rests on, named so they can be fetched
    #: again — not the values themselves, which would be a copy rather
    #: than a reference.
    inputs: tuple[str, ...] = ()

    #: This platform's account of the standing.
    because: str | None = None

    #: What would make a reader misread it. Never empty for a figure
    #: whose semantics were surprising.
    caveats: tuple[str, ...] = ()

    #: A secondary source's figure for the same question, where one
    #: exists — carried for perimeter comparison, never to be averaged
    #: with this one. A difference is evidence about the perimeters.
    compared_with: tuple[str, ...] = ()

    @property
    def is_repeatable(self) -> bool:
        """Whether a stranger has been given enough to run this again.

        Deliberately mechanical: a surface, an entity, a window, inputs,
        a formula and a rule version. A computation missing any of them
        is a number with a story, and the property exists so a test can
        say so rather than a reviewer having to notice.
        """

        return bool(
            self.surface.endpoint
            and self.entity
            and self.inputs
            and self.formula
            and self.rule_version
        )

    @property
    def is_independently_reproducible(self) -> bool:
        """Whether it could be obtained again *without* trusting this source.

        The distinction the whole slice turns on, and one the mechanical
        check above cannot make. Bitcoin's fee total is perfectly
        repeatable — ask the same explorer and the same number comes
        back — and it is not independently reproducible, because
        recovering it from the ledger needs an index this platform does
        not hold. Repeating somebody's answer is not checking it.
        """

        return (
            self.is_repeatable and self.surface.canonical and self.authority.is_primary
        )

    @property
    def stated(self) -> str:
        """The figure as a surface prints it."""

        if abs(self.value) >= 1_000_000:
            figure = f"{self.value:,.2f}"
        elif abs(self.value) >= 1:
            figure = f"{self.value:,.4f}"
        else:
            figure = f"{self.value:,.8f}"

        return f"{figure} {self.unit}"


@dataclass(frozen=True, slots=True)
class MechanismEvidence:
    """Evidence that an economic mechanism exists, apart from its size.

    The distinction the ruling insisted on and the corpus vindicated:
    *a fund exists and holds the token* and *the fund received X today*
    are different claims with different evidence and different
    reachability. Hyperliquid's Assistance Fund can be read from the
    protocol's own API — address, balance, and its listing among the
    non-circulating accounts — while what flowed into it over a day
    cannot be, from one reading.

    A mechanism established here says nothing about whether it is worth
    anything. That remains an interpretation nobody is authorised to
    make.
    """

    key: str
    label: str

    surface: SourceSurface

    #: What the source shows, in this platform's words.
    observed: str

    #: The source's own wording or identifiers, verbatim where it has
    #: any — an address, a field name, a published sentence.
    evidence: tuple[str, ...]

    authority: EvidenceAuthority
    standing: EvidenceStanding

    observed_at: datetime

    because: str

    #: What this does *not* establish. Always populated: a mechanism's
    #: existence is routinely read as a statement about its size.
    does_not_establish: tuple[str, ...] = ()
