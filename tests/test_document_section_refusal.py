"""An empty section is not a fact about a company.

Barclays' 20-F is 3.7 million characters of a real annual report and
Citigroup's 10-K is 1.53 million; both used to hand a surface an empty
string, and a surface that expects prose renders that as *"the company
describes no business"* — a claim about the filer produced by a limit of
this reader.

Every case below either pins which of four things happened, or pins that
saying so cost nothing else.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import date

import pytest

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.section_refusal import RefusedSection, SectionRefusal
from app.providers.edgar_filings import EdgarFilings, FilingReference
from app.repositories.source_codec import decode_source, encode_source
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeState,
)

REFERENCE = FilingReference(
    company="Example Corp",
    form="10-K",
    filed_on=date(2026, 2, 13),
    accession="0000000000-26-000001",
    url="https://example.invalid/10k.htm",
)

BODY = "Consumer Banking offers deposit products through branches. " * 300


def filing(document: str, form: str = "10-K"):
    return EdgarFilings()._read(replace(REFERENCE, form=form), document)  # noqa: SLF001


# ── the sixth state ─────────────────────────────────────────────────


def test_the_new_state_is_neither_available_nor_worth_retrying() -> None:
    """Nothing failed and nothing is intermittent.

    The filing says what it says, and the same request is refused for the
    same structural reason until a capability changes — not until a
    retry succeeds.
    """

    refused = KnowledgeState.DOCUMENT_REFUSED

    assert not refused.is_available
    assert not refused.may_succeed_later
    assert refused is not KnowledgeState.UNAVAILABLE
    assert refused is not KnowledgeState.PROVIDER_ERROR
    assert refused is not KnowledgeState.INVALID_EXTRACTION


def test_the_five_existing_states_are_unchanged() -> None:
    """The sixth member may not move any of the five."""

    expected = {
        KnowledgeState.AVAILABLE_CACHED: (True, False),
        KnowledgeState.AVAILABLE_ACQUIRED: (True, False),
        KnowledgeState.UNAVAILABLE: (False, False),
        KnowledgeState.PROVIDER_ERROR: (False, True),
        KnowledgeState.INVALID_EXTRACTION: (False, False),
    }

    for state, (available, later) in expected.items():
        assert state.is_available is available, state
        assert state.may_succeed_later is later, state

    assert len(KnowledgeState) == 6


# ── the producer ────────────────────────────────────────────────────


def test_a_cross_reference_index_is_the_conjunction_and_not_the_phrase() -> None:
    """Citigroup's shape: an index of item numbers against page ranges.

    Both halves are required. Measured over the 24 held annual reports:
    Fifth Third prints the phrase twice and Honeywell three times, and
    both print their sections — so the phrase alone would refuse two
    perfectly readable filings.
    """

    document = (
        "<html><body>"
        "<p>FORM 10-K CROSS-REFERENCE INDEX Item Number Page</p>"
        "<p>1. Business 4-36, 121-127 1A. Risk Factors 49-62</p>"
        f"<p>{BODY}</p>"
        "</body></html>"
    )

    read = filing(document)

    assert read.business_text == ""
    assert read.business_refusal is not None
    assert read.business_refusal.reason is SectionRefusal.CROSS_REFERENCE_INDEX


def test_the_phrase_alone_does_not_refuse_a_filing_that_prints_its_sections() -> None:
    """Fifth Third's and Honeywell's shape, reduced."""

    document = (
        "<html><body>"
        "<p>See Form 10-K Cross-Reference Index for a cross-reference.</p>"
        "<p>ITEM 1. BUSINESS</p>"
        f"<p>{BODY}</p>"
        "<p>ITEM 1A. RISK FACTORS</p>"
        f"<p>{BODY}</p>"
        "</body></html>"
    )

    read = filing(document)

    assert read.business_text.startswith("ITEM 1. BUSINESS")
    assert read.business_refusal is None


def test_a_filing_printing_no_candidate_and_no_index_says_so() -> None:
    document = (
        "<html><body><p>A report with no numbered items.</p>"
        f"<p>{BODY}</p></body></html>"
    )

    read = filing(document)

    assert read.business_refusal is not None
    assert read.business_refusal.reason is SectionRefusal.EXPECTED_SECTION_NOT_PRINTED
    assert "No Item 1 heading occurs" in read.business_refusal.observed


def test_candidates_that_never_resolve_are_a_location_refusal() -> None:
    """A filing that printed the section and a reader that could not settle it.

    Distinct from the case above on purpose: one is the filer's doing and
    the other is this platform's.
    """

    document = (
        "<html><body>"
        "<p>Risks are set forth in Item 1 of this report.</p>"
        "<p>See Item 1 for more, and refer to Item 1 again.</p>"
        "</body></html>"
    )

    read = filing(document)

    assert read.business_refusal is not None
    assert read.business_refusal.reason is SectionRefusal.SECTION_LOCATION_REFUSED
    assert "were discovered and none resolved" in read.business_refusal.observed


def test_the_two_sections_refuse_independently() -> None:
    """A filing may print one and not the other.

    Refusing both because one is missing would report this reader's
    coupling as the filer's silence.
    """

    document = (
        "<html><body>"
        "<p>ITEM 1. BUSINESS</p>"
        f"<p>{BODY}</p>"
        "<p>ITEM 1A. RISK FACTORS</p>"
        f"<p>{BODY}</p>"
        "</body></html>"
    )

    read = filing(document)

    assert read.business_text
    assert read.business_refusal is None
    assert read.discussion_refusal is not None, "Item 7 is absent and must say so"


def test_a_form_on_the_legacy_path_produces_no_refusal_yet() -> None:
    """20-F dispatch is a later slice; this carrier does not anticipate it."""

    document = "<html><body><p>Nothing numbered at all.</p></body></html>"

    for form in ("20-F", "10-K/A", "8-K", ""):
        assert filing(document, form=form).business_refusal is None


def test_the_producer_names_no_company() -> None:
    """No symbol branch — measured against what the module *executes*.

    The prose above the detector names Citigroup, Barclays and NatWest in
    order to say where their wordings came from, and a substring search
    over the file would call that explanation a branch.
    """

    import ast
    import pathlib

    tree = ast.parse(pathlib.Path("app/providers/edgar_filings.py").read_text())

    docstrings = set()

    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)

            if doc is not None:
                docstrings.add(doc)

    executed = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]

    for symbol in ("citigroup", "barclays", "natwest", "bcs", "nwg", "mufg"):
        offenders = [text for text in executed if symbol in text.casefold()]

        assert offenders == [], f"{symbol}: {offenders}"


# ── the wording ─────────────────────────────────────────────────────


def refusal(reason: SectionRefusal) -> RefusedSection:
    return RefusedSection(
        reason=reason,
        expected="business description",
        form="10-K",
        filing="0000831001-26-000011",
        observed="The filing prints no Item 1 heading.",
    )


@pytest.mark.parametrize("reason", list(SectionRefusal))
def test_no_refusal_ever_makes_a_claim_about_the_company(reason) -> None:
    """Six phrasings the ruling forbids, checked on every member."""

    stated = refusal(reason).stated().casefold()

    for banned in (
        "no provider",
        "describes no business",
        "contains no business information",
        "try again",
        "another provider",
        "retry",
    ):
        assert banned not in stated, f"{reason}: {banned}"


def test_the_cross_reference_wording_says_what_was_not_followed() -> None:
    stated = refusal(SectionRefusal.CROSS_REFERENCE_INDEX).stated()

    assert "is available" in stated
    assert "cross-reference index" in stated
    assert "did not follow those page or component references" in stated
    assert "Nothing follows from this about what the company does." in stated


@pytest.mark.parametrize("reason", list(SectionRefusal))
def test_every_reason_names_the_filing_and_disclaims_a_company_claim(reason) -> None:
    stated = refusal(reason).stated()

    assert "business description" in stated
    assert "Nothing follows from this about what the company does." in stated


# ── the consumer ────────────────────────────────────────────────────


def source_for(symbol: str = "C") -> PrimarySource:
    return PrimarySource(
        symbol=symbol,
        company="Citigroup Inc.",
        source_type=SourceType.ANNUAL_REPORT,
        identifier="10-K 0000831001-26-000011",
        key="0000831001-26-000011",
        published_on=date(2026, 2, 20),
        reporting_period=None,
        document_format="html",
        language="en",
        location="https://example.invalid/c.htm",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
        form="10-K",
    )


class Provider:
    name = "SEC EDGAR"

    def __init__(self, document: SourceDocument) -> None:
        self._document = document

    def resolve(self, symbol: str) -> PrimarySource:
        return self._document.source

    def fetch(self, source: PrimarySource) -> SourceDocument:
        return self._document


class Sources:
    def __init__(self, provider: Provider) -> None:
        self._provider = provider

    def resolve(self, symbol: str):
        return self._provider.resolve(symbol), self._provider


class Exploding:
    """An extractor that fails the test if it is ever reached."""

    async def extract(self, symbol, document):  # noqa: ANN001, ANN202
        raise AssertionError("a refused section reached the model")


def refused_document() -> SourceDocument:
    return SourceDocument(
        source=source_for(),
        business_description="",
        performance_discussion="",
        business_refusal=refusal(SectionRefusal.CROSS_REFERENCE_INDEX),
    )


def test_a_refused_section_never_reaches_the_model(tmp_path) -> None:
    """`observe` spends to the quorum; a refusal must stop before it."""

    from app.repositories.company_knowledge_store import (
        JsonCompanyKnowledgeStore,
    )

    store = JsonCompanyKnowledgeStore(tmp_path)
    service = CompanyKnowledgeService(
        store=store,
        sources=Sources(Provider(refused_document())),
        extractor=Exploding(),
    )

    outcome = asyncio.run(service.knowledge("C"))

    assert outcome.state is KnowledgeState.DOCUMENT_REFUSED
    assert outcome.absent_because
    assert "cross-reference index" in outcome.absent_because
    assert store.read("C", "0000831001-26-000011") == ()

    spent = asyncio.run(service.observe("C"))

    assert spent.state is KnowledgeState.DOCUMENT_REFUSED
    assert store.read("C", "0000831001-26-000011") == ()


def test_a_refusal_is_not_an_invalid_extraction() -> None:
    """Nothing was extracted, nothing failed grounding, nothing is stored."""

    assert KnowledgeState.DOCUMENT_REFUSED is not KnowledgeState.INVALID_EXTRACTION


# ── the carrier ─────────────────────────────────────────────────────


def test_a_document_may_refuse_a_section_and_still_carry_statements() -> None:
    """Citigroup's combination, and it is legitimate rather than tolerated."""

    document = SourceDocument(
        source=source_for(),
        business_description="",
        performance_discussion="",
        business_refusal=refusal(SectionRefusal.CROSS_REFERENCE_INDEX),
        income_statement_text="Revenues …",
        balance_sheet_text="Assets …",
        cash_flow_text="Operating activities …",
    )

    assert document.business_refusal is not None
    assert document.income_statement_text
    assert document.balance_sheet_text
    assert document.cash_flow_text


def test_the_carriers_default_to_absent_and_every_constructor_is_keyword_safe() -> None:
    import ast
    import pathlib

    document = SourceDocument(source=source_for(), business_description="x")

    assert document.business_refusal is None
    assert document.discussion_refusal is None

    positional = []
    root = pathlib.Path(".")

    for path in [*(root / "app").rglob("*.py"), *(root / "tests").rglob("*.py")]:
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "SourceDocument"
                and node.args
            ):
                positional.append(f"{path.name}:{node.lineno}")

    assert positional == [], positional


def test_an_older_stored_source_still_decodes() -> None:
    """The carriers live on the document, never on the stored identity."""

    stored = encode_source(source_for())

    assert "business_refusal" not in stored
    assert decode_source(stored) == source_for()
