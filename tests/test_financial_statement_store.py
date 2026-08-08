"""Statement observations are kept append-only, and never upgraded."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

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
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import (
    STATEMENT_SCHEMA_VERSION,
    JsonFinancialStatementStore,
)

ACCESSION = "0000019617-26-000100"


def source(key: str = ACCESSION, published: str = "2026-02-13") -> PrimarySource:
    return PrimarySource(
        symbol="JPM",
        company="Example Bank",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
        published_on=date.fromisoformat(published),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{key}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


def figure(column: int = 1, printed: str = "177,419", value: float = 177419.0):
    return ReportedFigure(
        label="Total net revenue",
        column_header="2025" if column == 1 else "2024",
        printed=printed,
        value=value,
        cell=CellReference(table=0, row=1, column=column),
        caption="(in millions)",
    )


def observation(
    key: str = ACCESSION, published: str = "2026-02-13"
) -> FinancialStatementObservation:
    anchor = figure()

    return FinancialStatementObservation(
        symbol="JPM",
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=StatementConcept.TOTAL_REVENUE,
                anchor=anchor,
                row=(anchor, figure(column=2, printed="162,878", value=162878.0)),
            ),
            StatementFact(
                concept=StatementConcept.NET_INCOME,
                anchor=None,
                unlocated_because="The reading located no cell holding it.",
            ),
        ),
        source=source(key, published),
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        ),
    )


def test_an_observation_survives_the_round_trip_exactly(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)

    store.append(observation())
    store.append(observation())

    restored = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)

    assert len(restored) == 2
    assert restored[0] == observation()
    assert restored[1] == observation()


def test_appending_never_replaces_what_a_reading_found(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)

    store.append(observation())
    first = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)
    store.append(observation())

    assert store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)[0] == first[0]


def test_another_schema_version_is_absent_not_upgraded(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())

    path = next(tmp_path.glob("*.json"))
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["schema_version"] = STATEMENT_SCHEMA_VERSION + 1
    path.write_text(json.dumps(stored), encoding="utf-8")

    assert store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT) == ()


def test_an_unreadable_entry_is_absent_not_repaired(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())

    path = next(tmp_path.glob("*.json"))
    path.write_text("{not json", encoding="utf-8")

    assert store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT) == ()


def test_latest_is_the_newest_filing_not_the_newest_reading(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)

    newer = "0000019617-26-000200"

    store.append(observation(key=newer, published="2026-02-13"))
    # An older filing read later must not become the current word.
    store.append(observation(key=ACCESSION, published="2025-02-14"))

    latest = store.latest("JPM", StatementKind.INCOME_STATEMENT)

    assert latest and latest[0].source.key == newer
