"""A named segment, asked against the package's untagged prose (E1).

The measured defect: Volkswagen's package ships its division
descriptions in a management report carrying no XBRL tag, so a reading
scoped to tagged blocks reported five times out of five that nothing
describes the segments — honestly, about text that genuinely printed
nothing. The repair keys on the *document pattern* — an untagged
package member, a segment name the filer's own prose uses — never on a
company, a language or an industry.
"""

import asyncio
import io
import json
import zipfile
from datetime import date

from app.domain.company_knowledge import RevenueModel
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.providers.esef_filings import read_package
from app.providers.narrative_provider import Draft, DraftRequest
from app.services.company_knowledge_extractor import (
    SUPPLEMENTAL_SYSTEM_PROMPT,
    CompanyKnowledgeExtractor,
    named_passage,
)

# ── the passage builder ────────────────────────────────────────────────


def test_a_passage_is_the_prose_around_the_filers_own_uses_of_the_name() -> None:
    text = (
        "Preamble about governance. "
        * 20
        + "The Widgets division makes industrial widgets and sells them "
        "to manufacturers. "
        + "Unrelated remuneration prose. " * 50
        + "Widgets grew strongly this year. "
        + "Closing remarks. " * 20
    )

    passage, truncated = named_passage(text, "Widgets", radius=60)

    assert "makes industrial widgets" in passage
    assert "grew strongly" in passage
    assert not truncated


def test_a_digit_dense_region_is_not_prose_about_the_segment() -> None:
    """A delivery table headed by the name is dropped, not read."""

    table = "Widgets 8.678.334 8.692.465 0,2 305.566 334.216 8,6 " * 8
    prose = "The Widgets division makes industrial widgets. "

    text = table + ("filler words here. " * 200) + prose

    passage, _ = named_passage(text, "Widgets", radius=50)

    assert "makes industrial widgets" in passage
    assert "8.678.334" not in passage


def test_the_cap_is_reported_rather_than_silent() -> None:
    text = ("The Widgets division does many things. " + "x" * 400 + " ") * 30

    passage, truncated = named_passage(text, "Widgets", radius=200, cap=1000)

    assert truncated
    assert len(passage) <= 1000


def test_a_name_the_prose_never_uses_yields_nothing() -> None:
    passage, truncated = named_passage("Entirely unrelated text.", "Widgets")

    assert passage == ""
    assert not truncated


# ── the package capture: pattern, not company ─────────────────────────


def _xhtml(body: str, *, lei: str | None = None, tagged: bool = False) -> str:
    """A minimal package member: tagged notes, or an untagged report."""

    contexts = (
        f"""<xbrli:context id="c1"><xbrli:entity>
        <xbrli:identifier scheme="http://standards.iso.org/iso/17442">{lei}</xbrli:identifier>
        </xbrli:entity><xbrli:period>
        <xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>"""
        if lei
        else ""
    )

    facts = (
        """<ix:nonNumeric name="ifrs-full:DisclosureOfOperatingSegmentsExplanatory"
        contextRef="c1">The reportable segments are Alpha Division and Beta
        Division.</ix:nonNumeric>"""
        if tagged
        else ""
    )

    return f"""<html xmlns:ix="i" xml:lang="fr"><head></head><body>
    {contexts}{facts}<p>{body}</p></body></html>"""


def _package(*members: str) -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        for index, member in enumerate(members):
            archive.writestr(f"reports/part{index}.xhtml", member)

    return buffer.getvalue()


DESCRIPTION_PROSE = (
    "Rapport de gestion. La division Alpha Division conçoit et vend des "
    "turbines industrielles aux compagnies d'électricité. La division "
    "Beta Division fournit des services de maintenance sous contrat."
)


def test_an_untagged_package_member_contributes_its_prose() -> None:
    """The pattern fires on package structure — a French filer's shape
    here, Volkswagen's in the corpus — never on a company identity."""

    package = _package(
        _xhtml("Notes.", lei="FRLEI000000000000001", tagged=True),
        _xhtml(DESCRIPTION_PROSE),
    )

    report = read_package(package)

    assert "Alpha Division and Beta" in report.business_text
    assert "turbines industrielles" in report.unstructured_text
    # The tagged member contributes nothing to the untagged text.
    assert "reportable segments" not in report.unstructured_text


