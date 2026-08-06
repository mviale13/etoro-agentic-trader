"""The reader is configured apart from the writer, and says so when absent."""

from pathlib import Path

import pytest

from app.services.company_knowledge_extractor import CompanyKnowledgeExtractor
from app.services.company_knowledge_reader import (
    DEFAULT_MODELS,
    MODEL_ENV,
    PROVIDER_ENV,
    resolve_reader,
)
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeState,
)
from app.services.executive_writer_service import (
    DEFAULT_MODELS as WRITER_MODELS,
)


def test_a_reader_without_credentials_is_a_worded_absence() -> None:
    """
    Not an exception, and not a silent fallback to reading nothing.

    The sentence is what a surface shows in place of a company's
    segments, so it has to name which seam is unconfigured — a reader
    that borrowed the writer's wording would send someone to check the
    wrong configuration.
    """

    resolved = resolve_reader()

    assert isinstance(resolved, str)
    assert "knowledge reader" in resolved
    assert "OpenAI" in resolved


def test_an_unknown_reader_provider_is_named_rather_than_defaulted(
    monkeypatch,
) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "a-provider-that-does-not-exist")

    resolved = resolve_reader()

    assert isinstance(resolved, str)
    assert "a-provider-that-does-not-exist" in resolved


def test_the_reader_is_not_pinned_to_the_writers_model() -> None:
    """
    Reading a filing and wording a case are different jobs.

    The writer's default is small and cheap on purpose, because wording
    a finished case is formatting. Locating one cell among forty tables
    is not, and a reader that inherited the writer's default would be
    quietly downgraded by a decision taken about something else.
    """

    assert DEFAULT_MODELS["openai"] != WRITER_MODELS["openai"]


def test_the_reader_model_can_be_pinned_without_a_code_change(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used")
    monkeypatch.setenv(MODEL_ENV, "gpt-5-pinned")

    resolved = resolve_reader()

    assert isinstance(resolved, CompanyKnowledgeExtractor)


class ResolverStub:
    """A resolver that would answer, if anything got as far as asking it."""

    def resolve(self, symbol: str):  # pragma: no cover - never reached
        raise AssertionError("The reader's absence is decided before this.")


def test_a_supplied_reader_is_taken_at_its_word() -> None:
    """
    A stand-in that answers the same way is a reader.

    Inspecting what a caller handed over would reject every double that
    is not literally a `CompanyKnowledgeExtractor`, which is the whole
    point of the seam — and it did, until this was caught.
    """

    class Stub:
        async def extract(self, symbol, document):  # pragma: no cover
            raise AssertionError

    service = CompanyKnowledgeService(
        sources=ResolverStub(),  # type: ignore[arg-type]
        extractor=Stub(),  # type: ignore[arg-type]
    )

    assert service._extractor is not None
    assert service._unreadable is None


@pytest.mark.anyio
async def test_the_readers_absence_travels_to_the_surface(tmp_path: Path) -> None:
    """
    Why a company is undescribed is a fact about the platform, reported.

    An unconfigured reader is a different situation from a gap in
    coverage or an outage, and a reader of the dashboard must not have
    to guess which one they are looking at.
    """

    from datetime import date

    from app.domain.primary_source import (
        IdentityCheck,
        PrimarySource,
        SourceAuthority,
        SourceType,
    )
    from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore

    class Resolver:
        def resolve(self, symbol: str):
            source = PrimarySource(
                symbol="DIS",
                company="Walt Disney Co",
                source_type=SourceType.ANNUAL_REPORT,
                identifier="10-K 0001744489-25-000155",
                key="0001744489-25-000155",
                published_on=date(2025, 11, 13),
                reporting_period=None,
                document_format="html",
                language="en",
                location="https://www.sec.gov/Archives/example",
                provider="SEC EDGAR",
                authority=SourceAuthority.REGULATOR_FILED,
                verification=(IdentityCheck.REGISTER_INDEXED,),
            )

            return (source, None)

    outcome = await CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path),
        sources=Resolver(),  # type: ignore[arg-type]
    ).knowledge("DIS")

    assert outcome.state is KnowledgeState.UNAVAILABLE
    assert outcome.knowledge is None
    assert "has not been read" in (outcome.absent_because or "")
    assert "knowledge reader" in (outcome.absent_because or "")
