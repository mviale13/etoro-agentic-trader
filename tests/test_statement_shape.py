"""A shape says whose absence an absence is, or it says nothing.

The measurement's whole value is the distinction a consensus cannot
draw, so the cases below are the three ways *no figure located* arises:
the filer printed no line, the filer printed one this platform does not
read, and this platform read nothing at all.
"""

from datetime import date

from app.domain.financial_statements import StatementConcept, StatementKind
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.statement_shape import Presence, shape_of
from app.domain.tabular_evidence import SourceTable, TableRow

#: A bank's income statement as JPMorgan prints one: a revenue line, a
#: net income line, and no gross profit or operating income anywhere.
BANK_INCOME = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total net revenue", "177,419", "162,878")),
        TableRow(cells=("Total noninterest expense", "91,000", "87,000")),
        TableRow(cells=("Net income", "58,471", "49,552")),
    ),
)

#: A manufacturer's, with both margins printed.
GENERIC_INCOME = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total net sales", "416,161", "391,035")),
        TableRow(cells=("Gross margin", "195,201", "180,683")),
        TableRow(cells=("Operating income", "133,050", "123,216")),
        TableRow(cells=("Net income", "112,010", "93,736")),
    ),
)

#: One a reader would call classified, with both subtotals printed.
CLASSIFIED_BALANCE = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total current assets", "147,957", "152,987")),
        TableRow(cells=("Total current liabilities", "165,631", "176,392")),
        TableRow(cells=("Total liabilities", "285,508", "308,030")),
        TableRow(cells=("Total shareholders' equity", "73,733", "56,950")),
    ),
)


