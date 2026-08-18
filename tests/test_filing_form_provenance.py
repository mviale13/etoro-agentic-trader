"""The SEC form is data, and it survives the whole path.

`ANNUAL_SECTION_READER_CUTOVER_MEASUREMENT.md` measured that every
production read reached the section reader with `form=""`: the form
travelled only as a string prefix inside `identifier`, and `read_url` —
the single path production takes — built its reference from a URL and
discarded everything else. So no form-aware dispatch could honestly be
written above it.

This slice carries the form and changes nothing else. Every test below
either pins the form's survival or pins that a reading did not move.
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.providers.edgar_filings import (
    AMENDED_ANNUAL_FORMS,
    ANNUAL_FORMS,
    EdgarFilings,
    FilingReference,
    normalized_form,
)
from app.providers.edgar_provider import EdgarProvider
from app.repositories.source_codec import decode_source, encode_source

ROOT = Path(__file__).resolve().parents[1]


def reference(form: str, accession: str = "0000320193-25-000079") -> FilingReference:
    return FilingReference(
        company="Apple Inc.",
        form=form,
        filed_on=date(2025, 11, 1),
        accession=accession,
        url=f"https://www.sec.gov/Archives/edgar/data/320193/{accession}/x.htm",
    )


class Filings:
    """An `EdgarFilings` that answers from a script and records the form."""

    def __init__(self, latest: FilingReference | None = None) -> None:
        self._latest = latest or reference("10-K")
        self.read_url_calls: list[tuple[str, str]] = []
        self.read_forms: list[str] = []

    def latest_reference(self, symbol: str) -> FilingReference:
        return self._latest

    def read_url(self, url: str, form: str = ""):
        self.read_url_calls.append((url, form))

        return _Filing()

    def read(self, ref: FilingReference):
        self.read_forms.append(ref.form)

        return _Filing()


class _Filing:
    business_text = ""
    business_regions = ()
    discussion_text = ""
    discussion_tables = ()
    income_statement_text = ""
    income_statement_tables = ()
    balance_sheet_text = ""
    balance_sheet_tables = ()
    cash_flow_text = ""
    cash_flow_tables = ()
    income_statement_contenders = 0
    balance_sheet_contenders = 0
    cash_flow_contenders = 0
    reference = reference("10-K")


# ── the form as data ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        ("10-K", "10-K"),
        ("20-F", "20-F"),
        ("10-K/A", "10-K/A"),
        ("20-F/A", "20-F/A"),
        ("8-K", "8-K"),
        ("6-K", "6-K"),
        ("  10-k ", "10-K"),
        ("20-f/a", "20-F/A"),
        ("", ""),
    ],
)
def test_the_regulators_designation_is_normalised_for_case_and_space_only(
    printed, expected
) -> None:
    """`10-K` and `10-K/A` are different documents and must stay so.

    Normalising further — stripping the amendment suffix, mapping an
    unknown form onto a known one — would be exactly the inference this
    field exists to remove.
    """

    assert normalized_form(printed) == expected


def test_an_unfamiliar_real_form_survives_rather_than_being_mapped() -> None:
    """A form this platform has no mapping for is still recorded as itself."""

    for real in ("11-K", "40-F", "S-1", "DEF 14A", "6-K"):
        assert normalized_form(real) == real.upper()


# ── the form survives the whole path ────────────────────────────────


@pytest.mark.parametrize("form", ["10-K", "20-F", "8-K", "10-K/A", "20-F/A"])
def test_the_form_reaches_the_source_and_then_the_reader(form) -> None:
    """discovery → FilingReference → PrimarySource → fetch → read_url."""

    filings = Filings(latest=reference(form))
    provider = EdgarProvider(filings=filings)

    source = provider.resolve("AAPL")

    assert source.form == form, "the source lost the form"
    assert source.is_form_classified

    provider.fetch(source)

    url, passed = filings.read_url_calls[-1]

    assert passed == form, "read_url was not told the form"
    assert url == source.location


def test_read_url_no_longer_manufactures_a_blank_form() -> None:
    """The defect this slice repairs, pinned at the boundary it lived on.

    `read_url` used to construct `FilingReference(form="")` regardless of
    what its caller knew, and it is the only path production takes.
    """

    seen: list[str] = []

    class Reading(EdgarFilings):
        def _get(self, url):  # noqa: ANN001, ANN202
            class Response:
                text = "<html><body><p>nothing</p></body></html>"

            return Response()

        def _read(self, reference, document):  # noqa: ANN001, ANN202
            seen.append(reference.form)

            return _Filing()

    Reading().read_url("https://example.invalid/x.htm", form="20-F")

    assert seen == ["20-F"]


def test_a_caller_that_knows_nothing_still_passes_nothing() -> None:
    """No inference from the URL, the filename or anything else."""

    seen: list[str] = []

    class Reading(EdgarFilings):
        def _get(self, url):  # noqa: ANN001, ANN202
            class Response:
                text = "<html><body><p>nothing</p></body></html>"

            return Response()

        def _read(self, reference, document):  # noqa: ANN001, ANN202
            seen.append(reference.form)

            return _Filing()

    Reading().read_url("https://www.sec.gov/Archives/.../aapl-10k_20250927.htm")

    assert seen == [""], "a form was inferred from the address"


def test_the_form_is_never_parsed_back_out_of_a_label() -> None:
    """`identifier` carries the form as text; nothing may read it there.

    Searched in the source, because the next such parse would arrive as
    a `split()` inside a helper and an import graph would not see it.
    """

    guarded = (
        ROOT / "app/providers/edgar_provider.py",
        ROOT / "app/providers/edgar_filings.py",
        ROOT / "app/repositories/source_codec.py",
        ROOT / "app/domain/primary_source.py",
    )

    for path in guarded:
        source = path.read_text()

        for parse in (
            "identifier.split",
            "identifier.partition",
            "identifier[:",
            "identifier.startswith",
            "location.split",
            "url.split",
        ):
            assert parse not in source, f"{path.name} parses a label: {parse}"


def test_a_non_sec_source_stays_unclassified_rather_than_guessed() -> None:
    """An ESEF package and an issuer's own report carry no SEC form."""

    unclassified = PrimarySource(
        symbol="NESN.SW",
        company="Nestlé S.A.",
        source_type=SourceType.ANNUAL_REPORT,
        identifier="ESEF 2025",
        key="hash",
        published_on=date(2026, 3, 1),
        reporting_period=None,
        document_format="xhtml",
        language="en",
        location="https://example.invalid/report.xhtml",
        provider="ESEF",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.DOCUMENT_LEI,),
    )

    assert unclassified.form == ""
    assert not unclassified.is_form_classified


