"""A surface may read what is known; it may never decide to pay for more.

The property this file exists to hold is the first one: composing an
understanding for a page must not resolve a filing, fetch a document or
ask a model. Everything else here follows from it — where nothing has
been observed, the absence is worded rather than filled.
"""

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
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.company_knowledge_service import CompanyKnowledgeService
from app.services.company_understanding_service import CompanyUnderstandingService
from app.services.financial_statement_service import FinancialStatementService

ACCESSION = "0000019617-26-000100"


def source() -> PrimarySource:
    return PrimarySource(
        symbol="EXA",
        company="Example Group",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {ACCESSION}",
        key=ACCESSION,
        published_on=date(2026, 2, 13),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{ACCESSION}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


class ExplodingResolver:
    """Any network use at all is the failure this suite is looking for."""

    def resolve(self, symbol: str):  # noqa: ANN001, ANN201
        raise AssertionError(
            "A surface resolved a primary source. Composing an understanding "
            "must read the stores and nothing else."
        )


class ExplodingExtractor:
    """A model call from a page view is the other half of the same failure."""

    async def extract(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("A surface asked a model to read a filing.")


def statement_observation(concept: StatementConcept, value: float, label: str):
    return FinancialStatementObservation(
        symbol="EXA",
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=concept,
                anchor=ReportedFigure(
                    label=label,
                    column_header="2025",
                    printed=f"{value:,.0f}",
                    value=value,
                    cell=CellReference(table=0, row=1, column=1),
                    caption="(in millions)",
                ),
                row=(),
            ),
        ),
        source=source(),
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
        located_among=1,
    )


@pytest.fixture
def service(tmp_path: Path) -> CompanyUnderstandingService:
    """Both services pointed at empty stores, and at nothing else."""

    return CompanyUnderstandingService(
        knowledge=CompanyKnowledgeService(
            store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
            sources=ExplodingResolver(),  # type: ignore[arg-type]
            extractor=ExplodingExtractor(),  # type: ignore[arg-type]
        ),
        statements=FinancialStatementService(
            store=JsonFinancialStatementStore(tmp_path / "statements"),
            sources=ExplodingResolver(),  # type: ignore[arg-type]
            extractor=ExplodingExtractor(),  # type: ignore[arg-type]
        ),
    )


def test_an_unread_company_costs_nothing_and_says_so(
    service: CompanyUnderstandingService,
) -> None:
    """The whole point: no resolve, no fetch, no model, no exception."""

    understanding = service.understanding("EXA")

    assert not understanding.is_understood
    assert understanding.business is None
    assert understanding.financial is None

    assert understanding.business_absent_because is not None
    assert "EXA" in understanding.business_absent_because

    assert understanding.financial_absent_because is not None


def test_an_absence_names_the_explicit_spend_rather_than_taking_it(
    service: CompanyUnderstandingService,
) -> None:
    """A surface reports the gap and names the command that closes it."""

    understanding = service.understanding("EXA")

    assert understanding.business_absent_because is not None
    assert "observe" in understanding.business_absent_because

    assert understanding.financial_absent_because is not None
    assert "observe-statements" in understanding.financial_absent_because


def test_a_symbol_is_normalised_before_anything_is_looked_up(
    service: CompanyUnderstandingService,
) -> None:
    assert service.understanding(" exa ").symbol == "EXA"


def test_statements_alone_are_understood_without_narrative_knowledge(
    tmp_path: Path,
) -> None:
    """The halves fail independently, which is why they are two fields."""

    store = JsonFinancialStatementStore(tmp_path / "statements")

    store.append(
        statement_observation(StatementConcept.TOTAL_REVENUE, 182447, "Total revenue")
    )
    store.append(
        statement_observation(StatementConcept.NET_INCOME, 57048, "Net income")
    )

    service = CompanyUnderstandingService(
        knowledge=CompanyKnowledgeService(
            store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
            sources=ExplodingResolver(),  # type: ignore[arg-type]
            extractor=ExplodingExtractor(),  # type: ignore[arg-type]
        ),
        statements=FinancialStatementService(
            store=store,
            sources=ExplodingResolver(),  # type: ignore[arg-type]
            extractor=ExplodingExtractor(),  # type: ignore[arg-type]
        ),
    )

    understanding = service.understanding("EXA")

    assert understanding.is_understood
    assert understanding.financial is not None
    assert understanding.business is None
    assert understanding.business_absent_because is not None


def test_the_store_only_door_never_reaches_a_provider(tmp_path: Path) -> None:
    """`established` is the read-only door; `knowledge` is not, by design."""

    knowledge = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
        sources=ExplodingResolver(),  # type: ignore[arg-type]
        extractor=ExplodingExtractor(),  # type: ignore[arg-type]
    )

    outcome = knowledge.established("EXA")

    assert outcome.knowledge is None
    assert not outcome.state.is_available

    statements = FinancialStatementService(
        store=JsonFinancialStatementStore(tmp_path / "statements"),
        sources=ExplodingResolver(),  # type: ignore[arg-type]
        extractor=ExplodingExtractor(),  # type: ignore[arg-type]
    )

    assert statements.established("EXA") == {}
