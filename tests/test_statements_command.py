"""`movrvest statements` shows every figure with its width, and absences apart."""

import asyncio

import pytest

from app.commands import statements as command
from app.domain.financial_statement_consensus import statement_consensus_of
from app.services.company_knowledge_service import KnowledgeState
from app.services.financial_statement_service import StatementOutcome
from tests.test_financial_statement_consensus import (
    absent_fact,
    located_fact,
    observation,
)


class ServiceStub:
    def __init__(self, outcome: StatementOutcome) -> None:
        self._outcome = outcome

    async def statements(self, symbol: str) -> StatementOutcome:
        return self._outcome


@pytest.fixture
def _no_reading(monkeypatch: pytest.MonkeyPatch):
    """Nothing here fetches a filing or calls a model."""

    def install(outcome: StatementOutcome) -> None:
        monkeypatch.setattr(
            command, "FinancialStatementService", lambda: ServiceStub(outcome)
        )

    return install


def test_a_security_with_no_statement_read_is_told_so(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _no_reading(
        StatementOutcome(
            state=KnowledgeState.UNAVAILABLE,
            absent_because="No provider holds an annual report for ACME.",
        )
    )

    exit_code = asyncio.run(command.run("acme"))
    printed = capsys.readouterr().out

    assert exit_code == 1
    assert "No provider holds an annual report" in printed
    assert "No statement has been read" in printed


def test_a_settled_figure_prints_its_cell_and_its_width(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    consensus = statement_consensus_of(
        tuple(observation(located_fact()) for _ in range(5))
    )

    _no_reading(
        StatementOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            statements=consensus,
        )
    )

    exit_code = asyncio.run(command.run("JPM"))
    printed = capsys.readouterr().out

    assert exit_code == 0
    assert "total_revenue" in printed
    assert "177,419" in printed
    assert "table 0, row 1, column 1" in printed
    assert "5 of 5 agree" in printed


def test_an_absent_figure_prints_its_reason_and_the_distribution(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    consensus = statement_consensus_of(
        (
            observation(absent_fact()),
            observation(absent_fact()),
            observation(located_fact()),
        )
    )

    _no_reading(
        StatementOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            statements=consensus,
        )
    )

    asyncio.run(command.run("JPM"))
    printed = capsys.readouterr().out

    assert "figure: absent" in printed
    assert "located no cell" in printed
    # Short of unanimity, the full distribution prints.
    assert "2×" in printed and "1×" in printed


def test_below_quorum_the_width_is_stated_up_front(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    consensus = statement_consensus_of((observation(located_fact()),))

    _no_reading(
        StatementOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            statements=consensus,
        )
    )

    asyncio.run(command.run("JPM"))
    printed = capsys.readouterr().out

    assert "1 of the 5 observations" in printed
