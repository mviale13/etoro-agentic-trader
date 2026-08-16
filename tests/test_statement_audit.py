"""Supersession removes authority from refuted readings, and nothing else.

The rule under test is narrow on purpose: a stored reading loses its vote
only where today's parse of the same immutable filing positively reads
something different at the cell the reading cited. Everything else — a
parse that moved, a table this platform can no longer head, a row that is
not where it was — keeps its authority, because failing to look is not
finding a contradiction.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.financial_statement_consensus import statement_consensus_of
from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.primary_source import SourceDocument
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    ReportedFigure,
    SourceTable,
    TableRow,
)
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services import statement_audit
from app.services.statement_audit import AuditVerdict, audit_observation
from tests.test_financial_statement_store import ACCESSION, source

CAPTION = "(in millions)"


def table(header: str = "2025", figure: str = "177,419") -> SourceTable:
    """A filing's own table: a spanned title, the years, then the row."""

    return SourceTable(
        index=0,
        caption=CAPTION,
        rows=(
            TableRow(cells=("", "Year Ended December 31,", "")),
            TableRow(cells=("", header, "2024")),
            TableRow(cells=("Total net revenue", figure, "162,878")),
        ),
    )


def document(built: SourceTable) -> SourceDocument:
    return SourceDocument(
        source=source(),
        business_description="",
        income_statement_tables=(built,),
    )


def anchor(
    column_header: str = "2025",
    printed: str = "177,419",
    value: float = 177419.0,
    label: str = "Total net revenue",
    row: int = 2,
    column: int = 1,
) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header=column_header,
        printed=printed,
        value=value,
        cell=CellReference(table=0, row=row, column=column),
        caption=CAPTION,
    )


def reading(
    stored: ReportedFigure | None = None,
    cells: int = 2,
) -> FinancialStatementObservation:
    stored = stored or anchor()
    later = anchor(column_header="2024", printed="162,878", value=162878.0, column=2)
    row = (stored, later)

    return FinancialStatementObservation(
        symbol="JPM",
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=StatementConcept.TOTAL_REVENUE,
                anchor=stored,
                row=row[:cells],
            ),
        ),
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 9, tzinfo=UTC)
        ),
    )


def ruled(observation: FinancialStatementObservation, built: SourceTable):
    return audit_observation(observation, document(built), "JPM", ACCESSION, 0)


# ── the rule ────────────────────────────────────────────────────────


def test_a_reading_todays_parse_reproduces_keeps_its_authority() -> None:
    assert ruled(reading(), table()).verdict is AuditVerdict.ACTIVE


def test_an_undated_header_where_the_filer_prints_a_year_is_stale() -> None:
    stale = reading(stored=anchor(column_header="Year Ended December 31,"))

    ruling = ruled(stale, table())

    assert ruling.verdict is AuditVerdict.STALE_PROVENANCE
    assert ruling.supersedes
    assert "'2025'" in ruling.because()


def test_a_row_the_filer_prints_wider_than_the_reading_captured_is_stale() -> None:
    ruling = ruled(reading(cells=1), table())

    assert ruling.verdict is AuditVerdict.STALE_PROVENANCE


def test_a_different_printed_figure_at_the_same_cell_is_invalid() -> None:
    ruling = ruled(reading(), table(figure="999,999"))

    assert ruling.verdict is AuditVerdict.INVALID_EXTRACTION
    assert ruling.supersedes


# ── what may never supersede ────────────────────────────────────────


def test_a_column_todays_parse_cannot_head_keeps_its_authority() -> None:
    """Honeywell's shape: rows and labels intact, every column unheaded."""

    unheaded = SourceTable(
        index=0,
        caption=CAPTION,
        rows=(
            TableRow(cells=("", "Year Ended December 31,", "")),
            TableRow(cells=("2025", "", "")),
            TableRow(cells=("Total net revenue", "177,419", "162,878")),
        ),
    )

    ruling = ruled(reading(), unheaded)

    assert ruling.verdict is AuditVerdict.UNDECIDABLE
    assert not ruling.supersedes


def test_a_moved_row_keeps_its_authority() -> None:
    moved = SourceTable(
        index=0,
        caption=CAPTION,
        rows=(
            TableRow(cells=("", "2025", "2024")),
            TableRow(cells=("Something else", "1", "2")),
            TableRow(cells=("Another line", "3", "4")),
        ),
    )

    assert ruled(reading(), moved).verdict is AuditVerdict.UNDECIDABLE


def test_a_row_that_no_longer_exists_keeps_its_authority() -> None:
    short = SourceTable(
        index=0,
        caption=CAPTION,
        rows=(TableRow(cells=("", "2025", "2024")),),
    )

    assert ruled(reading(), short).verdict is AuditVerdict.UNDECIDABLE


def test_a_reading_holding_more_cells_than_todays_parse_keeps_authority() -> None:
    """This platform reading less than it once did is not a refutation."""

    narrow = SourceTable(
        index=0,
        caption=CAPTION,
        rows=(
            TableRow(cells=("", "Year Ended December 31,")),
            TableRow(cells=("", "2025")),
            TableRow(cells=("Total net revenue", "177,419")),
        ),
    )

    assert ruled(reading(cells=2), narrow).verdict is AuditVerdict.UNDECIDABLE


def test_a_reading_that_located_nothing_is_undecidable() -> None:
    absent = FinancialStatementObservation(
        symbol="JPM",
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=StatementConcept.TOTAL_REVENUE,
                anchor=None,
                unlocated_because="The reading located no cell holding it.",
            ),
        ),
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 9, tzinfo=UTC)
        ),
    )

    assert ruled(absent, table()).verdict is AuditVerdict.UNDECIDABLE


