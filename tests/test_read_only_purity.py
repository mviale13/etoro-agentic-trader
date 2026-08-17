"""A surface that says it never observes must be unable to, not merely asked not to.

BQ15's incident, pinned so it cannot recur: `movrvest financials` was
documented *"Read-only and free … never observes"* and one run of it
read a filing with a paid model and fetched the broker's watchlist,
because its playbook-selection dependency reached the acquiring
`knowledge()` door and the watchlist fallback. The contract lived in a
docstring; the dependency graph disagreed; the graph won.

Two kinds of pin, and both are needed:

- **structural** — the read-only modules' own syntax trees never name an
  acquiring door, so a future import of one fails here before it runs;
- **behavioural** — the command completes with every acquiring door
  booby-trapped to raise, credentials present, and evidence both missing
  and present. Credentials are set deliberately: the boundary must hold
  because acquisition is unreachable, never because a key was absent.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
from pathlib import Path

import pytest

from app.commands import financials as financials_module
from app.commands.financials import FinancialsCommand
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services import stored_playbook_selection as selection_module
from app.services.stored_playbook_selection import StoredPlaybookSelection
from tests.test_financial_statement_service import observation

#: The doors through which this platform acquires: filings, readings,
#: broker payloads, provider profiles. A read-only module that names one
#: of these has stopped being read-only, whatever its docstring says.
ACQUIRING_ATTRIBUTES = frozenset(
    {
        "knowledge",  # CompanyKnowledgeService's acquiring door
        "statements",  # FinancialStatementService's acquiring door
        "observe",  # both observation spends
        "select",  # the two-route selector (watchlist + knowledge)
        "fetch",  # provider document/broker fetches
        "find_symbol",  # the watchlist lookup that fetches
        "extract",  # the model extractors
        "resolve",  # the primary-source resolver
    }
)

ACQUIRING_MODULES = frozenset(
    {
        "app.services.playbook_selection_service",
        "app.services.watchlist_service",
        "app.services.company_facts_service",
        "app.providers.primary_source_provider",
        "app.brokers.etoro_client",
        "app.brokers.etoro_watchlist",
        "app.services.company_knowledge_reader",
    }
)


def _syntax(module) -> ast.Module:  # type: ignore[no-untyped-def]
    return ast.parse(inspect.getsource(module))


def _called_attributes(module) -> set[str]:  # type: ignore[no-untyped-def]
    """Every method name the module *calls*, not every field it reads.

    `outcome.knowledge` is a field on a result object and legitimate
    everywhere; `service.knowledge(...)` is the acquiring door. The
    boundary is about invocation, so the walk keeps only attributes in
    call position.
    """

    return {
        node.func.attr
        for node in ast.walk(_syntax(module))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def _imports(module) -> set[str]:  # type: ignore[no-untyped-def]
    names: set[str] = set()

    for node in ast.walk(_syntax(module)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)

    return names


# ── structural: the graph itself refuses ────────────────────────────


def test_the_stored_selection_names_no_acquiring_door() -> None:
    used = _called_attributes(selection_module)

    # `established` is the one knowledge door a read surface may open.
    assert "established" in used
    assert not used & ACQUIRING_ATTRIBUTES, sorted(used & ACQUIRING_ATTRIBUTES)


def test_the_stored_selection_imports_no_acquiring_module() -> None:
    reached = _imports(selection_module) & ACQUIRING_MODULES

    assert not reached, sorted(reached)


def test_financials_names_no_acquiring_door() -> None:
    used = _called_attributes(financials_module)

    assert not used & ACQUIRING_ATTRIBUTES, sorted(used & ACQUIRING_ATTRIBUTES)


def test_financials_imports_no_acquiring_module() -> None:
    reached = _imports(financials_module) & ACQUIRING_MODULES

    assert not reached, sorted(reached)


# ── behavioural: booby-trapped doors, credentials present ───────────


@pytest.fixture
def armed_and_trapped(monkeypatch, tmp_path: Path):
    """Every acquiring door raises; credentials exist; evidence root is clean.

    The trap distinguishes the two failure modes this test exists to
    tell apart: a surface that *asks* politely and is refused by a
    missing key would pass a credential check and still be defective.
    Here the keys are present and the doors themselves are armed.
    """

    monkeypatch.setenv("OPENAI_API_KEY", "sk-present-and-must-not-matter")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-present-and-must-not-matter")
    monkeypatch.setenv("ETORO_API_KEY", "present-and-must-not-matter")

    def trap(name: str):
        def _sprung(*args, **kwargs):
            raise AssertionError(f"read-only surface reached {name}")

        return _sprung

    from app.brokers.etoro_client import EtoroClient
    from app.providers.primary_source_provider import PrimarySourceResolver
    from app.services.company_knowledge_service import CompanyKnowledgeService
    from app.services.financial_statement_service import FinancialStatementService
    from app.services.watchlist_service import WatchlistService

    monkeypatch.setattr(
        CompanyKnowledgeService, "knowledge", trap("CompanyKnowledgeService.knowledge")
    )
    monkeypatch.setattr(
        FinancialStatementService,
        "statements",
        trap("FinancialStatementService.statements"),
    )
    monkeypatch.setattr(
        FinancialStatementService, "observe", trap("FinancialStatementService.observe")
    )
    monkeypatch.setattr(WatchlistService, "get", trap("WatchlistService.get"))
    monkeypatch.setattr(
        WatchlistService, "find_symbol", trap("WatchlistService.find_symbol")
    )
    monkeypatch.setattr(EtoroClient, "get", trap("EtoroClient.get"))
    monkeypatch.setattr(
        PrimarySourceResolver, "resolve", trap("PrimarySourceResolver.resolve")
    )

    return tmp_path


def test_financials_completes_with_no_evidence_and_every_door_armed(
    armed_and_trapped: Path, capsys
) -> None:
    """Missing evidence renders as absence; nothing falls back to acquiring."""

    command = FinancialsCommand(
        store=JsonFinancialStatementStore(armed_and_trapped / "statements")
    )

    exit_code = asyncio.run(command.run("JPM"))

    printed = capsys.readouterr().out

    assert exit_code == 1
    assert "no statement has been read" in printed


def test_financials_completes_with_evidence_and_every_door_armed(
    armed_and_trapped: Path, capsys
) -> None:
    """The full render — measures, model selection, answers — spends nothing."""

    store = JsonFinancialStatementStore(armed_and_trapped / "statements")

    for _ in range(5):
        store.append(observation())

    command = FinancialsCommand(store=store)

    exit_code = asyncio.run(command.run("JPM"))

    printed = capsys.readouterr().out

    assert exit_code == 0
    assert "financial interpretation model: generic" in printed
    assert "acquires nothing" in printed


def test_the_stored_selection_survives_an_empty_store(armed_and_trapped: Path) -> None:
    selection = StoredPlaybookSelection()

    governing = selection.governing("JPM")

    assert governing.model.value == "generic"
    assert "acquires nothing" in governing.because
