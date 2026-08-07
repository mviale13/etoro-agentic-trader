"""Every absent claim in the store, classified by structural cause.

The measurement that decides whether reader work is earned. Individual
failures earn backlog entries; a measured pattern — several companies
blocked by the *same* structural cause — earns an engineering slice.
This module is the arithmetic that tells one from the other.

Nothing here diagnoses, guesses or reads. Every absent claim in the
knowledge layer already carries its reason, worded by the code path
that refused it; classification is matching those reasons back to the
templates that produced them. A reason no template explains lands in
OTHER with its wording carried verbatim — an unclassified defect is a
finding too, not a rounding error.

What the store cannot show, this taxonomy cannot count: a reading the
grounding contract refused outright stores nothing, so total refusals
(ETOR's class) are visible only at the moment of refusal and live on
the reader watchlist in `MIGRATION_PLAN.md`. The surface states this
limit rather than presenting store-visible counts as the whole truth.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum


class Claim(StrEnum):
    """Which claim about a segment the defect blocked."""

    SEGMENTS = "which segments exist"
    DESCRIPTION = "way of earning"
    SIZE = "size"


class DefectCause(StrEnum):
    """The structural causes the knowledge layer's own reasons name.

    One member per reason template. Matching is by each template's
    invariant phrase, so a new refusal wording in the knowledge layer
    lands in OTHER until it is named here — loudly, not silently.
    """

    #: The reader returned no describing words for the segment.
    NEVER_ARRIVED = "description never arrived"

    #: The description quoted real words printed under another
    #: section, and applicability refused the ownership.
    MISAPPLIED = "description rejected by applicability"

    #: The description quoted words the document does not print.
    UNGROUNDED = "description quotes words not in the document"

    #: A description was established and names no way of earning.
    NAMES_NO_EARNING = "description names no way of earning"

    #: The observations disagree; no answer carries a strict majority.
    UNSETTLED = "observations disagree"

    #: The document is a pointer — its discussion prints no table the
    #: figures could be proven against.
    POINTER_DOCUMENT = "document points elsewhere for its tables"

    #: Tables exist and no cell reporting this figure was located.
    CELL_NOT_LOCATED = "no table cell located for the figure"

    #: A reason no template above explains. Carried verbatim.
    OTHER = "other"


#: Invariant phrase → cause, checked in order. UNSETTLED first: a
#: consensus disagreement wording may embed observation wordings
#: beneath it, and the disagreement is the operative fact. MISAPPLIED
#: before UNGROUNDED: an applicability refusal quotes real words, and
#: its wording must not fall through to the weaker class.
_TEMPLATES: tuple[tuple[str, DefectCause], ...] = (
    ("unsettled across", DefectCause.UNSETTLED),
    ("outside the section it heads", DefectCause.MISAPPLIED),
    ("prints under", DefectCause.MISAPPLIED),
    ("arrived with no words at all", DefectCause.NEVER_ARRIVED),
    ("quotes words that are not in the document", DefectCause.UNGROUNDED),
    ("names no way of earning", DefectCause.NAMES_NO_EARNING),
    ("prints no table", DefectCause.POINTER_DOCUMENT),
    ("located no cell", DefectCause.CELL_NOT_LOCATED),
)


def cause_of(reason: str) -> DefectCause:
    """The structural cause a stored reason names, or OTHER."""

    for phrase, cause in _TEMPLATES:
        if phrase in reason:
            return cause

    return DefectCause.OTHER


@dataclass(frozen=True, slots=True)
class ReaderDefect:
    """One absent claim, one company, one classified cause."""

    symbol: str

    #: The segment the claim was about, or the company-level frame
    #: where the observations could not agree what the segments are.
    segment: str

    claim: Claim
    cause: DefectCause

    #: The knowledge layer's reason, verbatim. The classification can
    #: always be checked against it.
    because: str

    #: How wide the consensus behind the reason is.
    width: int


@dataclass(frozen=True, slots=True)
class CauseCount:
    """One structural cause, and how far it reaches."""

    cause: DefectCause
    companies: int
    claims: int
    symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DefectTaxonomy:
    """The store's absent claims, counted by structural cause."""

    #: Every company scanned, defective or not — the denominator.
    scanned: tuple[str, ...]

    defects: tuple[ReaderDefect, ...]

    @property
    def by_cause(self) -> tuple[CauseCount, ...]:
        """Causes by reach: companies first, then claims."""

        naming: dict[DefectCause, set[str]] = defaultdict(set)
        claims: dict[DefectCause, int] = defaultdict(int)

        for defect in self.defects:
            naming[defect.cause].add(defect.symbol)
            claims[defect.cause] += 1

        return tuple(
            sorted(
                (
                    CauseCount(
                        cause=cause,
                        companies=len(symbols),
                        claims=claims[cause],
                        symbols=tuple(sorted(symbols)),
                    )
                    for cause, symbols in naming.items()
                ),
                key=lambda count: (-count.companies, -count.claims, count.cause.value),
            )
        )

    @property
    def affected(self) -> tuple[str, ...]:
        """Every company carrying at least one defect."""

        return tuple(sorted({defect.symbol for defect in self.defects}))

    def earned(self, threshold: int = 2) -> tuple[CauseCount, ...]:
        """The causes whose reach meets the pattern threshold.

        The rule the taxonomy exists to apply: a cause blocking this
        many companies is a measured pattern and earns an engineering
        slice; anything narrower stays a backlog entry. UNSETTLED is
        never returned — disagreement is reader noise the consensus
        architecture already absorbs, not a defect to engineer away.
        """

        return tuple(
            count
            for count in self.by_cause
            if count.companies >= threshold and count.cause is not DefectCause.UNSETTLED
        )