def document(
    income: tuple[SourceTable, ...] = (BANK_INCOME,),
    income_text: str = "Consolidated statements of income",
    balance: tuple[SourceTable, ...] = (),
    balance_text: str = "",
    contenders: int = 1,
) -> SourceDocument:
    return SourceDocument(
        source=PrimarySource(
            symbol="EXA",
            company="Example",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 0000019617-26-000100",
            key="0000019617-26-000100",
            published_on=date(2026, 2, 13),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://www.sec.gov/Archives/example",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        business_description="",
        income_statement_text=income_text,
        income_statement_tables=income,
        income_statement_contenders=contenders,
        balance_sheet_text=balance_text,
        balance_sheet_tables=balance,
        balance_sheet_contenders=contenders if balance else 0,
    )


def income_of(shape, concept: StatementConcept):
    statement = shape.of(StatementKind.INCOME_STATEMENT)
    assert statement is not None

    return statement.of(concept)


def test_a_printed_line_is_reported_with_the_filers_own_label() -> None:
    shape = shape_of("AAPL", document(income=(GENERIC_INCOME,)))

    gross = income_of(shape, StatementConcept.GROSS_PROFIT)

    assert gross is not None
    assert gross.presence is Presence.PRINTED
    assert gross.printed_as == "Gross margin"


def test_a_line_the_filer_never_printed_is_the_filers_absence() -> None:
    shape = shape_of("JPM", document())

    statement = shape.of(StatementKind.INCOME_STATEMENT)
    assert statement is not None

    for concept in (StatementConcept.GROSS_PROFIT, StatementConcept.OPERATING_INCOME):
        shaped = statement.of(concept)

        assert shaped is not None
        assert shaped.presence is Presence.NOT_PRINTED
        assert statement.evidences_absence(concept)


def test_a_label_this_platform_cannot_read_is_this_platforms_absence() -> None:
    """A filer printing "Gross profit before impairment" is not a bank."""

    printed = SourceTable(
        index=0,
        caption="",
        rows=(
            TableRow(cells=("", "2025")),
            TableRow(cells=("Total net sales", "400")),
            TableRow(cells=("Gross profit before exceptional items", "120")),
            TableRow(cells=("Net income", "80")),
        ),
    )

    shape = shape_of("EXA", document(income=(printed,)))

    statement = shape.of(StatementKind.INCOME_STATEMENT)
    assert statement is not None

    gross = statement.of(StatementConcept.GROSS_PROFIT)

    assert gross is not None
    assert gross.presence is Presence.UNREAD
    assert gross.unread == ("Gross profit before exceptional items",)

    # And the absence is explicitly not evidence about the company.
    assert not statement.evidences_absence(StatementConcept.GROSS_PROFIT)


def test_a_statement_where_nothing_was_read_evidences_no_absence() -> None:
    """Measured on MUFG: every concept absent, and none of it evidence.

    A statement whose rows this platform cannot read at all produces the
    identical answer a bank's produces, so the absences must not count.
    """

    unreadable = SourceTable(
        index=0,
        caption="",
        rows=(
            TableRow(cells=("", "2025")),
            TableRow(cells=("Total", "1,000")),
            TableRow(cells=("Total", "2,000")),
        ),
    )

    shape = shape_of("MUFG", document(income=(unreadable,)))

    statement = shape.of(StatementKind.INCOME_STATEMENT)
    assert statement is not None

    assert statement.is_located
    assert not statement.is_read

    for concept in (StatementConcept.GROSS_PROFIT, StatementConcept.OPERATING_INCOME):
        shaped = statement.of(concept)

        assert shaped is not None
        assert shaped.presence is Presence.NOT_PRINTED
        assert not statement.evidences_absence(concept)


def test_a_statement_never_located_says_so_rather_than_reporting_absences() -> None:
    shape = shape_of("EXA", document())

    balance = shape.of(StatementKind.BALANCE_SHEET)
    assert balance is not None

    assert not balance.is_located
    assert not balance.is_read
    assert balance.unlocated_because is not None
    assert "located no balance sheet" in balance.unlocated_because

    for shaped in balance.concepts:
        assert shaped.presence is Presence.UNLOCATED
        assert not balance.evidences_absence(shaped.concept)


def test_a_located_statement_printing_no_readable_table_is_a_different_fact() -> None:
    shape = shape_of(
        "BAC",
        document(balance=(), balance_text="Consolidated Balance Sheet Assets ..."),
    )

    balance = shape.of(StatementKind.BALANCE_SHEET)
    assert balance is not None

    assert balance.unlocated_because is not None
    assert "prints a balance sheet title" in balance.unlocated_because


def test_a_classified_balance_sheet_prints_both_subtotals() -> None:
    shape = shape_of(
        "AAPL",
        document(balance=(CLASSIFIED_BALANCE,), balance_text="Balance sheets"),
    )

    balance = shape.of(StatementKind.BALANCE_SHEET)
    assert balance is not None

    for concept in (
        StatementConcept.TOTAL_CURRENT_ASSETS,
        StatementConcept.TOTAL_CURRENT_LIABILITIES,
    ):
        shaped = balance.of(concept)

        assert shaped is not None
        assert shaped.presence is Presence.PRINTED


def test_a_heading_that_prints_no_figure_is_not_read_as_the_line() -> None:
    """A section heading inside a statement names something and measures nothing."""

    with_heading = SourceTable(
        index=0,
        caption="",
        rows=(
            TableRow(cells=("", "2025")),
            TableRow(cells=("Gross profit", "")),
            TableRow(cells=("Net income", "80")),
        ),
    )

    shape = shape_of("EXA", document(income=(with_heading,)))

    gross = income_of(shape, StatementConcept.GROSS_PROFIT)

    assert gross is not None
    assert gross.presence is Presence.UNREAD


def test_several_contenders_are_reported_as_an_interpretation() -> None:
    shape = shape_of("EXA", document(contenders=3))

    statement = shape.of(StatementKind.INCOME_STATEMENT)
    assert statement is not None

    assert statement.contenders == 3
    assert statement.provenance_uncertain


def test_the_shape_carries_the_document_an_investor_would_cite() -> None:
    shape = shape_of("jpm ", document())

    assert shape.symbol == "JPM"
    assert "10-K 0000019617-26-000100" in shape.source
