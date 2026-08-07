"""How far independent answers to one question agree, and what they were.

The platform's one vocabulary for reproducibility, shared by the two
places that speak it: the calibration instrument, which measures how far
readings of a document agree and stores nothing, and the knowledge
consensus, which decides whether stored observations agree far enough to
support interpretation. One concept, one implementation — a stability
figure that meant something different on each surface would be the
duplication this platform removes elsewhere.

Nothing here is a probability. An agreement of 6 over 10 counts
something that happened; the chance that an eleventh answer agrees was
not measured and is not stated.
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

    @property
    def by_majority(self) -> bool:
        """Whether the modal answer carries a strict majority.

        The consensus rule, kept here beside the arithmetic it reads.
        Content-blind by construction: it counts who agreed and never
        looks at what they agreed on, so a worded absence wins it
        exactly as a measured value does.

        A majority is a fact about *these* answers, never a forecast.
        Measured on NVIDIA: a claim that leaned one way over ten
        readings settled the other way over a five-observation quorum,
        and both majorities were real. Whether a majority would survive
        further observations — robustness — is a different property,
        and this platform has not established it for anything. That is
        why the count travels with every majority: 3 of 5 and 5 of 5
        are different findings, and a consumer that treated them as
        equally firm would be reading a forecast nobody made.
        """

        return self.readings > 0 and self.agreeing * 2 > self.readings

    @property
    def is_narrow(self) -> bool:
        """Whether this is the smallest strict majority the count allows.

        The weakest kind of settled: one changed answer would unsettle
        it. Worded rather than banded — there is no scale here, only
        the observation that 3 of 5 sits at the edge and 5 of 5 does
        not.
        """

        return self.by_majority and self.agreeing == self.readings // 2 + 1

    def counted(self) -> str:
        """The width as a surface shows it: '3/5'."""

        return f"{self.agreeing}/{self.readings}"

    def stated_majority(self) -> str:
        """The strength of the winning count, always with the count.

        Never without the numbers: "narrow" is a reading of 3/5, and
        printed alone it would be an interpretation wearing the
        authority of a measurement.
        """

        if self.settled:
            return f"unanimous ({self.counted()})"

        if self.is_narrow:
            return f"a narrow majority ({self.counted()})"

        if self.by_majority:
            return f"a majority ({self.counted()})"

        return f"no majority ({self.counted()})"

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
