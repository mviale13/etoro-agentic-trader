"""Which stored statement readings the filing itself refutes.

The operator-invoked half of targeted supersession. BQ14 measured that
`STATEMENT_SCHEMA_VERSION` cannot separate the two parses that share
version 3 — the header repair and the version bump were the same commit,
and the corpus was written inside it — so 325 of 400 stored anchors are
identical to what today's parse produces and 75 are not. A version bump
would discard all four hundred.

This asks the narrower question instead, one reading at a time:

> **Could this stored reading have been produced, correctly, by today's
> parse of the same immutable document?**

Where the answer is provably no, the reading loses its vote. Where it is
yes, or where the audit cannot tell, the reading keeps it.

## What this may look at, and what it may not

Every verdict terminates in a printed cell: the label the filer typeset
on that row, the figure printed in that column, the header above it, and
how many headed cells the row carries. Nothing here reads a margin, a
growth rate, a factor, a score, a band, a verdict or a recommendation,
and nothing here knows which company it is looking at.

That is the whole safeguard against the failure mode this replaces.
Superseding a reading *because the answer improves* would be evidence
selection with extra steps — so the rule is written to be incapable of
it, and `tests/test_statement_audit.py` greps this module's own source
for every analytical name it must never contain.

The proof that it worked is that the same rule promotes ALL to HIGH,
demotes TSLA and WMT to LOW, and names no company anywhere.

## Why absences are not audited here

A stored *absence* — "no cell was located for this concept" — is a claim
about the reading, not about the document, and the document cannot refute
it. The tempting rule is that today's `CONCEPT_LABELS` admits a
figure-bearing row the reading recorded absent, so the reading must be
wrong. It is not safe: it would let the parser decide which row answers a
concept, which is exactly the authority BQ7 kept out of the parser, and
it fires on ordinary reader fallibility — the thing the quorum exists to
absorb. Measured on the live corpus in `TARGETED_STATEMENT_SUPERSESSION.md`;
declined, with the consequence stated rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementKind,
    statement_tables,
)
from app.domain.primary_source import SourceDocument
from app.domain.tabular_evidence import SourceTable, row_figures


class AuditVerdict(StrEnum):
    """What re-examining the source says about one stored reading."""

    #: Today's parse yields the same anchors and the same rows. The
    #: reading is exactly what a reading taken now would be.
    ACTIVE = "active"

    #: The figures are the filer's own, and the provenance around them is
    #: not: the period header the reading stored is not the header the
    #: filer printed above that cell, or the row carries cells the
    #: reading never captured. Numerically correct, evidentially
    #: incomplete.
    STALE_PROVENANCE = "stale_provenance"

    #: The document does not support the stored claim at the stored
    #: address: the row is gone, names something else, or no longer
    #: carries the figure the reading anchored on.
    INVALID_EXTRACTION = "invalid_extraction"

    #: Not enough could be established to remove authority — the
    #: statement or the table could not be located today, or the reading
    #: located nothing to check. Authority is kept.
    UNDECIDABLE = "undecidable"

    @property
    def supersedes(self) -> bool:
        """Whether this verdict removes a reading's vote."""

        return self in {
            AuditVerdict.STALE_PROVENANCE,
            AuditVerdict.INVALID_EXTRACTION,
        }


#: Worst-first. A reading with one refuted anchor is refuted whether or
#: not its other anchors survive — a proven defect outranks an
#: undecidable, and an undecidable outranks a clean one so that
#: uncertainty is visible rather than averaged away.
_SEVERITY: tuple[AuditVerdict, ...] = (
    AuditVerdict.INVALID_EXTRACTION,
    AuditVerdict.STALE_PROVENANCE,
    AuditVerdict.UNDECIDABLE,
    AuditVerdict.ACTIVE,
)


@dataclass(frozen=True, slots=True)
class AnchorRuling:
    """One stored anchor, re-examined against the filing."""

    concept: str
    verdict: AuditVerdict

    #: The disagreement in printed terms, or nothing where there is none.
    because: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationRuling:
    """One stored reading's verdict, and the anchors that reached it."""

    symbol: str
    key: str
    statement: StatementKind

    #: Position in the entry's own observation list — the address
    #: `supersede` takes, stable because the store only ever appends.
    position: int

    verdict: AuditVerdict
    anchors: tuple[AnchorRuling, ...]

    @property
    def supersedes(self) -> bool:
        return self.verdict.supersedes

    def because(self) -> str:
        """Why this reading loses authority, in the filing's own terms."""

        refuted = [
            anchor
            for anchor in self.anchors
            if anchor.verdict.supersedes and anchor.because
        ]

        return "; ".join(anchor.because or "" for anchor in refuted)


