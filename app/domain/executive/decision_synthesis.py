"""The conclusion an investor can challenge, rather than a gate report.

The Artificial CIO's rationale says which gate a case reached: *"The
investment case satisfies quality, evidence, valuation, risk, and
portfolio gates."* That sentence is true, it is the same sentence under
every recommendation, and it names nothing about the company. An
investor reading it cannot tell NVIDIA's case from any other, cannot see
what would have to be wrong for the platform to be wrong, and cannot
find the one fact most likely to make them disagree.

A synthesis answers the three questions a conclusion owes:

```text
RECOMMEND
  because   the strongest facts arguing for it
  despite   the strongest fact or unresolved uncertainty arguing against
  review if a named condition occurs
```

Every part is read off canonical objects the dossier already holds.
Nothing here scores, ranks, re-weighs or decides: the decision was made
before this object existed and is unchanged by it. This only says, in
the platform's own recorded words, what the decision rests on.

## Two rules that shape the whole design

**A fact's origin travels with it.** *Large-cap company* and *net margin
31.3%, five readings of five* are both true and are not the same kind of
thing: one is this platform's analysts reading market data, the other is
a figure read out of the company's own audited statement and checked
against the cell it sits in. Presented side by side without saying
which is which, the weaker borrows the stronger's authority. So every
fact carries its `FactOrigin`.

**An empty part says so.** Where the canonical case records no opposing
fact, or no condition for review, this reports that in words rather than
filling the slot. A conclusion that invents a trigger is worse than one
that admits it has none, because the investor stops looking for one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.committee.opinion import Uncertainty
from app.domain.decision_state import DecisionState


class FactOrigin(StrEnum):
    """Where a fact in the conclusion came from, and therefore how far it goes."""

    #: Read out of the company's own filing and checked against the cell
    #: or span it sits in. The strongest thing this platform holds.
    ESTABLISHED = "established"

    #: This platform's analysts, reading market and provider data. A
    #: judgment about the security rather than a figure the company
    #: published — sound, and a different kind of claim.
    ASSESSED = "assessed"


@dataclass(frozen=True, slots=True)
class SynthesisFact:
    """One fact in the conclusion, with where it came from."""

    statement: str
    origin: FactOrigin

    #: Which committee's position this fact stands under, where one
    #: does. An investor weighing a reservation reads it differently
    #: when they can see it was the Risk Committee's ground rather than
    #: an unattributed line: attribution is what turns a list of facts
    #: back into a discussion.
    #:
    #: None for a fact no committee's remit covers — the established
    #: facts below, which no analyst consumed.
    committee: str | None = None

    @property
    def is_established(self) -> bool:
        return self.origin is FactOrigin.ESTABLISHED


@dataclass(frozen=True, slots=True)
class ReviewCondition:
    """A named condition under which the decision should be looked at again.

    Deliberately not called an invalidation condition. The thesis carries
    a field by that name whose contents are the account's weaknesses and
    the market's risks — identical under every symbol, and already shown
    on the same page as portfolio context. A condition here is about
    *this security*, or it is not here.
    """

    condition: str
    origin: FactOrigin

    #: What it would change, where the platform can say. A contingency
    #: knows the conclusion its alternative reaches; a missing
    #: measurement only knows that it is missing.
    would_change: str | None = None


@dataclass(frozen=True, slots=True)
class CommitteeUncertainty:
    """One thing a named committee could not settle.

    Attributed, because *which* committee cannot see something tells an
    investor what the gap costs: the Risk Committee unable to measure
    volatility and the Investment Committee unable to read a valuation
    are both absences, and they hold back different halves of the case.
    """

    committee: str
    uncertainty: Uncertainty

    @property
    def is_resolvable(self) -> bool:
        return self.uncertainty.is_resolvable

    @property
    def about(self) -> str:
        return self.uncertainty.about


@dataclass(frozen=True, slots=True)
class Deliberation:
    """Why this conclusion prevailed over the one that did not.

    The part a scoring engine could never write. A gate report says
    which thresholds were cleared; it cannot say that two committees
    concurred, or that one dissented and was overruled by a named rule,
    because a score carries no record of a position having been taken.

    Nothing here re-decides. The decision was made before this object
    existed and is unchanged by it: `prevailed` restates the verdict in
    the words of the rule that reached it, and `over` states the
    position that did not carry — preserved, because a conclusion whose
    losing side was discarded can be read but not audited.
    """

    #: How far the committees that spoke pointed the same way, worded.
    agreement: str

    #: The course the decision took, and the rule that took it.
    prevailed: str

    #: The position that did not carry, where one was held. None when
    #: no committee dissented — which is not the same as a case with no
    #: opposition, and is worded rather than left silent.
    over: str | None

    #: Why. Composed only from the counts and the named rules already
    #: recorded above — never an argument this layer invents.
    because: str


@dataclass(frozen=True, slots=True)
class DecisionSynthesis:
    """One decision, stated so it can be argued with.

    Composed after the decision and consumed by nothing. Every field is
    either canonical text carried through unchanged or an absence worded
    where the canonical case holds nothing.
    """

    symbol: str
    state: DecisionState
    conviction: int

    #: The strongest facts arguing for the decision, strongest first.
    because: tuple[SynthesisFact, ...]

    #: Why there are none, where there are none.
    because_absent: str | None

    #: The strongest fact or unresolved uncertainty arguing against it.
    #: Kept short on purpose: an investor challenging a recommendation
    #: needs the one thing most likely to change their mind, not a list.
    despite: tuple[SynthesisFact, ...]
    despite_absent: str | None

    #: Named conditions for reviewing the decision.
    review_if: tuple[ReviewCondition, ...]
    review_if_absent: str | None

    #: What the company's own filing establishes, carried beside the
    #: decision and marked as not having reached it. This is the
    #: distinction the conclusion exists to make plain: the platform
    #: holds audited facts about the business that its analysts, which
    #: read market data, did not consume.
    established: tuple[SynthesisFact, ...]

    #: What is not yet known, carried from the committees' own
    #: uncertainties. Its own part of the conclusion rather than a
    #: footnote to the opposing case, because they are different
    #: claims: a fact against the security is a reason to hesitate, and
    #: something unmeasured is a reason the platform cannot yet say.
    #: Folding the second into the first is how not knowing becomes
    #: bearishness.
    uncertainty: tuple[CommitteeUncertainty, ...] = ()
    uncertainty_absent: str | None = None

    #: Why the conclusion is what it is, given both sides. None only
    #: where no committee spoke at all.
    deliberation: Deliberation | None = None

    @property
    def is_challengeable(self) -> bool:
        """Whether an investor is given something to disagree with.

        The measurable bar this slice set for itself. A conclusion with
        no opposing fact and no condition for review can be read but not
        argued with, and reporting that plainly is the point.
        """

        return bool(self.despite) or bool(self.review_if)

    @property
    def is_deliberated(self) -> bool:
        """Whether the conclusion shows an argument rather than a checklist.

        The bar this slice set for itself, and the one the acceptance
        case is measured against: a synthesis that can name what
        prevailed, over what, and what remains unresolved is an
        investment committee's account of a decision. One that cannot
        is a gate report with better headings.
        """

        return self.deliberation is not None and (
            bool(self.uncertainty) or self.deliberation.over is not None
        )
