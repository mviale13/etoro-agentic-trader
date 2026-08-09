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

    @property
    def is_challengeable(self) -> bool:
        """Whether an investor is given something to disagree with.

        The measurable bar this slice set for itself. A conclusion with
        no opposing fact and no condition for review can be read but not
        argued with, and reporting that plainly is the point.
        """

        return bool(self.despite) or bool(self.review_if)
