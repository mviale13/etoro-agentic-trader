"""Every evidence repository hangs from the declared evidence root.

BQ10, closing the class #118 opened. That slice made the root a
declared input and converted the provider caches; every *repository*
kept a string literal, and BQ9 found the first of them the hard way —
the statement store was reading the developer's own corpus in tests
that thought they were hermetic.

This file states the invariant once, over the whole participating set,
so the next repository added either joins it or is named in
`OUTSIDE_THE_ROOT` with a reason. A test asserting one store's
behaviour would have to be remembered; this one cannot be forgotten,
because a new store that ignores the root fails it by construction.
"""

from __future__ import annotations

import inspect
import pkgutil
from pathlib import Path
from typing import Any

import pytest

from app.infrastructure.evidence_root import ROOT_ENV, evidence_path
from app.memory.json_snapshot_repository import JsonSnapshotRepository
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.repositories.investment_decision_store import JsonInvestmentDecisionStore
from app.repositories.json_event_repository import JsonEventRepository

#: Every repository whose default location is evidence, with the
#: segment it must hang from and how it names its own directory.
PARTICIPATING: tuple[tuple[str, Any, str, str], ...] = (
    ("statements", JsonFinancialStatementStore, "statements", "directory"),
    ("knowledge", JsonCompanyKnowledgeStore, "knowledge", "directory"),
    ("decisions", JsonInvestmentDecisionStore, "decisions", "_directory"),
    ("events", JsonEventRepository, "events", "directory"),
    (
        "snapshots",
        JsonSnapshotRepository,
        "portfolio_snapshots",
        "_directory",
    ),
)

#: Deliberately outside the abstraction, with the reason recorded.
#:
#: `data/investor_strategy.json` is the investor's own declared
#: strategy — one tracked configuration file read by a service, not a
#: stream of observations kept by a repository. Redirecting it with the
#: evidence root would make a test's *configuration* depend on where
#: its *evidence* lives, which is the coupling this module exists to
#: remove rather than to spread.
OUTSIDE_THE_ROOT = {
    "app/services/investor_strategy_service.py": (
        "static configuration, not an evidence stream"
    ),
}


def _directory(repository: Any, attribute: str) -> Path:
    return Path(getattr(repository, attribute))


@pytest.mark.parametrize(
    ("name", "factory", "segment", "attribute"),
    PARTICIPATING,
    ids=[row[0] for row in PARTICIPATING],
)
class TestEveryEvidenceRepositoryObeysTheRoot:
    def test_the_default_hangs_from_the_configured_root(
        self,
        name: str,
        factory: Any,
        segment: str,
        attribute: str,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        assert _directory(factory(), attribute) == tmp_path / segment
        assert _directory(factory(), attribute) == evidence_path(segment)

    def test_nothing_is_read_or_written_outside_that_root(
        self,
        name: str,
        factory: Any,
        segment: str,
        attribute: str,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Production evidence is unreachable under an isolated root."""

        monkeypatch.setenv(ROOT_ENV, str(tmp_path))

        directory = _directory(factory(), attribute)

        assert tmp_path in directory.parents or directory == tmp_path / segment
        assert directory != Path("data") / segment

    def test_an_explicit_path_stays_authoritative(
        self,
        name: str,
        factory: Any,
        segment: str,
        attribute: str,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "ignored"))

        explicit = tmp_path / "explicit" / name

        assert _directory(factory(explicit), attribute) == explicit

    def test_the_root_is_re_read_between_constructions(
        self,
        name: str,
        factory: Any,
        segment: str,
        attribute: str,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """No repository freezes a root it saw earlier.

        The failure a signature default produces: `evidence_path(...)`
        evaluated at import binds whatever root existed then, and a
        later redirection is silently ignored.
        """

        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "first"))
        first = _directory(factory(), attribute)

        monkeypatch.setenv(ROOT_ENV, str(tmp_path / "second"))
        second = _directory(factory(), attribute)

        assert first != second
        assert second == tmp_path / "second" / segment

    def test_production_is_still_what_an_unset_root_means(
        self,
        name: str,
        factory: Any,
        segment: str,
        attribute: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The repair changes isolation, never production behaviour."""

        monkeypatch.delenv(ROOT_ENV, raising=False)

        assert _directory(factory(), attribute) == Path("data") / segment


class TestTheClassIsClosed:
    """A new repository cannot quietly reintroduce the defect."""

    def test_no_module_defaults_to_a_data_literal(self) -> None:
        """Search the source, not a remembered list.

        Anything naming `data/...` as its own default is either an
        evidence repository that must hang from the root, or it is
        recorded in `OUTSIDE_THE_ROOT` with a reason.
        """

        import app

        offenders: list[str] = []

        for module in pkgutil.walk_packages(app.__path__, prefix="app."):
            try:
                imported = __import__(module.name, fromlist=["_"])
                source = inspect.getsource(imported)
            except (ImportError, OSError, TypeError):
                continue

            if '= "data/' in source or '= Path("data/' in source:
                path = module.name.replace(".", "/") + ".py"

                if path not in OUTSIDE_THE_ROOT:
                    offenders.append(path)

        assert offenders == [], (
            f"{offenders} default to a literal evidence path; hang them "
            "from evidence_path(...) or record them in OUTSIDE_THE_ROOT "
            "with the reason they are outside the abstraction"
        )

    def test_every_documented_exception_still_exists(self) -> None:
        """A stale exemption is a lie about the codebase."""

        for path in OUTSIDE_THE_ROOT:
            assert Path(path).exists(), f"{path} is exempted and gone"
