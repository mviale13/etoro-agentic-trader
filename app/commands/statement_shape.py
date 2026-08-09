"""Show what shape a filer's own statements have, and whose absence each is.

Developer-level inspection, in the family of `movrvest reader-stability`:
a measurement of this platform against one document. It costs a fetch,
asks no model, stores nothing and decides nothing.

What it is for is the question a consensus cannot answer. When
`movrvest statements` reports *gross profit: no figure located*, this
says whether the filer printed no such line, printed one this platform
does not read, or was never located at all.
"""

from __future__ import annotations

from app.domain.statement_shape import DocumentShape, Presence, StatementShape
from app.services.statement_shape_service import ShapeOutcome, StatementShapeService


class StatementShapeCommand:
    def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = StatementShapeService().shape(normalized)

        _render(normalized, outcome)

        return 0 if outcome.shape is not None else 1


def _render(symbol: str, outcome: ShapeOutcome) -> None:
    print(f"{symbol} — statement shape — {outcome.state.value}")
    print()

    if outcome.absent_because:
        print(outcome.absent_because)
        print()

    if outcome.shape is None:
        print("No filing was located for this security, so nothing was measured.")
        return

    _render_shape(outcome.shape)


def _render_shape(shape: DocumentShape) -> None:
    print(shape.source)
    print("measured structurally by this platform — no model was asked")

    for statement in shape.statements:
        print()
        print(statement.name)
        _render_statement(statement)


def _render_statement(statement: StatementShape) -> None:
    if not statement.is_located:
        print(f"  NOT LOCATED — {statement.unlocated_because}")
        return

    print(
        f"  {statement.tables} table(s), {statement.numeric_rows} rows that "
        f"print a figure, located among {statement.contenders}"
    )

    if statement.provenance_uncertain:
        print(
            "  PROVENANCE UNCERTAIN: this filing prints this statement's title "
            f"in {statement.contenders} structural positions, so which section "
            "these rows came from is an interpretation."
        )

    if not statement.is_read:
        print(
            "  NOTHING READ: no concept was located here at all, which is what "
            "a statement this platform failed to read looks like. The absences "
            "below are not evidence about the company."
        )

    for concept in statement.concepts:
        if concept.presence is Presence.PRINTED:
            print(f"  {concept.concept.value:28s} printed as {concept.printed_as!r}")
        elif concept.presence is Presence.NOT_PRINTED:
            print(
                f"  {concept.concept.value:28s} "
                + (
                    "the statement prints no such line"
                    if statement.evidences_absence(concept.concept)
                    else "no such line was found, and nothing here was read"
                )
            )
        elif concept.presence is Presence.UNREAD:
            print(
                f"  {concept.concept.value:28s} UNREAD — the statement prints "
                f"{concept.unread[0]!r}, which this platform does not read as "
                "answering it. This absence is this platform's, not the filer's."
            )
        else:
            print(f"  {concept.concept.value:28s} nothing was located")


def run(symbol: str) -> int:
    return StatementShapeCommand().run(symbol)
