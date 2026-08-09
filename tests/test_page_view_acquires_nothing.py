"""A page view reads what has been acquired, and acquires nothing.

The per-security research path runs once for every holding and every
research candidate, on every page an investor opens. It used to reach the
knowledge layer through `knowledge()`, which resolves the company's
current filing against a regulator before it can answer anything — and
reads that filing, through a model, whenever the store has not seen it.

So opening a dossier put a network round trip per security behind the
page, and a company that had just filed put a model call behind it. The
read-only door existed the whole time and said so in its own docstring;
this proves the page now uses it.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services import company_knowledge_service as knowledge_module
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeState,
)
from app.services.company_research_service import CompanyResearchService
from tests.test_company_knowledge_service import (
    ExtractorStub,
    ProviderStub,
    ResolverStub,
    knowledge,
)
from tests.test_company_research_service_pipeline import make_company


def make_service(
    tmp_path: Path,
    provider: ProviderStub,
    extractor: ExtractorStub,
) -> CompanyResearchService:
    """The real research path over a knowledge layer that counts."""

    return CompanyResearchService(
        knowledge_service=CompanyKnowledgeService(
            store=JsonCompanyKnowledgeStore(tmp_path),
            sources=ResolverStub(provider),  # type: ignore[arg-type]
            extractor=extractor,  # type: ignore[arg-type]
        )
    )


def test_a_page_view_resolves_no_filing_and_reads_none(tmp_path: Path) -> None:
    """The measurement this exists for: no regulator, no model, no spend."""

    provider = ProviderStub()
    extractor = ExtractorStub()

    research = asyncio.run(
        make_service(tmp_path, provider, extractor).analyze(make_company())
    )

    # The door was opened — this security's playbook does expect company
    # accounts — and opening it cost no lookup, no document and no reading.
    assert research.knowledge_state is not None

    assert provider.lookups == 0
    assert provider.documents_read == 0
    assert extractor.extractions == 0


def test_a_page_view_serves_the_filing_already_read(tmp_path: Path) -> None:
    """What was acquired is served — the door is read-only, not blind."""

    provider = ProviderStub()
    extractor = ExtractorStub()

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.append(knowledge())

    service = CompanyResearchService(
        knowledge_service=CompanyKnowledgeService(
            store=store,
            sources=ResolverStub(provider),  # type: ignore[arg-type]
            extractor=extractor,  # type: ignore[arg-type]
        )
    )

    research = asyncio.run(
        service.analyze(replace(make_company(), symbol="DIS", name="Walt Disney Co"))
    )

    assert research.knowledge is not None
    assert research.knowledge_state == KnowledgeState.AVAILABLE_CACHED.value

    # Served from the store alone. The consensus is over the newest filing
    # this platform has actually observed, which is a different claim from
    # the newest filing that exists — and one the page can make offline.
    assert provider.lookups == 0


def test_a_company_never_read_says_so_and_names_the_spend(tmp_path: Path) -> None:
    """An absence carries its reason, and the reason is not a failure."""

    outcome = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path),
        sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
        extractor=ExtractorStub(),  # type: ignore[arg-type]
    ).established("DIS")

    assert outcome.state is KnowledgeState.UNAVAILABLE
    assert outcome.knowledge is None
    assert "movrvest observe" in (outcome.absent_because or "")


def test_no_reader_is_composed_until_a_filing_is_actually_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Composing the reader resolves credentials into a live model client.

    A page builds this service once per security and only ever opens the
    read-only door, so paying to compose a reader there is paid for
    nothing — thirteen times a page view, measured. The two doors that
    can actually read a filing ask for it; nothing else does.
    """

    composed = 0

    def counting_resolve_reader() -> ExtractorStub:
        nonlocal composed
        composed += 1

        return ExtractorStub()

    monkeypatch.setattr(
        knowledge_module,
        "resolve_reader",
        counting_resolve_reader,
    )

    service = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path),
        sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
    )

    service.established("DIS")

    assert composed == 0

    asyncio.run(service.knowledge("DIS"))

    assert composed == 1

    # And composed once, not once per question asked.
    asyncio.run(service.knowledge("DIS"))

    assert composed == 1
