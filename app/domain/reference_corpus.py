"""The companies every reasoning change must keep passing through.

An engineering designation, not a user-facing concept and not an
investment view. When the platform's first end-to-end chain closed —
filing to authoritative playbook with every link consuming consensus
claims only — the company it closed on became worth keeping: not
because anyone intends to buy it, but because a future change that
breaks any link of that chain should be caught by the company that
first proved the chain works.

Each member is here for a property its filings exercise, named beside
it. The corpus is the set of engineering acceptance cases the platform
has actually earned — a company enters by exercising something real, as
measured, never by being interesting. Membership is reviewed by the
measurements' owner.

These companies are tracked by the coverage measurement under their own
origin so they never blend into the portfolio or a watchlist: the
portfolio KPI cannot move because a reference company improved, and a
surface never presents an acceptance case as something the investor
chose to watch.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceCompany:
    """One engineering acceptance case, and what it exercises."""

    symbol: str

    #: The property this company's filings hold in the corpus — what a
    #: regression here would actually mean.
    exercises: str


REFERENCE_CORPUS: tuple[ReferenceCompany, ...] = (
    ReferenceCompany(
        symbol="JPM",
        exercises=(
            "the complete chain: a diversified financial whose 10-K "
            "points elsewhere for both its descriptions and its tables — "
            "the first company carried from filing to authoritative "
            "playbook with every link grounded"
        ),
    ),
    ReferenceCompany(
        symbol="DIS",
        exercises="a diversified media business, segments as table rows",
    ),
    ReferenceCompany(
        symbol="NVDA",
        exercises="a manufacturer whose archetype rests on one dominant engine",
    ),
    ReferenceCompany(
        symbol="CAT",
        exercises=(
            "difficult tables: an in-table title, and a section once "
            "located by width instead of structure"
        ),
    ),
    ReferenceCompany(
        symbol="VOW3.DE",
        exercises=(
            "the European narrative edge: an ESEF package whose tagged "
            "note prints tables and boilerplate, with the describing "
            "prose in the untagged management report"
        ),
    ),
    ReferenceCompany(
        symbol="META",
        exercises=(
            "the applicability edge: a filing that names its segments "
            "after describing them, and descriptions refused as printed "
            "outside their section"
        ),
    ),
    ReferenceCompany(
        symbol="UMI.BR",
        exercises="an ESEF industrial read in Dutch, grounded to Industrial",
    ),
)


def reference_symbols() -> frozenset[str]:
    """The corpus by symbol, for membership checks."""

    return frozenset(company.symbol for company in REFERENCE_CORPUS)
