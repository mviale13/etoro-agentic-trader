"""Take statement observations of a company's current document up to a count.

The statement stream's explicit spend, exactly as `observe` is the
segment stream's: invoking it is the request to pay for the readings.
The stopping rule references only the count — the quorum by default, or
a deeper target stated up front — never what any observation says. An
entry stops at its target whether its claims settled or not, and an
unsettled consensus at the target is a finding, not a failure to keep
asking.
"""

from __future__ import annotations

from app.commands.statements import _render
from app.domain.financial_statements import StatementKind
from app.services.financial_statement_service import FinancialStatementService


class ObserveStatementsCommand:
    async def run(
        self,
        symbol: str,
        to: int | None = None,
        statement: StatementKind = StatementKind.INCOME_STATEMENT,
    ) -> int:
        normalized = symbol.upper().strip()

        service = FinancialStatementService()

        outcome = await (
            service.observe(normalized, statement)
            if to is None
            else service.observe(normalized, statement, target=to)
        )

        _render(normalized, outcome, statement)

        return 0 if outcome.statements is not None else 1


async def run(
    symbol: str,
    to: int | None = None,
    statement: StatementKind = StatementKind.INCOME_STATEMENT,
) -> int:
    return await ObserveStatementsCommand().run(symbol, to, statement)
