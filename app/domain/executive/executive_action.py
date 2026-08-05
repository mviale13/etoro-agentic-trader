"""What the Artificial CIO is asking the investor to consider."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ActionKind(StrEnum):
    """
    The kind of thing being asked, apart from the words asking it.

    A surface needs to style "consider opening a position" differently
    from "nothing to do", and it must not do that by reading the sentence.
    """

    OPEN = "open"
    ADD = "add"
    HOLD = "hold"
    REDUCE = "reduce"
    RESEARCH = "research"
    WAIT = "wait"
    WATCH = "watch"
    NONE = "none"

    @property
    def asks_for_something(self) -> bool:
        """Whether this puts a decision in front of the investor."""

        return self in (
            ActionKind.OPEN,
            ActionKind.ADD,
            ActionKind.REDUCE,
            ActionKind.RESEARCH,
        )


@dataclass(frozen=True, slots=True)
class ExecutiveAction:
    """
    One thing to consider about one security, and why.

    Deliberately not the recommendation. Every case on the dashboard was
    labelled "Monitor" — including the ones the Artificial CIO had moved
    to RECOMMEND — because the action was being read off nothing at all.
    A decision state says where the case stands; what to do about it also
    depends on whether the investor already owns the security, which the
    state cannot know.

    It is a consideration, never an instruction. MOVRvest recommends and
    the investor decides, so nothing here is worded as a command and no
    size, price or quantity is ever suggested.
    """

    kind: ActionKind

    #: What to consider, in one line.
    statement: str

    #: The Artificial CIO's own reason, carried rather than rewritten.
    because: str

    #: The next dated thing that bears on this case — a report the company
    #: has published a date for. None where nothing is scheduled, which is
    #: not the same as nothing being expected.
    checkpoint: str | None = None
