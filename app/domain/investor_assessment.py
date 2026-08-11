"""The strongest useful thing this platform can responsibly say.

Between grounded evidence and an investment recommendation there is a
layer this platform did not have, and its absence was leaking. Internal
epistemic vocabulary — `CONFLICTED`, `CLAIMED`, `INSUFFICIENT_EVIDENCE`
— was reaching the surface *as though it were an investment conclusion*,
and it is not one. **`CONFLICTED` is a fact about two readings;
"we cannot tell you anything" is a fact about the investor's question,
and they are different sentences.**

So this layer asks one question of whatever is held:

> What is the strongest useful statement MOVRvest can responsibly make
> from the information available?

**The answer does not have to be binary, and usually is not.** Six
shapes were derived from the live corpus rather than imagined — every
one of them is produced by real evidence across the eight reference
assets, and none of them is a grade:

```text
PRECISE      Bitcoin's maximum supply is 21,000,000
RANGE        Bittensor's circulating supply is 8.6–9.6 million across
             three estimates
STRUCTURAL   Cardano's new supply is created by a rule this platform
             re-ran, changeable by governance without a fork
QUALIFIED    fee capture is evidenced, and the share reaching holders
             is what it is rather than what it should be
UNCERTAIN    Hyperliquid's circulating estimates span 78%, and one of
             them exceeds the maximum supply
```

**A difference between readings is not automatically a failure.** Two
credible estimates 2% apart bound an answer; the useful statement is the
bound, not a complaint. The evidence layer already draws that line —
`Comparison.CORROBORATED`, `COEXIST`, `CONFLICTED` — and this layer
reads it rather than inventing a second opinion about the same numbers.

**And no canonical figure is ever invented.** A range is reported as a
range. Averaging two disagreeing sources into one number nobody
published would be the exact failure this platform exists not to
commit — see `Invariant 1`: absent evidence is reported as absent,
never estimated. A midpoint is a plausible number on an investment
dashboard, which is to say a measurement that was never taken.

**What is deliberately absent**: no score, no rank, no recommendation,
no aggregate, no agreement between committees, and no favourable,
adverse, positive, negative, good or bad. The shapes below are not
ordered — `PRECISE` is not "better" than `UNCERTAIN`, because a precise
answer to a question the investor is not asking is worth less than an
honest bound on one they are.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class StatementShape(StrEnum):
    """What kind of useful thing is being said. **Not a ranking.**

    Six, each observed in the live corpus before it was declared —
    which is why there is no `DIRECTIONAL`. A comparison the evidence
    settles without settling a level ("new issuance currently exceeds
    what is burned") is a legitimate investor statement and nothing here
    can currently produce one: the burn side of Ethereum is held and the
    reward side is not read. It will be added when something produces
    it, and not before.

    The enumeration exists so a surface can render a bound differently
    from a single figure — not so anything can sort them, and there is
    no `rank`, no ordering and no comparison operator.
    """

    #: One figure the evidence settles.
    PRECISE = "precise"

    #: Several credible readings that bound the answer. **The bound is
    #: the statement**; no midpoint is computed.
    RANGE = "range"

    #: How something works, rather than how much of it there is.
    STRUCTURAL = "structural"

    #: True, with a stated limit on how far it goes.
    QUALIFIED = "qualified"

    #: Readings differ in a way that changes what can responsibly be
    #: said. **Reached only when the difference itself is material** —
    #: not merely because two numbers are not identical.
    UNCERTAIN = "uncertain"

    #: Nothing useful can be said yet. The last resort, and a surface
    #: should treat reaching it often as a finding about this platform.
    INSUFFICIENT = "insufficient"

    @property
    def stated(self) -> str:
        return _SHAPES[self]


_SHAPES = {
    StatementShape.PRECISE: "a figure the evidence settles",
    StatementShape.RANGE: "a bound across the available readings",
    StatementShape.STRUCTURAL: "how this works, rather than how much",
    StatementShape.QUALIFIED: "true, within a stated limit",
    StatementShape.UNCERTAIN: "the readings differ in a way that matters",
    StatementShape.INSUFFICIENT: "not enough is held to say anything useful",
}


@dataclass(frozen=True, slots=True)
class ObservedValue:
    """One reading behind a statement, with where it came from.

    Carried in full rather than summarised, which is what keeps
    provenance intact and what lets a range name its sources. **Adding a
    fourth reading changes this tuple and nothing else** — the schema
    does not move because a value differs.
    """

    value: float
    unit: str
    source: str
    observed_at: datetime | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "observed_at": (self.observed_at.isoformat() if self.observed_at else None),
        }


@dataclass(frozen=True, slots=True)
class InvestorStatement:
    """One useful thing, said as strongly as the evidence allows.

    `stated` is what an investor reads. Everything else exists so the
    sentence can be checked: which readings it rests on, what limits it,
    and what is still open.
    """

    #: What this is about, in the investor's terms — "Maximum supply",
    #: "Fee capture". Never an internal metric name.
    subject: str

    shape: StatementShape

    #: The sentence. Built deterministically, never drafted.
    stated: str

    #: What limits it, where something does. A qualification is part of
    #: the statement rather than a footnote on it.
    qualification: str | None = None

    #: What remains open — **carried only when it is material**, because
    #: an uncertainty printed beside every sentence teaches a reader to
    #: skip them all.
    uncertainty: str | None = None

    #: Why an investor should care. Absent rather than padded: not every
    #: true statement has a reason worth a sentence.
    why_it_matters: str | None = None

    #: The readings beneath it, in full.
    observed: tuple[ObservedValue, ...] = ()

    #: Handles back into the layer that established it — a committee
    #: key, an evidence ref. Never empty for a statement that rests on
    #: something checkable.
    refs: tuple[str, ...] = ()

    @property
    def is_useful(self) -> bool:
        """Whether this says anything at all beyond *we do not know*."""

        return self.shape is not StatementShape.INSUFFICIENT

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "shape": self.shape.value,
            "shape_stated": self.shape.stated,
            "stated": self.stated,
            "qualification": self.qualification,
            "uncertainty": self.uncertainty,
            "why_it_matters": self.why_it_matters,
            "observed": [value.as_dict() for value in self.observed],
            "refs": list(self.refs),
        }


@dataclass(frozen=True, slots=True)
class InvestorAssessment:
    """Everything usefully sayable about one asset. A list, not a verdict.

    **No summary of itself.** There is no overall statement, no headline,
    no count that means anything and no ordering by importance —
    deciding which of an investor's questions matters most is the
    recommendation layer, and it does not exist.
    """

    asset: str

    statements: tuple[InvestorStatement, ...] = ()

    #: Questions this platform holds nothing useful about, named rather
    #: than omitted. An investor who cannot see what is missing cannot
    #: tell a thin dossier from a complete one.
    silent_about: tuple[str, ...] = ()

    @property
    def useful(self) -> tuple[InvestorStatement, ...]:
        return tuple(item for item in self.statements if item.is_useful)

    def about(self, subject: str) -> InvestorStatement | None:
        for item in self.statements:
            if item.subject.lower() == subject.lower():
                return item

        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "statements": [item.as_dict() for item in self.statements],
            "silent_about": list(self.silent_about),
        }
