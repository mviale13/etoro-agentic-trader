"""How a business creates value, explained from consensus knowledge.

The first consumer of the knowledge layer's finished contract, and a
different responsibility from it. Company Knowledge answers *what has
been established*; Business Understanding answers *how this business
creates value* — one level above the knowledge, one level below the
committees that will eventually reason from it.

```text
CompanyKnowledgeConsensus
          ↓
BusinessUnderstanding          ← this module
          ↓
PlaybookSelector → analysts → Executive Committee
```

Three rules make it trustworthy, and all three are structural:

- **Completely deterministic.** No model is asked, nothing is re-read,
  and the same consensus in produces the same understanding out. This
  is an explanation layer, not another reading.
- **Every statement traces to the consensus.** The economic engine is
  worded from settled segments, settled mechanisms and the archetype —
  never from a name, an industry, or anything a reader might "know"
  about the company. A business this platform cannot describe from its
  consensus facts is a business it does not claim to understand.
- **It never infers, and never compensates.** Where the consensus says
  *not established*, understanding says *not established*. What it may
  add — and does — is why the gap matters: for a narrow or unsettled
  claim, it evaluates what the rules would have concluded had the claim
  settled at each of its **observed** answers, and reports which
  conclusions are contingent on which majorities. Observed answers
  only, verbatim: evaluating an answer nobody gave would be synthesis
  wearing arithmetic's clothes.

Uncertainty belongs beside the explanation, not underneath it. A
mechanism carried by a 3/5 majority is reported as exactly that,
wherever it appears.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.agreement import Agreement
from app.domain.company_archetype import CompanyArchetype, Unestablished
from app.domain.company_knowledge import RevenueModel
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class SellsThrough:
    """One part of the business, as consensus establishes it.

    Deliberately not carrying a quoted description: the spans never
    settle, so what a segment *does* in prose is evidence attached to
    observations, not a settled fact this layer may restate. What is
    settled — and therefore what this carries — is the segment's
    existence, its measured share, and the ways it earns.
    """

    name: str

    #: The settled share of revenue, or None with the reason beside it.
    share: float | None
    unmeasured_because: str | None

    #: The settled ways this part earns. Empty with the reason where
    #: nothing settled.
    mechanisms: tuple[RevenueModel, ...]
    mechanisms_because: str | None


@dataclass(frozen=True, slots=True)
class RevenueMechanism:
    """One way the business earns, and how firmly that is held.

    The agreement carried is the *narrowest* earning claim among the
    segments this mechanism runs through: a mechanism is exactly as
    established as the weakest claim that carries it.
    """

    model: RevenueModel

    #: The segments whose settled earning includes this mechanism.
    through: tuple[str, ...]

    #: How much of measured revenue those segments account for. None
    #: where no size was settled — coverage over unmeasured segments
    #: would be a weight nobody measured.
    coverage: float | None

    #: The narrowest earning agreement among the carrying segments.
    support: Agreement


@dataclass(frozen=True, slots=True)
class AlternativeConclusion:
    """What the rules would conclude under one observed answer."""

    #: The observed answer, verbatim as the observations stated it.
    answer: str

    #: How many observations gave it.
    given: int

    #: What `classify` concludes with that answer settled.
    concludes: str


@dataclass(frozen=True, slots=True)
class Contingency:
    """One narrow or unsettled claim, and what settling it would change.

    The "why it matters" a gap is owed. Each alternative is one of the
    claim's *observed* answers evaluated through the identical rules —
    deterministic arithmetic about the rules, never a new fact about
    the company. A contingency whose every alternative concludes the
    same thing is evidence the conclusion is insensitive to the gap;
    one that concludes differently says precisely which majority the
    conclusion depends on.
    """

    #: The claim, in the same words the consensus uses.
    claim: str

    #: Its full distribution.
    agreement: Agreement

    #: What the rules conclude as things stand.
    as_it_stands: str

    #: Whether the claim currently participates in the conclusion at
    #: all. An unsettled claim was excluded, not resolved — a different
    #: fact from a narrow claim that was consumed.
    consumed: bool

    alternatives: tuple[AlternativeConclusion, ...]

    @property
    def could_change_conclusion(self) -> bool:
        """Whether any observed answer would conclude differently."""

        return any(
            alternative.concludes != self.as_it_stands
            for alternative in self.alternatives
        )


@dataclass(frozen=True, slots=True)
class BusinessUnderstanding:
    """How this business creates value, and how firmly that is known.

    Everything here is derived from one `CompanyKnowledgeConsensus` by
    arithmetic and rule evaluation. Nothing is read, nothing is
    inferred, and every absence below is the consensus's own absence,
    passed through with its reason.
    """

    symbol: str

    #: The document everything traces to, as an investor would cite it.
    source: str

    reading: Provenance

    #: The consensus's own width and state, carried so no consumer of
    #: an understanding can forget what it rests on.
    quorate: bool
    observation_count: int
    quorum: int

    #: The engine in one sentence: single- or multi-engine, and what
    #: leads. Worded from the archetype and coverage, never from a name.
    engine: str

    #: What the business sells through — its settled segments.
    sells: tuple[SellsThrough, ...]

    #: How it earns, widest coverage first, each with its support.
    mechanisms: tuple[RevenueMechanism, ...]

    #: What kind of business the rules concluded, in full — the rulings,
    #: the basis, and what it rests on travel with it.
    characteristics: CompanyArchetype

    #: The narrow and unsettled claims, each evaluated against its own
    #: observed answers.
    contingencies: tuple[Contingency, ...]

    #: The consensus's gaps, verbatim. Never compensated for.
    not_established: tuple[Unestablished, ...]

    #: Why there are no segments at all, where there are none.
    segments_because: str | None

    @property
    def narrow_support(self) -> tuple[RevenueMechanism, ...]:
        """The mechanisms whose narrowest support is short of unanimous."""

        return tuple(
            mechanism for mechanism in self.mechanisms if not mechanism.support.settled
        )