# ── the rule cannot see an answer ───────────────────────────────────

#: Every name by which an analytical outcome could reach this audit. The
#: point of supersession is that evidence is withdrawn for what the
#: filing says, never for what withdrawing it would do to a verdict — so
#: the rule is pinned to be structurally incapable of consulting one.
FORBIDDEN = frozenset(
    {
        "BusinessQuality",
        "QualityBand",
        "quality_of",
        "band",
        "band_for",
        "score",
        "favourable",
        "adverse",
        "sense_of",
        "FinancialUnderstanding",
        "financial_engine",
        "answer_questions",
        "assess",
        "recommendation",
        "portfolio",
        "decide",
    }
)


def _identifiers(module) -> set[str]:  # type: ignore[no-untyped-def]
    """Every name the module's *code* uses — docstrings excluded.

    Read from the syntax tree rather than the text, because a module
    that explains in prose what it refuses to import would otherwise
    fail its own guard for saying so.
    """

    tree = ast.parse(inspect.getsource(module))
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.update(node.name.split("."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.update(node.module.split("."))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)

    return names


def _constants(module) -> set[str]:  # type: ignore[no-untyped-def]
    """Every string literal in the module's code, docstrings excluded."""

    tree = ast.parse(inspect.getsource(module))
    docstrings = {
        ast.get_docstring(node)
        for node in ast.walk(tree)
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
    }

    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    }


def test_the_audit_cannot_read_an_analytical_outcome() -> None:
    used = _identifiers(statement_audit)

    assert not used & FORBIDDEN, f"the audit reaches {sorted(used & FORBIDDEN)}"


def test_the_audit_names_no_company() -> None:
    """No symbol-specific exception, in either direction."""

    literals = _constants(statement_audit)

    for symbol in ("ALL", "TSLA", "WMT", "KO", "MTB", "RF", "HON", "C", "JPM"):
        assert symbol not in literals, f"the audit names {symbol}"


def test_the_same_defect_supersedes_whichever_way_the_figures_move() -> None:
    """A rising row and a falling row are ruled identically."""

    rising = ruled(
        reading(stored=anchor(column_header="Year Ended December 31,")),
        table(),
    )

    falling_table = SourceTable(
        index=0,
        caption=CAPTION,
        rows=(
            TableRow(cells=("", "Year Ended December 31,", "")),
            TableRow(cells=("", "2025", "2024")),
            TableRow(cells=("Total net revenue", "177,419", "999,999")),
        ),
    )
    falling = ruled(
        reading(stored=anchor(column_header="Year Ended December 31,")),
        falling_table,
    )

    assert rising.verdict is falling.verdict is AuditVerdict.STALE_PROVENANCE


# ── the store ───────────────────────────────────────────────────────


def test_an_entry_without_the_field_loads_as_authoritative(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(reading())

    restored = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)

    assert restored[0].superseded_because is None
    assert restored[0].is_active


def test_an_active_store_encodes_without_the_field(tmp_path: Path) -> None:
    """No migration: a store of active readings is byte-identical to before."""

    store = JsonFinancialStatementStore(tmp_path)
    store.append(reading())

    written = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")

    assert "superseded_because" not in written


def test_supersession_keeps_the_reading_and_removes_its_vote(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(reading())
    store.append(reading())

    assert store.supersede("JPM", ACCESSION, {0: "the filer heads it 2025"}) == 1

    restored = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)

    assert len(restored) == 2, "the reading is still stored"
    assert restored[0].superseded_because == "the filer heads it 2025"
    assert not restored[0].is_active
    assert restored[1].is_active
    assert restored[0].facts == restored[1].facts, "what it found is untouched"


def test_supersession_is_write_once(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(reading())

    store.supersede("JPM", ACCESSION, {0: "the first reason"})

    assert store.supersede("JPM", ACCESSION, {0: "a softer reason"}) == 0

    restored = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)

    assert restored[0].superseded_because == "the first reason"


def test_superseding_nothing_leaves_the_file_alone(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(reading())

    before = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")

    assert store.supersede("JPM", ACCESSION, {}) == 0
    assert next(tmp_path.glob("*.json")).read_text(encoding="utf-8") == before


# ── the consensus ───────────────────────────────────────────────────


def superseded(why: str = "the filer heads it 2025") -> FinancialStatementObservation:
    return FinancialStatementObservation(
        symbol="JPM",
        statement=StatementKind.INCOME_STATEMENT,
        facts=reading().facts,
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 9, tzinfo=UTC)
        ),
        superseded_because=why,
    )


def test_a_superseded_reading_does_not_vote() -> None:
    consensus = statement_consensus_of((superseded(), reading(), reading()))

    assert consensus.observation_count == 2
    assert consensus.superseded_count == 1


def test_the_consensus_says_what_it_did_not_count() -> None:
    consensus = statement_consensus_of((superseded(), reading()))

    caveat = consensus.supersession_caveat()

    assert caveat is not None
    assert "3 stored readings" not in caveat
    assert "superseded rather than" in caveat
    assert "deleted" in caveat


def test_a_consensus_with_nothing_superseded_says_nothing() -> None:
    assert statement_consensus_of((reading(),)).supersession_caveat() is None


def test_a_wholly_superseded_statement_is_refused_not_invented() -> None:
    with pytest.raises(ValueError, match="superseded"):
        statement_consensus_of((superseded(), superseded()))


def test_quorum_counts_only_authoritative_readings() -> None:
    """The threshold is untouched; what it counts is what still votes."""

    held = (*(reading() for _ in range(4)), superseded())

    assert not statement_consensus_of(held).is_quorate
    assert statement_consensus_of((*held, reading())).is_quorate
