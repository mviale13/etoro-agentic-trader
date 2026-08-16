"""The statement store obeys the evidence root, like every other store.

BQ9 Part A. #118 made the evidence root a declared input and converted
the caches; the four *repositories* kept their string literals, and
`JsonFinancialStatementStore` was the one that mattered — it holds the
statement corpus every grounded-quality answer rests on, so a test
constructing it with no argument read the developer's real evidence,
and BQ8's funded experiment needed an explicit path to stay hermetic.

The property under test is the one #118 stated: **the location is a
declared input with one owner**, redirectable in one place. Nothing
about storage, format or production behaviour changes.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.provenance import Provenance
from app.infrastructure.evidence_root import ROOT_ENV, evidence_path
from app.repositories.financial_statement_store import JsonFinancialStatementStore

#: The production location, named once so a drift is visible here.
PRODUCTION = Path("data/statements")


def _observation(symbol: str = "TEST") -> FinancialStatementObservation:
    return FinancialStatementObservation(
        symbol=symbol,
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=StatementConcept.TOTAL_REVENUE,
                anchor=None,
                unlocated_because="nothing was located, in a test",
            ),
        ),
        source=PrimarySource(
            symbol=symbol,
            company="Example Co",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K test-document",
            key="test-document",
            published_on=date(2026, 1, 1),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://example.invalid/test-document",
            provider="test",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
    )


class TestTheDefaultResolvesThroughTheRoot:
    def test_the_default_is_the_configured_evidence_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        assert JsonFinancialStatementStore().directory == tmp_path / "statements"
        assert JsonFinancialStatementStore().directory == evidence_path("statements")

    def test_production_is_what_an_unset_root_still_means(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Production reads exactly what it read before the repair."""

        monkeypatch.delenv(ROOT_ENV, raising=False)

        assert JsonFinancialStatementStore().directory == PRODUCTION

    def test_the_root_is_read_per_construction_not_at_import(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A default frozen at import would ignore a redirection.

        #118's own lesson, and the bug ruff caught in three stores
        during it: the root must be resolved when the store is built.
        """

        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "first"))
        first = JsonFinancialStatementStore().directory

        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "second"))
        second = JsonFinancialStatementStore().directory

        assert first != second
        assert second == tmp_path / "second" / "statements"


class TestRedirectionCoversReadsAndWrites:
    def test_a_write_lands_under_the_isolated_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        JsonFinancialStatementStore().append(_observation())

        written = list((tmp_path / "statements").glob("*.json"))

        assert len(written) == 1

    def test_a_read_sees_only_the_isolated_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The half that matters: an empty root reads empty.

        Before the repair this returned the developer's real corpus,
        so a test that forgot its fixtures passed on ambient state.
        """

        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        store = JsonFinancialStatementStore()

        for symbol in ("AAPL", "JPM", "KO", "TSLA"):
            assert store.latest(symbol, StatementKind.INCOME_STATEMENT) == ()

    def test_the_production_corpus_is_unreachable_under_an_isolated_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No test silently reads production statement evidence."""

        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        directory = JsonFinancialStatementStore().directory

        assert PRODUCTION not in directory.parents
        assert directory != PRODUCTION


class TestAnExplicitPathStillWins:
    def test_an_explicit_directory_overrides_the_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A caller that declares where its evidence lives is obeyed.

        The property BQ8's harness depended on, and the one a
        redirection must not take away.
        """

        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "ignored"))

        explicit = tmp_path / "explicit"

        assert JsonFinancialStatementStore(explicit).directory == explicit
        assert JsonFinancialStatementStore(str(explicit)).directory == explicit

    def test_an_explicit_path_round_trips_an_observation(self, tmp_path: Path) -> None:
        explicit = tmp_path / "explicit"

        store = JsonFinancialStatementStore(explicit)
        store.append(_observation("ACME"))

        assert len(store.latest("ACME", StatementKind.INCOME_STATEMENT)) == 1


class TestTheStoreJoinsTheHermeticInvariant:
    def test_no_literal_production_path_remains_in_the_store(self) -> None:
        """The defect stated as a property of the source itself."""

        import inspect

        from app.repositories import financial_statement_store

        source = inspect.getsource(financial_statement_store)

        assert '"data/statements"' not in source
        assert "evidence_path(" in source
