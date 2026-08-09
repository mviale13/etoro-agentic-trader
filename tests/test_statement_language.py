"""A language is established from lines a filer printed, never from silence.

Two kinds of case below, and the second matters more than the first.
The positive cases prove each accepted form is read. The rejection cases
prove the near-miss rows that sit directly beside them on the same real
statements are refused — "Net interest income after provision for credit
losses" one row under the line it is not, "Net premiums written" one row
above it, and "Total liabilities and stockholders' equity", which is the
balance sheet's grand total and many times the equity it ends with.
"""

from datetime import UTC, datetime

import pytest

from app.domain.agreement import agreement
from app.domain.financial_statement_consensus import (
    ConsensusFact,
    FinancialStatementConsensus,
)
from app.domain.financial_statements import (
    StatementConcept,
    StatementKind,
    concepts_of,
    matches_concept,
    names_its_own_equity,
)
from app.domain.knowledge_consensus import ConsensusState
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.provenance import Provenance
from app.domain.statement_language import (
    StatementLanguage,
    language_of,
)
from app.domain.tabular_evidence import CellReference, ReportedFigure

# ── the grounding contract ──────────────────────────────────────────


@pytest.mark.parametrize(
    "label",
    [
        "Net interest income",
        "Net Interest Income",
        "Net interest income (a)",
    ],
)
def test_net_interest_income_is_read(label: str) -> None:
    assert matches_concept(StatementConcept.NET_INTEREST_INCOME, label)


@pytest.mark.parametrize(
    "label",
    [
        # Printed directly beneath the line it is not, by six banks in
        # the corpus. A different quantity: struck after an expense.
        "Net interest income after provision for credit losses",
        "Net Interest Income After Provision for Credit Losses",
        # Components, which every ordinary company also prints.
        "Interest income",
        "Interest expense",
        "Total interest income",
        "Net interest margin",
    ],
)
def test_net_interest_income_refuses_its_neighbours(label: str) -> None:
    assert not matches_concept(StatementConcept.NET_INTEREST_INCOME, label)


@pytest.mark.parametrize(
    "label",
    [
        "Premiums",
        "Net premiums earned",
    ],
)
def test_premium_revenue_is_read(label: str) -> None:
    assert matches_concept(StatementConcept.PREMIUM_REVENUE, label)


@pytest.mark.parametrize(
    "label",
    [
        # Chubb prints all three; only the third is revenue.
        "Net premiums written",
        "Increase in unearned premiums",
        # A different sense of the word entirely, printed further down
        # the same statement by MetLife and AIG.
        "Preferred stock redemption premium",
        "Dividends on preferred stock and preferred stock redemption premiums",
        # A bank's insurance line, which is not a clean premium revenue
        # row and must not make a bancassurer read as an insurer.
        "Insurance premiums, including deposit insurance",
        # Allstate's, split by product with no total: the corpus's one
        # insurer this platform cannot establish a premium line for.
        "Property and casualty insurance premiums",
        "Accident and health insurance premiums and contract charges",
    ],
)
def test_premium_revenue_refuses_everything_else(label: str) -> None:
    assert not matches_concept(StatementConcept.PREMIUM_REVENUE, label)


@pytest.mark.parametrize(
    "label",
    [
        "Total Allstate shareholders' equity",
        "Total AIG shareholders’ equity",
        "Total MetLife, Inc.’s stockholders’ equity",
        "Total Chubb shareholders' equity",
        "Total Disney Shareholders’ equity",
        "Total Honeywell shareowners’ equity",
        "Total Deere & Company stockholders’ equity",
        "Total Walmart shareholders' equity",
        # The form that used to be listed by name, now covered by rule.
        "Total JPMorgan Chase stockholders' equity",
    ],
)
def test_a_filer_may_name_its_own_equity(label: str) -> None:
    assert names_its_own_equity(label)
    assert matches_concept(StatementConcept.TOTAL_EQUITY, label)


@pytest.mark.parametrize(
    "label",
    [
        # The grand total. Many times the equity, and the failure this
        # rule exists to make impossible.
        "Total liabilities and stockholders' equity",
        "Total liabilities and shareholders’ equity",
        "Total liabilities, mezzanine equity and equity",
        "Total liabilities, redeemable noncontrolling interest, and"
        " shareholders' equity",
        "Total liabilities, redeemable noncontrolling interest and shareowners’ equity",
        "Total liabilities and common shareholders' equity",
        "Total Liabilities and Equity",
        # Equity including the interests the concept excludes.
        "Total equity",
        "Total equity excluding non-controlling interests",
        "Total permanent equity",
        # Not equity at all.
        "Total liabilities",
        "Total assets",
    ],
)
def test_the_equity_rule_refuses_every_grand_total(label: str) -> None:
    assert not names_its_own_equity(label)
    assert not matches_concept(StatementConcept.TOTAL_EQUITY, label)


def test_the_platform_no_longer_names_a_company_in_its_vocabulary() -> None:
    """The rule replaced a hard-coded company name; it must not come back."""

    from app.domain.financial_statements import CONCEPT_LABELS

    for forms in CONCEPT_LABELS.values():
        for form in forms:
            assert "jpmorgan" not in form.casefold()


def test_the_income_statement_is_asked_for_both_markers() -> None:
    asked = concepts_of(StatementKind.INCOME_STATEMENT)

    assert StatementConcept.NET_INTEREST_INCOME in asked
    assert StatementConcept.PREMIUM_REVENUE in asked