def audit_observation(
    observation: FinancialStatementObservation,
    document: SourceDocument,
    symbol: str,
    key: str,
    position: int,
) -> ObservationRuling:
    """Re-examine one stored reading against the document it was read from."""

    tables = statement_tables(document, observation.statement)

    anchors = tuple(
        _anchor_ruling(fact, tables)
        for fact in observation.facts
        if fact.anchor is not None
    )

    if not anchors:
        # The reading located nothing, so there is no printed cell to
        # check it against. An absence is a claim about the reading and
        # the document cannot refute it.
        verdict = AuditVerdict.UNDECIDABLE
    else:
        verdict = next(
            level
            for level in _SEVERITY
            if any(anchor.verdict is level for anchor in anchors)
        )

    return ObservationRuling(
        symbol=symbol,
        key=key,
        statement=observation.statement,
        position=position,
        verdict=verdict,
        anchors=anchors,
    )


def _anchor_ruling(fact, tables: tuple[SourceTable, ...]) -> AnchorRuling:  # type: ignore[no-untyped-def]
    """One anchor against the same cell of the same table, parsed today."""

    anchor = fact.anchor
    concept = fact.concept.value

    if not 0 <= anchor.cell.table < len(tables):
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.UNDECIDABLE,
            because=(
                f"{concept}: table {anchor.cell.table} is not among the "
                f"{len(tables)} this statement locates today, so nothing "
                "can be checked against it"
            ),
        )

    table = tables[anchor.cell.table]

    # From here on the asymmetry is deliberate and is the whole safety
    # property: **only what today's parse can positively read may refute
    # a reading.** Where the parse produces nothing at the address —
    # because the parse itself has moved, or because it cannot head that
    # table's columns — the audit has not found a contradiction, it has
    # failed to look. Honeywell is the case that forced this: its rows
    # and labels are exactly where the reading said, its figures are the
    # filer's, and today's header detection reads that table so poorly
    # that every column comes back unheaded. Calling that a refutation
    # would withdraw good evidence because *this platform* regressed.

    if not 0 <= anchor.cell.row < len(table.rows):
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.UNDECIDABLE,
            because=(
                f"{concept}: the filing's table {anchor.cell.table} parses "
                f"today as {len(table.rows)} rows and the reading cited row "
                f"{anchor.cell.row}, so its row cannot be found to check"
            ),
        )

    printed_label = table.rows[anchor.cell.row].label.strip()

    if printed_label != anchor.label.strip():
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.UNDECIDABLE,
            because=(
                f"{concept}: today's parse puts {printed_label!r} at "
                f"{anchor.cell.stated()} where the reading recorded "
                f"{anchor.label!r}, so this is not the same row and the "
                "reading's own row cannot be checked"
            ),
        )

    printed = row_figures(table, anchor.cell.row)
    at_cell = [figure for figure in printed if figure.cell.column == anchor.cell.column]

    if not at_cell:
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.UNDECIDABLE,
            because=(
                f"{concept}: today's parse heads no column at "
                f"{anchor.cell.stated()}, so the cell the reading "
                "recorded cannot be read back"
            ),
        )

    if at_cell[0].printed != anchor.printed:
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.INVALID_EXTRACTION,
            because=(
                f"{concept}: the filing prints {at_cell[0].printed} on "
                f"{anchor.label!r} at {anchor.cell.stated()} and the "
                f"reading recorded {anchor.printed}"
            ),
        )

    if at_cell[0].column_header != anchor.column_header:
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.STALE_PROVENANCE,
            because=(
                f"{concept}: the filer heads {anchor.printed} with "
                f"{at_cell[0].column_header!r} and the reading recorded "
                f"{anchor.column_header!r}"
            ),
        )

    if len(printed) > len(fact.row):
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.STALE_PROVENANCE,
            because=(
                f"{concept}: the filer prints {len(printed)} headed "
                f"cells on {anchor.label!r} and the reading captured "
                f"{len(fact.row)}"
            ),
        )

    if len(printed) < len(fact.row):
        # The reading holds cells today's parse cannot reproduce. That is
        # this platform reading less than it once did, not the filing
        # contradicting the reading.
        return AnchorRuling(
            concept=concept,
            verdict=AuditVerdict.UNDECIDABLE,
            because=(
                f"{concept}: the reading captured {len(fact.row)} headed "
                f"cells on {anchor.label!r} and today's parse finds "
                f"{len(printed)}, so the reading cannot be checked whole"
            ),
        )

    return AnchorRuling(concept=concept, verdict=AuditVerdict.ACTIVE)
