"""What repeated statement readings agree on, counted content-blind."""

from datetime import UTC, date, datetime

import pytest

from app.domain.financial_statement_consensus import (
    NO_FIGURE,
    statement_consensus_of,
)
from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.knowledge_consensus import ConsensusState
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure

ACCESSION = "0000019617-26-000100"


def source(key: str = ACCESSION) -> PrimarySource:
    return PrimarySource(
        symbol="JPM",
        company="Example Bank",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
        published_on=date(2026, 2, 13),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{key}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


def figure(printed: str = "177,419", value: float = 177419.0, row: int = 1):
    return ReportedFigure(
        label="Total net revenue",
        column_header="2025",
        printed=printed,
        value=value,
        cell=CellReference(table=0, row=row, column=1),
        caption="(in millions)",
    )


def located_fact(printed: str = "177,419", value: float = 177419.0, row: int = 1):
    anchor = figure(printed, value, row)

    return StatementFact(
        concept=StatementConcept.TOTAL_REVENUE,
        anchor=anchor,
        row=(anchor,),
    )


def absent_fact(because: str = "The reading located no cell holding it."):
    return StatementFact(
        concept=StatementConcept.TOTAL_REVENUE,
        anchor=None,
        unlocated_because=because,
    )


def observation(
    fact: StatementFact,
    key: str = ACCESSION,
    kind: StatementKind = StatementKind.INCOME_STATEMENT,
) -> FinancialStatementObservation:
    return FinancialStatementObservation(
        symbol="JPM",
        statement=kind,
        facts=(fact,),
        source=source(key),
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime(2026, 8, 8, tzinfo=UTC),
        ),
    )


def test_a_majority_settles_a_figure_verbatim() -> None:
    """The settled anchor is, verbatim, an observation's checked figure."""

    consensus = statement_consensus_of(
        (
            observation(located_fact()),
            observation(located_fact()),
            observation(absent_fact()),
        )
    )

    fact = consensus.fact(StatementConcept.TOTAL_REVENUE)

    assert fact is not None and fact.anchor is not None
    assert fact.anchor.printed == "177,419"
    assert fact.row == (fact.anchor,)
    assert fact.agreement.counted() == "2/3"


def test_a_settled_absence_carries_its_modal_reason_with_the_count() -> None:
    consensus = statement_consensus_of(
        (
            observation(absent_fact()),
            observation(absent_fact()),
            observation(located_fact()),
        )
    )

    fact = consensus.fact(StatementConcept.TOTAL_REVENUE)

    assert fact is not None and fact.anchor is None
    assert fact.unlocated_because is not None
    assert "located no cell" in fact.unlocated_because
    # Readings of a filing, never "observations": the count is repeated
    # attempts on one document, and the wording may not let it read as
    # independent corroboration (BQ4, STATEMENT_GAP_TRUTHFULNESS.md).
    assert "2 of 3 readings of one filing" in fact.unlocated_because
    assert "observations" not in fact.unlocated_because


def test_a_tie_settles_nothing_and_serves_its_distribution() -> None:
    consensus = statement_consensus_of(
        (
            observation(located_fact()),
            observation(located_fact(printed="162,878", value=162878.0, row=2)),
        )
    )

    fact = consensus.fact(StatementConcept.TOTAL_REVENUE)

    assert fact is not None and fact.anchor is None
    assert fact.unlocated_because is not None
    assert "unsettled across 2 readings" in fact.unlocated_because
    assert "observations" not in fact.unlocated_because
    assert "162,878" in fact.unlocated_because


def test_the_comparable_answer_is_the_anchor_cell_and_value() -> None:
    """Two readings that found the same figure in the same cell agree."""

    consensus = statement_consensus_of(
        (observation(located_fact()), observation(located_fact()))
    )

    fact = consensus.fact(StatementConcept.TOTAL_REVENUE)

    assert fact is not None
    assert fact.agreement.settled
    assert fact.agreement.modal is not None
    assert fact.agreement.modal.stated != NO_FIGURE
    assert "table 0, row 1, column 1" in fact.agreement.modal.stated


def test_quorum_is_a_property_of_the_count_alone() -> None:
    below = statement_consensus_of(tuple(observation(located_fact()) for _ in range(2)))
    at = statement_consensus_of(tuple(observation(located_fact()) for _ in range(5)))

    assert below.state is ConsensusState.INSUFFICIENT_QUORUM
    assert at.state is ConsensusState.QUORATE
    assert "not yet a consensus" in below.reading.source
    assert "consensus of 5 statement readings" in at.reading.source


def test_an_empty_set_derives_nothing() -> None:
    with pytest.raises(ValueError, match="none were given"):
        statement_consensus_of(())


def test_two_documents_cannot_share_a_consensus() -> None:
    with pytest.raises(ValueError, match="one immutable document"):
        statement_consensus_of(
            (
                observation(located_fact()),
                observation(located_fact(), key="0000019617-25-000099"),
            )
        )


def test_two_statements_cannot_share_a_consensus() -> None:
    """Guarded now, while the vocabulary holds one kind, so growing it
    cannot silently pool readings of different statements."""

    first = observation(located_fact())
    second = FinancialStatementObservation(
        symbol="JPM",
        statement="balance_sheet",  # type: ignore[arg-type]
        facts=(located_fact(),),
        source=source(),
        reading=first.reading,
    )

    with pytest.raises(ValueError, match="one statement"):
        statement_consensus_of((first, second))
