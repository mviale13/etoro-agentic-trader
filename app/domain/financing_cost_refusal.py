"""When a located figure is refused the concept it was read for.

The sibling of `absence_supersession`, and deliberately not part of it.
That module can withdraw an **absence** whose producing vocabulary
provably could not have accepted a label. This one refuses a **positive**
whose semantic role the statement's own structure disproves. The two run
in opposite directions and would be unreadable folded together: one asks
*could this reader have seen it*, the other asks *is this the quantity the
concept names*.

## The measurement that earned it

Three filers print the same construction — non-interest revenues plus net
interest income — under three different labels, and all three reconcile
exactly:

```text
GS   Total non-interest revenues 44,724 + Net interest income 13,559 =  58,283
JPM  Noninterest revenue         87,004 + Net interest income 95,443 = 182,447
AXP  Total non-interest revenues 54,865 + Net interest income 17,364 =  72,229
```

Goldman's and JPMorgan's labels are in `CONCEPT_LABELS[TOTAL_REVENUE]`
and American Express's is not, so two of the three answered the concept
and one did not. Nothing economic separates them. The two accepted forms
came from the founding vocabulary, written before any semantic standard
existed; the standard arrived later and is stated in the same file — *an
addition of revenue components with no expense deducted, which is what
makes it a gross top line rather than a net one*. It was never applied
backwards, so no decision about Goldman's label was ever made
(`docs/architecture/REVENUE_NET_OF_INTEREST.md`).

## The rule

> **`TOTAL_REVENUE` is gross revenue before financing cost.** A located
> figure does not answer it where the same statement prints a net
> interest income subtotal in the same column of the same table, on an
> earlier row. Such a figure is a measure net of financing cost — a
> different economic quantity — and belongs to a concept this platform
> has not yet named.

**It reads no words.** Not the label, not the word *net*, not a company
name, and there is no list of companies anywhere in it. Eleven of the
thirteen top lines the corpus establishes carry no financing cost above
them and are untouched; three of those eleven print *net* in the label,
because `Net sales` is net of returns and allowances, which is a revenue
adjustment and not an expense line.

**One table and one column**, borrowed verbatim from `comparable`: one
table is one scale and one column is one period. A subtotal in another
table is not known to feed this total, and a subtotal in another column
is a different year's. Where the structure cannot be established the
figure keeps its concept — the same direction `absence_supersession`
takes when a contract cannot be bounded.

## What it does not do

It changes no stored byte. The observation still holds the cell it read,
still says exactly what it said, still carries its own provenance. What
is lost is the figure's authority to answer one concept of one statement,
derived on every read and written nowhere. And the refusal is **carried
rather than erased**: a refused figure is reported with the reason and
the label, because *the filer printed no such line* would be a false
claim about a filer that printed one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_statements import StatementConcept
from app.domain.tabular_evidence import ReportedFigure


class RefusalStanding(StrEnum):
    """Why a located figure does not answer the concept it was read for."""

    #: The statement prints a net interest income subtotal above this
    #: figure, in the same column of the same table, so the figure is a
    #: total after financing cost rather than a gross top line.
    NET_OF_FINANCING_COST = "constructed from net interest income"


#: Which concept each refusal governs, and which concept's presence
#: disproves it. Declared as a pair rather than coded into a branch, so
#: that adding a second structural refusal cannot quietly widen this one.
#:
#: One entry. `TOTAL_REVENUE` is the only concept whose contract states a
#: gross reading, and `NET_INTEREST_INCOME` is the only concept that
#: positively evidences a financing cost already deducted. Neither half
#: generalises: a premium revenue line says nothing about financing, and
#: net income is net of everything by definition.
GOVERNED: dict[StatementConcept, StatementConcept] = {
    StatementConcept.TOTAL_REVENUE: StatementConcept.NET_INTEREST_INCOME,
}


@dataclass(frozen=True, slots=True)
class FactRefusal:
    """A figure the filer printed, and the concept it may not answer.

    Carries the figure rather than discarding it. A consensus that
    reported only *no figure located* here would be making a false claim
    about the document — Goldman prints `Total net revenues` and prints
    58,283 in it — and an investor comparing two companies is owed the
    difference between a filer that printed nothing and a platform that
    declined what was printed.
    """

    concept: StatementConcept

    standing: RefusalStanding

    #: The refused figure, verbatim as the reading checked it.
    figure: ReportedFigure

    #: Its row, carried with it exactly as a located fact would carry it.
    row: tuple[ReportedFigure, ...]

    #: The figure whose presence disproved the concept.
    disproved_by: ReportedFigure

    because: str


def refusal_for(
    concept: StatementConcept,
    figure: ReportedFigure | None,
    row: tuple[ReportedFigure, ...],
    established: dict[StatementConcept, ReportedFigure],
) -> FactRefusal | None:
    """Whether this located figure is refused the concept it was read for.

    `established` is the statement's other settled figures, by concept —
    the evidence the refusal is drawn from, passed in rather than looked
    up so that this function reads one statement and cannot reach a
    store, a document or a company.

    Returns `None` for every concept this rule does not govern, for an
    absent figure, and wherever the structure is not established. Total
    and deterministic.
    """

    if figure is None:
        return None

    disproving = GOVERNED.get(concept)

    if disproving is None:
        return None

    marker = established.get(disproving)

    if marker is None or not precedes_in_one_column(marker, figure):
        return None

    return FactRefusal(
        concept=concept,
        standing=RefusalStanding.NET_OF_FINANCING_COST,
        figure=figure,
        row=row,
        disproved_by=marker,
        because=(
            f'The statement prints "{marker.label}" {marker.printed} at '
            f"{marker.cell.stated()}, above "
            f'"{figure.label}" {figure.printed} at {figure.cell.stated()} '
            f'and in the same column ("{figure.column_header}"). So the '
            f"figure is a total after financing cost, not the gross "
            f"{concept.value} this concept names, and it is a different "
            "economic quantity. The filer did print it, and this platform "
            "holds no concept for it yet."
        ),
    )


def precedes_in_one_column(
    marker: ReportedFigure,
    candidate: ReportedFigure,
) -> bool:
    """Whether the marker is printed above the candidate, comparably.

    One table, one column, earlier row — `comparable`'s discipline plus
    an order. Stated positively so that anything it cannot establish
    leaves the candidate alone.
    """

    here, there = marker.cell, candidate.cell

    return (
        here.table == there.table
        and here.column == there.column
        and here.row < there.row
    )