def test_the_form_round_trips_through_the_store() -> None:
    source = PrimarySource(
        symbol="AAPL",
        company="Apple Inc.",
        source_type=SourceType.ANNUAL_REPORT,
        identifier="10-K 0000320193-25-000079",
        key="0000320193-25-000079",
        published_on=date(2025, 11, 1),
        reporting_period=None,
        document_format="html",
        language="en",
        location="https://example.invalid/x.htm",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
        form="10-K",
    )

    assert encode_source(source)["form"] == "10-K"
    assert decode_source(encode_source(source)) == source


def test_a_record_written_before_the_field_decodes_as_unclassified() -> None:
    """Absent is unclassified. Decoding never repairs."""

    stored = encode_source(
        PrimarySource(
            symbol="AAPL",
            company="Apple Inc.",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 0000320193-25-000079",
            key="k",
            published_on=date(2025, 11, 1),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://example.invalid/x.htm",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(),
            form="10-K",
        )
    )
    del stored["form"]

    assert decode_source(stored).form == ""
    assert not decode_source(stored).is_form_classified


# ── amendments stay out of selection ────────────────────────────────


def test_latest_annual_selection_still_excludes_amendments() -> None:
    """Measured: an amendment does not contain the business section.

    Disney's and Tesla's `10-K/A` print only Items 10-15; Barclays'
    `20-F/A` only Items 17-18. Selected as the latest annual report,
    either would be a document with no business description in it.
    """

    assert ANNUAL_FORMS == ("10-K", "20-F")

    for amended in AMENDED_ANNUAL_FORMS:
        assert amended not in ANNUAL_FORMS

    assert AMENDED_ANNUAL_FORMS == ("10-K/A", "20-F/A")


def test_an_amendment_read_explicitly_still_carries_its_own_form() -> None:
    """Excluded from *selection* is not the same as unreadable."""

    for amended in AMENDED_ANNUAL_FORMS:
        filings = Filings(latest=reference(amended))
        source = EdgarProvider(filings=filings).resolve("DIS")

        assert source.form == amended

        EdgarProvider(filings=filings).fetch(source)

        assert filings.read_url_calls[-1][1] == amended


# ── zero behaviour change ───────────────────────────────────────────


def test_the_dispatch_is_an_equality_against_exactly_one_form() -> None:
    """Superseded by the exact 10-K cutover, and inverted rather than deleted.

    When this slice shipped it asserted that `_read` consulted no
    locator, because carrying the form and reading it were deliberately
    separate PRs. The reading has since been ruled and built, so what
    matters now is *how* the form is read: an equality against one
    normalised value, and nothing looser.
    """

    section = (ROOT / "app/providers/edgar_filings.py").read_text()

    body = section[section.index("def _read(") :]
    body = body[: body.index("\n    @staticmethod")]

    assert 'normalized_form(reference.form) == "10-K"' in body

    # The three ways a looser match would let the wrong document through.
    assert "startswith" not in body, "a prefix match would admit 10-K/A"
    assert "in ANNUAL_FORMS" not in body, "membership would admit 20-F"
    assert 'replace("/A"' not in body and 'rstrip("/A")' not in body

    # Both paths are present: the located one and the legacy one.
    assert "self._located(" in body
    assert "_ITEM_1" in body and "_ITEM_7" in body, "the legacy path must remain"