def test_a_single_document_package_captures_nothing_extra() -> None:
    """A filer whose tagged blocks already speak is read exactly as
    before — the scope expands only where the measured pattern exists."""

    package = _package(
        _xhtml("All in one file.", lei="FRLEI000000000000001", tagged=True),
    )

    report = read_package(package)

    assert report.unstructured_text == ""


# ── the supplemental reading ──────────────────────────────────────────


def source_document(unstructured: str) -> SourceDocument:
    return SourceDocument(
        source=PrimarySource(
            symbol="EXAM.PA",
            company="Exemple SA",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="exam-2025",
            key="abc123",
            published_on=date(2026, 3, 1),
            reporting_period=None,
            document_format="xhtml",
            language="fr",
            location="https://example.invalid/report.zip",
            provider="ESEF",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        business_description=(
            "The reportable segments are Alpha Division and Beta Division."
        ),
        unstructured_text=unstructured,
    )


class ScriptedProvider:
    """Answers each request in turn, and remembers what was asked."""

    name = "Scripted"
    model = "scripted-1"

    def __init__(self, payloads: list[object]) -> None:
        self._payloads = list(payloads)
        self.requests: list[DraftRequest] = []

    async def draft(self, request: DraftRequest) -> Draft:
        self.requests.append(request)

        return Draft(
            text=json.dumps(self._payloads.pop(0)),
            model=self.model,
            usage=None,
        )


PRIMARY_PAYLOAD = {
    "description": "An industrial group.",
    "segments": [
        {"name": "Alpha Division", "revenue_models": [], "quoted": ""},
    ],
}

EMPTY_FOLLOW_UP = {"quoted": ""}


def test_a_wordless_segment_is_asked_against_the_untagged_prose() -> None:
    provider = ScriptedProvider(
        [
            PRIMARY_PAYLOAD,
            EMPTY_FOLLOW_UP,  # asked by name against the tagged text: none
            {  # supplemental, against the untagged prose: found
                "quoted": "conçoit et vend des turbines industrielles",
                "revenue_models": ["manufacturing"],
            },
        ]
    )

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            source_document(DESCRIPTION_PROSE),
        )
    )

    segment = knowledge.segments[0]

    assert segment.description is not None
    assert segment.revenue_models == (RevenueModel.MANUFACTURING,)

    # Never presented as a first reading: the repair provenance names
    # the untagged text as where the words were found.
    assert segment.description.repair is not None
    assert "untagged report text" in segment.description.repair.first_refused_because

    # The supplemental ask carried its own contract, not the repair's.
    assert provider.requests[-1].system_prompt == SUPPLEMENTAL_SYSTEM_PROMPT


def test_a_span_the_prose_does_not_print_is_refused() -> None:
    provider = ScriptedProvider(
        [
            PRIMARY_PAYLOAD,
            EMPTY_FOLLOW_UP,
            {
                # Not printed in the French prose below.
                "quoted": "designs and sells industrial turbines",
                "revenue_models": ["manufacturing"],
            },
        ]
    )

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            source_document(DESCRIPTION_PROSE),
        )
    )

    segment = knowledge.segments[0]

    assert segment.description is None
    assert segment.revenue_models == ()
    assert "refused" in (segment.undescribed_because or "")


def test_an_honest_empty_supplemental_answer_is_recorded_with_both_reasons() -> None:
    provider = ScriptedProvider(
        [
            PRIMARY_PAYLOAD,
            EMPTY_FOLLOW_UP,
            {"quoted": "", "revenue_models": []},
        ]
    )

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            source_document(DESCRIPTION_PROSE),
        )
    )

    segment = knowledge.segments[0]

    assert segment.description is None
    assert "untagged report text" in (segment.undescribed_because or "")


def test_a_document_without_untagged_prose_is_never_asked_the_question() -> None:
    """The EDGAR shape: no unstructured text, no supplemental request.
    Two asks — the primary and the by-name follow-up — and no third."""

    provider = ScriptedProvider([PRIMARY_PAYLOAD, EMPTY_FOLLOW_UP])

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            source_document(""),
        )
    )

    assert len(provider.requests) == 2
    assert knowledge.segments[0].description is None


def test_a_name_the_untagged_prose_never_uses_is_answered_without_a_model() -> None:
    provider = ScriptedProvider([PRIMARY_PAYLOAD, EMPTY_FOLLOW_UP])

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            source_document("Prose that never names the division at all."),
        )
    )

    # No third request was spent on a passage that does not exist.
    assert len(provider.requests) == 2
    assert "prints no prose around the filer's own uses" in (
        knowledge.segments[0].undescribed_because or ""
    )