# ── the language derivation ─────────────────────────────────────────


def figure(label: str, printed: str = "60,096") -> ReportedFigure:
    return ReportedFigure(
        value=60096.0,
        printed=printed,
        label=label,
        column_header="2025",
        caption="(in millions)",
        cell=CellReference(table=0, row=3, column=1),
    )


def fact(
    concept: StatementConcept,
    label: str | None,
    agreeing: int = 5,
) -> ConsensusFact:
    located = label is not None

    return ConsensusFact(
        concept=concept,
        addressed_in=5,
        observations=5,
        anchor=figure(label) if located else None,
        row=(),
        unlocated_because=None if located else "The reading located no cell.",
        agreement=agreement(
            "where",
            ["yes"] * agreeing + ["no"] * (5 - agreeing),
        ),
    )


def consensus(
    facts: tuple[ConsensusFact, ...],
    statement: StatementKind = StatementKind.INCOME_STATEMENT,
) -> FinancialStatementConsensus:
    return FinancialStatementConsensus(
        symbol="EXA",
        statement=statement,
        source=PrimarySource(
            symbol="EXA",
            company="Example",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 1",
            key="1",
            published_on=datetime.now(UTC).date(),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://example",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        observation_count=5,
        quorum=5,
        state=ConsensusState.QUORATE,
        located_among=1,
        facts=facts,
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
    )


def test_a_net_interest_subtotal_establishes_interest_based() -> None:
    established = language_of(
        consensus(
            (
                fact(StatementConcept.NET_INCOME, "Net income"),
                fact(StatementConcept.NET_INTEREST_INCOME, "Net interest income"),
                fact(StatementConcept.PREMIUM_REVENUE, None),
            )
        )
    )

    assert established.language is StatementLanguage.INTEREST_BASED
    assert established.statement_read


def test_a_premium_line_establishes_insurance_based() -> None:
    established = language_of(
        consensus(
            (
                fact(StatementConcept.NET_INCOME, "Net income"),
                fact(StatementConcept.NET_INTEREST_INCOME, None),
                fact(StatementConcept.PREMIUM_REVENUE, "Premiums"),
            )
        )
    )

    assert established.language is StatementLanguage.INSURANCE_BASED


def test_both_lines_establish_both_rather_than_either() -> None:
    """A bancassurer prints both, and the answer must not silently pick one."""

    established = language_of(
        consensus(
            (
                fact(StatementConcept.NET_INCOME, "Net income"),
                fact(StatementConcept.NET_INTEREST_INCOME, "Net interest income"),
                fact(StatementConcept.PREMIUM_REVENUE, "Premiums"),
            )
        )
    )

    assert established.language is StatementLanguage.BOTH


def test_a_read_statement_with_neither_line_establishes_neither() -> None:
    established = language_of(
        consensus(
            (
                fact(StatementConcept.TOTAL_REVENUE, "Total net sales"),
                fact(StatementConcept.NET_INCOME, "Net income"),
                fact(StatementConcept.NET_INTEREST_INCOME, None),
                fact(StatementConcept.PREMIUM_REVENUE, None),
            )
        )
    )

    assert established.language is StatementLanguage.NEITHER
    assert established.statement_read


def test_an_unread_statement_establishes_nothing() -> None:
    """The MUFG regression: rows labelled only 'Total' locate nothing.

    Every concept absent is what a bank, an insurer and an ordinary
    company all look like when the statement could not be read, so it
    must never come out as `NEITHER`.
    """

    established = language_of(
        consensus(
            (
                fact(StatementConcept.TOTAL_REVENUE, None),
                fact(StatementConcept.NET_INCOME, None),
                fact(StatementConcept.NET_INTEREST_INCOME, None),
                fact(StatementConcept.PREMIUM_REVENUE, None),
            )
        )
    )

    assert established.language is StatementLanguage.NOT_ESTABLISHED
    assert not established.statement_read
    assert established.absent_because is not None
    assert "MUFG" in established.absent_because


def test_a_balance_sheet_consensus_establishes_no_language() -> None:
    established = language_of(
        consensus(
            (fact(StatementConcept.TOTAL_EQUITY, "Total shareholders' equity"),),
            statement=StatementKind.BALANCE_SHEET,
        )
    )

    assert established.language is StatementLanguage.NOT_ESTABLISHED
    assert established.absent_because is not None


def test_a_reading_that_predates_the_concept_says_so() -> None:
    """A stored schema-2 reading was never asked, which is not an absence."""

    established = language_of(
        consensus((fact(StatementConcept.NET_INCOME, "Net income"),))
    )

    marker = established.marker(StatementConcept.NET_INTEREST_INCOME)

    assert marker is not None
    assert not marker.is_established
    assert marker.absent_because is not None
    assert "was asked" in marker.absent_because


def test_the_language_carries_the_narrowest_width_beneath_it() -> None:
    established = language_of(
        consensus(
            (
                fact(StatementConcept.NET_INCOME, "Net income"),
                fact(
                    StatementConcept.NET_INTEREST_INCOME,
                    "Net interest income",
                    agreeing=3,
                ),
                fact(StatementConcept.PREMIUM_REVENUE, None),
            )
        )
    )

    assert established.support is not None
    assert established.support.agreeing == 3
