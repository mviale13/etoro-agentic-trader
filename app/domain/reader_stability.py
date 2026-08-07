"""How far independent readings of one unchanged document agree.

The platform's first measurement of itself rather than of a company.

Everything else in this repository treats a reading as a fact once it
has survived grounding, identity and applicability. Those checks prove
that a reading is *supported by the document*. None of them proves it is
the reading the same question would produce again — and it is not
always: NVIDIA's archetype moved from Diversified to Manufacturer with
its sizes unchanged, because a second reading of the same unchanged
prose reported one fewer way of earning for one segment.

That is a different kind of defect from every acquisition failure before
it. Those were the platform reading the wrong thing; this is the
platform reading the same thing twice and getting two answers. The
document is immutable, the rules downstream are a pure function, and the
variance sits entirely in the one layer that asks a model.

So it is measured, and it is measured *before* anything else is improved
— because an improvement smaller than the noise it is measured against
cannot be told from another draw of the same distribution.

Nothing here is called a probability. An agreement observed over ten
readings is exactly that, and stating it as the chance of a future
reading agreeing would be inventing a number nobody measured.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Answer:
    """One distinct answer, and how many readings gave it."""

    stated: str

    given: int


@dataclass(frozen=True, slots=True)
class Agreement:
    """
    How far the readings agreed about one thing, and what they said.

    Every distinct answer is kept, not just the winner. A question
    answered nine ways once each and a question answered two ways five
    times each both agree 10% — and they are entirely different
    findings, one of them a reading that is barely reading at all and
    the other a reading torn between two defensible views.
    """

    #: What was asked of each reading, in words a reader can check.
    question: str

    #: Every distinct answer, most given first. Ties keep the order the
    #: answers were first seen, which is the order the readings ran.
    answers: tuple[Answer, ...]

    @property
    def readings(self) -> int:
        """How many readings answered this at all."""

        return sum(answer.given for answer in self.answers)

    @property
    def modal(self) -> Answer | None:
        """The answer most readings gave, where any did."""

        return self.answers[0] if self.answers else None

    @property
    def agreeing(self) -> int:
        """How many readings gave that answer."""

        return self.answers[0].given if self.answers else 0

    @property
    def stability(self) -> float | None:
        """
        The share of readings that gave the same answer, 0.0 to 1.0.

        None where nothing answered. A question no reading reached is
        not a question answered inconsistently, and averaging the two
        together would report a reading that never happened as a
        disagreement.
        """

        if not self.readings:
            return None

        return self.agreeing / self.readings

    @property
    def settled(self) -> bool:
        """Whether every reading that answered gave the same answer."""

        return len(self.answers) == 1

    def stated(self) -> str:
        """The finding as an investor-facing line."""

        if self.modal is None:
            return f"{self.question}: no reading answered"

        return (
            f"{self.question}: {self.agreeing} of {self.readings} readings "
            f"agreed — {self.modal.stated}"
        )


def agreement(question: str, answers: Iterable[str]) -> Agreement:
    """Count what the readings said, keeping every distinct answer."""

    counted = Counter(answers)

    return Agreement(
        question=question,
        answers=tuple(
            Answer(stated=stated, given=given)
            for stated, given in counted.most_common()
        ),
    )


@dataclass(frozen=True, slots=True)
class SegmentStability:
    """How reproducibly one segment was read.

    Each dimension is counted only over the readings that named this
    segment. A segment three readings out of ten never mentioned has no
    opinion in the other seven to disagree with, and folding those in as
    disagreement would report one instability as three.
    """

    name: str

    #: How many readings named this segment at all, out of how many read
    #: the document successfully. The denominator of everything below.
    named_in: int

    #: Whether a size was measured, and which one.
    size: Agreement

    #: Which ways of earning the filing was shown to describe.
    earning: Agreement

    #: Whether a description survived applicability at all.
    described: Agreement

    #: Which span was cited for it.
    #:
    #: Reported apart from `described`, because they are different
    #: questions with different consequences and only one of them
    #: reaches a decision. Measured on Caterpillar, ten readings cited
    #: the same sentence about Resource Industries eight ways — trimmed
    #: at "quarry", at "quarry and aggregates", with and without the
    #: full stop. As spans that is 2 of 10; as an account of what the
    #: segment does it is 10 of 10, and reporting only the first would
    #: describe a reader that cannot read.
    #:
    #: Neither figure replaces the other. The span is the evidence a
    #: reader checks against the filing, so a platform that stopped
    #: measuring it would stop noticing when two readings quote
    #: genuinely different sentences.
    description: Agreement


@dataclass(frozen=True, slots=True)
class ReaderStability:
    """One document, read repeatedly under identical conditions.

    The document is fetched once and handed to every reading, which is
    not an approximation of reading it repeatedly — a primary source is
    immutable, so one fetch *is* every reading's document. What varies
    is only what this platform asked a model, which is the point.
    """

    symbol: str

    #: The document, stated as an investor would cite it.
    source: str

    #: What did the reading, since the answer is only as reproducible as
    #: whatever produced it.
    reader: str

    #: How many independent readings were run.
    readings: int

    #: How many produced knowledge. A reading refused for want of
    #: grounding is not a failed measurement — it is the measurement,
    #: and the share of readings that get nothing at all is the first
    #: thing a reader of this report needs.
    read: int

    #: Why the rest were refused, one entry per distinct reason.
    refusals: Agreement

    #: The set of segments the document was read as naming.
    identity: Agreement

    segments: tuple[SegmentStability, ...]

    #: What the deterministic rules concluded from each reading. The
    #: rules cannot disagree with themselves, so every difference here
    #: arrived from the layer above.
    archetype: Agreement

    @property
    def completed(self) -> float | None:
        """The share of readings that produced knowledge at all."""

        if not self.readings:
            return None

        return self.read / self.readings