def test_the_item_anchors_are_untouched() -> None:
    from app.providers.edgar_filings import _ITEM_1, _ITEM_1A, _ITEM_7, _ITEM_7A

    assert _ITEM_1 == ("item 1.", "item 1 ", "item 1:")
    assert _ITEM_1A == ("item 1a.", "item 1a ", "item 2.", "item 2 ")
    assert _ITEM_7 == ("item 7.", "item 7 ", "item 7:")
    assert _ITEM_7A[:2] == ("item 7a.", "item 7a ")


def test_every_constructor_still_passes_keywords() -> None:
    """The field is last and defaulted; nothing positional may appear.

    Audited across the whole tree rather than trusted to test discovery:
    a positional construction added later would silently take the form's
    slot.
    """

    positional = []

    for path in [*(ROOT / "app").rglob("*.py"), *(ROOT / "tests").rglob("*.py")]:
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - not expected in-tree
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ("PrimarySource", "FilingReference")
                and node.args
            ):
                positional.append(f"{path.name}:{node.lineno}")

    assert positional == [], positional


def test_the_form_now_selects_the_reader_and_only_for_exact_10_k() -> None:
    """Superseded: the form was inert here, and now it chooses the reader.

    This test used to assert that one document read under every form
    produced one identical result, which was the mechanism behind #207's
    byte-identity. The exact 10-K cutover changes that on purpose — and
    only for `10-K`. So the assertion becomes the cutover's own contract:
    every other form, including both amendments, the blank and an
    unfamiliar one, still reads identically to each other.
    """

    markup = (
        "<p>Item 1. Business 3</p><p>Item 1A. Risk Factors 9</p>"
        "<p>ITEM\xa01. BUSINESS</p>" + "<p>" + "What it does. " * 400 + "</p>"
        "<p>ITEM\xa01A. RISK FACTORS</p>" + "<p>" + "Risks. " * 400 + "</p>"
        "<p>ITEM\xa07. MANAGEMENT'S DISCUSSION</p>" + "<p>" + "Results. " * 400 + "</p>"
        "<p>ITEM\xa07A. QUANTITATIVE</p>" + "<p>" + "Risk. " * 400 + "</p>"
    )

    class Reading(EdgarFilings):
        def _get(self, url):  # noqa: ANN001, ANN202
            class Response:
                text = markup

            return Response()

    legacy_forms = ("", "20-F", "10-K/A", "20-F/A", "8-K", "NOT-A-FORM")

    read = {
        form: Reading().read_url("https://example.invalid/x.htm", form=form)
        for form in (*legacy_forms, "10-K")
    }

    business = {read[form].business_text for form in legacy_forms}
    discussion = {read[form].discussion_text for form in legacy_forms}

    assert len(business) == 1, "the form changed a legacy reading"
    assert len(discussion) == 1, "the form changed a legacy discussion"

    # Every legacy form keeps the reading exactly as it was, defects
    # included: the literal reader takes this document's contents entry
    # rather than its body, and misses the discussion entirely because
    # the closing anchor is matched against a non-breaking space.
    assert business.pop() == "Item 1. Business 3"
    assert discussion.pop() == ""

    # And exactly `10-K` now reads the body instead.
    assert read["10-K"].business_text.startswith("ITEM\xa01. BUSINESS")
    assert "What it does" in read["10-K"].business_text
    assert read["10-K"].discussion_text.startswith("ITEM\xa07.")

    # And the form still arrived, so this is not identity by ignorance.
    assert read["20-F"].reference.form == "20-F"
    assert read[""].reference.form == ""


def test_no_decision_bearing_module_reads_the_form() -> None:
    """Provenance is carried for a future dispatch and consumed by nothing.

    Searched in the source of every area a form must not reach. The two
    providers that populate or forward it are exempt by name; everything
    else must not mention it.
    """

    allowed = {
        "providers/edgar_provider.py",
        "providers/edgar_filings.py",
        "repositories/source_codec.py",
        "domain/primary_source.py",
    }
    forbidden_areas = (
        "services/business_quality",
        "domain/business_quality",
        "services/recommendation",
        "domain/recommendation",
        "application/committees",
        "committee",
        "services/artificial_cio",
        "domain/decision",
        "services/decision",
        "application/brain",
        "analysts",
    )

    offenders = []

    for path in (ROOT / "app").rglob("*.py"):
        relative = str(path.relative_to(ROOT / "app"))

        if relative in allowed:
            continue

        if not any(relative.startswith(area) for area in forbidden_areas):
            continue

        source = path.read_text()

        if "source.form" in source or ".is_form_classified" in source:
            offenders.append(relative)

    assert offenders == [], offenders
