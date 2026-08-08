"""Show the figures a filer's own statements settled, and how firmly.

Developer-level inspection, exactly as `movrvest knowledge` is: it
exists so a stored figure can be checked against the filing by hand —
the table, the row, the printed cell, the caption that states the
scale. Every claim carries its width; below quorum the surface serves
what it has, labeled. Nothing here decides anything, and nothing here
derives anything: the figures are the filer's, at addresses this
platform checked.
"""

from __future__ import annotations

from app.domain.agreement import Agreement
from app.domain.financial_statement_consensus import FinancialStatementConsensus
from app.services.financial_statement_service import (
    FinancialStatementService,
    StatementOutcome,
)


class StatementsCommand:
    async def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = await FinancialStatementService().statements(normalized)

        _render(normalized, outcome)

        return 0 if outcome.state.is_available else 1


def _render(symbol: str, outcome: StatementOutcome) -> None:
    print(f"{symbol} — {outcome.state.value}")
    print()

    if outcome.absent_because:
        print(outcome.absent_because)
        print()

    if outcome.statements is None:
        print("No statement has been read for this security.")
        return

    _render_statements(outcome.statements)


def _render_statements(consensus: FinancialStatementConsensus) -> None:
    print(consensus.stated_source())
    print(f"read: {consensus.reading.source}")

    if not consensus.is_quorate:
        print(
            f"  {consensus.observation_count} of the {consensus.quorum} "
            "observations this platform wants before calling anything "
            "settled. Every claim below is what the observations so far "
            "say, at that width."
        )

    print()
    print(consensus.statement.value)

    for fact in consensus.facts:
        print(f"  {fact.concept.value}")

        if fact.anchor is None:
            print("    figure: absent")
            print(f"      because: {fact.unlocated_because or 'not stated'}")
            _agreement("located", fact.agreement, indent="    ")
            continue

        print(f"    figure: {fact.anchor.stated()}")

        for figure in fact.row:
            if figure.cell == fact.anchor.cell:
                continue

            # The rest of the row, read by this platform off the
            # anchored row: prior periods under the filer's own
            # headers, no model claim anywhere in them.
            print(
                f"      also on this row: {figure.printed} under "
                f'"{figure.column_header}" ({figure.cell.stated()})'
            )

        _agreement("located", fact.agreement, indent="    ")


def _agreement(
    named: str,
    measured: Agreement,
    indent: str = "",
) -> None:
    """One claim's width, and its full distribution short of unanimity."""

    if measured.modal is None:
        return

    print(f"{indent}{named}: {measured.agreeing} of {measured.readings} agree")

    if measured.settled:
        return

    for answer in measured.answers:
        print(f"{indent}  {answer.given}× {answer.stated}")


async def run(symbol: str) -> int:
    return await StatementsCommand().run(symbol)
