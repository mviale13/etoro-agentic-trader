"""What happened on every explicit company-knowledge attempt, persisted.

The measurement that earned this (`SECURITY_SPECIFIC_EVIDENCE_SUFFICIENCY.md`):
`CompanyKnowledgeService.established()` — the read-only door every
decision path uses — can return only `AVAILABLE_CACHED` or
`UNAVAILABLE`. `PROVIDER_ERROR`, `INVALID_EXTRACTION` and
`DOCUMENT_REFUSED` were computed at acquisition and **discarded**, and a
search of the whole evidence root found no stored occurrence of any of
them. At the point of decision, *a filing whose section was structurally
refused* and *a company nobody has ever looked at* were the same fact.

**This slice persists facts only.** It replaces no score and moves no
decision.

Two dimensions, never collapsed: what knowledge is usable, and what the
latest explicit attempt did. Every pinned path below tests them apart.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.knowledge_acquisition import (
    KnowledgeAcquisitionEvent,
    KnowledgeOutcomeHistory,
)
from app.domain.knowledge_state import KnowledgeState
from app.domain.primary_source import SourceDocument
from app.domain.section_refusal import RefusedSection, SectionRefusal
from app.infrastructure.evidence.knowledge_outcome_store import (
    SCHEMA,
    KnowledgeOutcomeStore,
)
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.company_knowledge_extractor import ExtractionRejected
from app.services.company_knowledge_service import CompanyKnowledgeService
from tests.test_company_knowledge_service import (
    ExtractorStub,
    ProviderStub,
    ResolverStub,
)

MOMENT = datetime(2026, 8, 24, 18, 0, tzinfo=UTC)


def outcomes(tmp_path: Path) -> KnowledgeOutcomeStore:
    return KnowledgeOutcomeStore(tmp_path / "outcomes")


def service(
    tmp_path: Path,
    provider: ProviderStub,
    extractor: ExtractorStub | None,
    store: KnowledgeOutcomeStore | None = None,
) -> CompanyKnowledgeService:
    return CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
        sources=ResolverStub(provider),  # type: ignore[arg-type]
        extractor=extractor,  # type: ignore[arg-type]
        outcomes=store or outcomes(tmp_path),
    )


def refusing_document():
    """A document whose business section is structurally refused.

    Citigroup's shape: Item 1 is a page range, and the financial
    statements are printed in full — so the refusal rides on the
    section rather than failing the document.
    """

    def fetch(self, resolved):
        self.documents_read += 1

        return SourceDocument(
            source=resolved,
            business_description="",
            performance_discussion="",
            business_refusal=RefusedSection(
                reason=SectionRefusal.CROSS_REFERENCE_INDEX,
                expected="business description",
                form="10-K",
            ),
        )

    return fetch


# ── the six states, each pinned ─────────────────────────────────────


def test_available_acquired_is_recorded_with_its_document(tmp_path: Path) -> None:
    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert event.knowledge_usable is True
    assert event.observations_after == 1
    assert event.source_key
    assert event.usable_source_key == event.source_key
    assert event.ended_in_refusal is False


def test_available_cached_is_a_second_attempt_not_a_second_reading(
    tmp_path: Path,
) -> None:
    """A cache hit is still an attempt, and still appends."""

    store = outcomes(tmp_path)
    extractor = ExtractorStub()
    knowing = service(tmp_path, ProviderStub(), extractor, store)

    asyncio.run(knowing.knowledge("DIS"))
    asyncio.run(knowing.knowledge("DIS"))

    history = store.history("DIS")

    assert [e.state for e in history.events] == [
        KnowledgeState.AVAILABLE_ACQUIRED,
        KnowledgeState.AVAILABLE_CACHED,
    ]
    assert extractor.extractions == 1, "the second attempt read nothing"
    assert history.events[1].knowledge_usable is True


def test_unavailable_records_no_source_key(tmp_path: Path) -> None:
    """Source resolution failed, so no document was ever identified.

    The difference this preserves: *we could not find a filing* is not
    *we found one and could not read it*.
    """

    store = outcomes(tmp_path)

    asyncio.run(
        service(
            tmp_path, ProviderStub(unavailable="no filing"), ExtractorStub(), store
        ).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.UNAVAILABLE
    assert event.source_key is None
    assert event.knowledge_usable is False


def test_provider_error_is_distinct_from_unavailable(tmp_path: Path) -> None:
    store = outcomes(tmp_path)

    asyncio.run(
        service(
            tmp_path,
            ProviderStub(unavailable="the provider is down", outage=True),
            ExtractorStub(),
            store,
        ).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.PROVIDER_ERROR
    assert event.state.may_succeed_later is True


def test_invalid_extraction_is_recorded_and_stores_no_knowledge(
    tmp_path: Path,
) -> None:
    class Rejecting(ExtractorStub):
        async def extract(self, symbol: str, document: SourceDocument):
            raise ExtractionRejected("The span was not in the text.")

    store = outcomes(tmp_path)

    asyncio.run(service(tmp_path, ProviderStub(), Rejecting(), store).knowledge("DIS"))

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.INVALID_EXTRACTION
    assert event.knowledge_usable is False
    assert event.observations_after == 0
    assert event.ended_in_refusal is True


def test_document_refused_is_recorded_with_its_safe_wording(
    tmp_path: Path, monkeypatch
) -> None:
    store = outcomes(tmp_path)
    provider = ProviderStub()
    monkeypatch.setattr(ProviderStub, "fetch", refusing_document())

    asyncio.run(service(tmp_path, provider, ExtractorStub(), store).knowledge("DIS"))

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.DOCUMENT_REFUSED
    assert event.state.may_succeed_later is False
    assert event.source_key, "the document was found; its section was refused"
    # Retained only because it comes from a typed carrier this platform
    # composed — never from a provider's own message.
    assert event.because


# ── the two dimensions, apart ───────────────────────────────────────


@pytest.mark.parametrize(
    ("provider", "state"),
    [
        (ProviderStub(unavailable="down", outage=True), KnowledgeState.PROVIDER_ERROR),
        (ProviderStub(unavailable="none held"), KnowledgeState.UNAVAILABLE),
    ],
)
def test_last_known_knowledge_survives_every_non_available_outcome(
    tmp_path: Path, provider: ProviderStub, state: KnowledgeState
) -> None:
    """The pair the old shape could not express.

    Usable knowledge exists **and** the latest attempt failed. One
    boolean cannot hold both, which is why there are two fields.
    """

    store = outcomes(tmp_path)

    # First, acquire something real.
    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    # Then fail, with that knowledge still standing.
    outcome = asyncio.run(
        service(tmp_path, provider, ExtractorStub(), store).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert outcome.knowledge is not None, "the earlier reading still serves"
    assert event is not None
    assert event.state is state
    assert event.knowledge_usable is True
    assert event.observations_after == 1
    assert event.had_prior_knowledge is True


def test_no_prior_knowledge_beside_a_non_available_outcome(tmp_path: Path) -> None:
    store = outcomes(tmp_path)

    asyncio.run(
        service(
            tmp_path,
            ProviderStub(unavailable="down", outage=True),
            ExtractorStub(),
            store,
        ).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert event is not None
    assert event.knowledge_usable is False
    assert event.had_prior_knowledge is False


def test_a_partial_extraction_carries_both_halves(tmp_path: Path) -> None:
    """The case that earned a separate object rather than a seventh state.

    `observe()` takes some observations and a later extraction is
    refused. The knowledge is real and the run ended in a refusal, and
    no single `KnowledgeState` can say both — so the state stays
    AVAILABLE_ACQUIRED, which is true, and the refusal is carried
    beside it.
    """

    class RefusingAfterOne(ExtractorStub):
        async def extract(self, symbol: str, document: SourceDocument):
            if self.extractions >= 1:
                raise ExtractionRejected("The span was not in the text.")

            return await super().extract(symbol, document)

    store = outcomes(tmp_path)

    outcome = asyncio.run(
        service(tmp_path, ProviderStub(), RefusingAfterOne(), store).observe("DIS")
    )

    event = store.history("DIS").latest

    assert outcome.knowledge is not None
    assert event is not None
    assert event.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert event.knowledge_usable is True
    assert event.observations_after == 1
    assert event.ended_in_refusal is True, (
        "an uncomplicated success and a run that ended in a refusal "
        "must not look the same"
    )


# ── what may and may not append ─────────────────────────────────────


def test_established_appends_nothing_and_asks_nobody(tmp_path: Path) -> None:
    """A read-only page request is not an acquisition attempt."""

    store = outcomes(tmp_path)
    provider = ProviderStub()
    extractor = ExtractorStub()
    knowing = service(tmp_path, provider, extractor, store)

    asyncio.run(knowing.knowledge("DIS"))

    lookups, reads, extractions = (
        provider.lookups,
        provider.documents_read,
        extractor.extractions,
    )
    before = len(store.history("DIS").events)

    for _ in range(3):
        knowing.established("DIS")

    assert len(store.history("DIS").events) == before, "a page view appended"
    assert provider.lookups == lookups, "a page view resolved a source"
    assert provider.documents_read == reads, "a page view fetched a document"
    assert extractor.extractions == extractions, "a page view asked a model"


def test_two_identical_attempts_are_two_events(tmp_path: Path) -> None:
    """*This platform tried twice* is a fact only an unclipped record holds."""

    store = outcomes(tmp_path)
    knowing = service(
        tmp_path, ProviderStub(unavailable="down", outage=True), ExtractorStub(), store
    )

    asyncio.run(knowing.knowledge("DIS"))
    asyncio.run(knowing.knowledge("DIS"))

    history = store.history("DIS")

    assert history.attempts == 2
    assert {e.state for e in history.events} == {KnowledgeState.PROVIDER_ERROR}


def test_the_knowledge_write_lands_before_the_event_claims_it(
    tmp_path: Path,
) -> None:
    """Ordering, proved by killing the process between the two writes.

    A hard kill after the knowledge write leaves the knowledge usable
    and invents **no** attempt outcome — there is no `finally` that
    would manufacture one.
    """

    class Exploding(KnowledgeOutcomeStore):
        def append(self, event: KnowledgeAcquisitionEvent) -> None:
            raise KeyboardInterrupt("killed between the two writes")

    knowledge_store = JsonCompanyKnowledgeStore(tmp_path / "knowledge")
    store = Exploding(tmp_path / "outcomes")

    knowing = CompanyKnowledgeService(
        store=knowledge_store,
        sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
        extractor=ExtractorStub(),  # type: ignore[arg-type]
        outcomes=store,
    )

    with pytest.raises(KeyboardInterrupt):
        asyncio.run(knowing.knowledge("DIS"))

    # The knowledge is durable...
    survivor = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
        sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
        extractor=ExtractorStub(),  # type: ignore[arg-type]
        outcomes=outcomes(tmp_path),
    )

    assert survivor.established("DIS").knowledge is not None

    # ...and no outcome was manufactured for the attempt that died.
    assert KnowledgeOutcomeStore(tmp_path / "outcomes").history("DIS").events == ()


# ── safety: nothing sensitive reaches disk ──────────────────────────

SECRET = (
    "GET https://api.example.com/v1/filings?apikey=sk-live-9f3a2b71c0&"
    "account=ACC-88213 failed; body: 'Total revenue was $12,345,678 in "
    "the segment described on page 41'"
)


@pytest.mark.parametrize("outage", [True, False])
def test_no_credential_url_or_document_fragment_reaches_disk(
    tmp_path: Path, outage: bool
) -> None:
    """A provider message is never persisted, only its exception class.

    Seeded with an API key, a URL query, an account identifier and a
    fragment of the document. None of it may reach the journal.
    """

    store = outcomes(tmp_path)

    asyncio.run(
        service(
            tmp_path,
            ProviderStub(unavailable=SECRET, outage=outage),
            ExtractorStub(),
            store,
        ).knowledge("DIS")
    )

    written = store.path_for("DIS").read_text()
    event = store.history("DIS").latest

    for secret in (
        "sk-live-9f3a2b71c0",
        "api.example.com",
        "ACC-88213",
        "12,345,678",
        "page 41",
    ):
        assert secret not in written, f"{secret} reached disk"

    assert event is not None
    assert event.because in ("PrimarySourceProviderError", "PrimarySourceUnavailable")


def test_no_extraction_message_reaches_disk(tmp_path: Path) -> None:
    class Leaking(ExtractorStub):
        async def extract(self, symbol: str, document: SourceDocument):
            raise ExtractionRejected(SECRET)

    store = outcomes(tmp_path)

    asyncio.run(service(tmp_path, ProviderStub(), Leaking(), store).knowledge("DIS"))

    written = store.path_for("DIS").read_text()

    for secret in ("sk-live-9f3a2b71c0", "api.example.com", "ACC-88213", "12,345,678"):
        assert secret not in written, f"{secret} reached disk"

    assert store.history("DIS").latest.because == "ExtractionRejected"  # type: ignore[union-attr]


def test_no_raw_filing_content_is_stored(tmp_path: Path) -> None:
    """The document's own words never enter the outcome journal."""

    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    written = store.path_for("DIS").read_text()

    assert "theme parks" not in written
    assert "Experiences segment operates" not in written


# ── the read contract ───────────────────────────────────────────────


def test_unreadable_and_unsupported_records_are_counted_separately(
    tmp_path: Path,
) -> None:
    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    path = store.path_for("DIS")

    with path.open("a", encoding="utf-8") as stream:
        stream.write("{not json at all\n")
        stream.write(json.dumps({"schema": 99, "symbol": "DIS"}) + "\n")
        stream.write(json.dumps({"schema": SCHEMA, "symbol": "DIS"}) + "\n")

    history = store.history("DIS")

    assert history.attempts == 1, "only the well-formed line decoded"
    assert history.unreadable_records == 2, "malformed JSON and a missing field"
    assert history.unsupported_schemas == (("99", 1),)
    assert history.is_complete is False
    assert history.skipped == 3


def test_an_incomplete_history_refuses_to_name_a_latest_outcome(
    tmp_path: Path,
) -> None:
    """With a line missing, the newest readable event may not be newest."""

    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    with store.path_for("DIS").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"schema": 99}) + "\n")

    history = store.history("DIS")

    assert history.events, "the readable event is still returned"
    assert history.latest is None, "a latest claim needs a complete history"


def test_a_corrupt_history_does_not_erase_usable_company_knowledge(
    tmp_path: Path,
) -> None:
    """Two stores, two facts. A broken journal says nothing about the company."""

    store = outcomes(tmp_path)
    knowing = service(tmp_path, ProviderStub(), ExtractorStub(), store)

    asyncio.run(knowing.knowledge("DIS"))

    store.path_for("DIS").write_text("{ruined\n{also ruined\n")

    assert store.history("DIS").is_complete is False
    assert knowing.established("DIS").knowledge is not None


def test_a_symbol_never_attempted_has_an_empty_history(tmp_path: Path) -> None:
    """Never recorded — not a provider error, and not a document refusal."""

    history = outcomes(tmp_path).history("NEVER")

    assert history.events == ()
    assert history.latest is None
    assert history.is_complete is True, "an empty journal is complete, not broken"
    assert history.attempts == 0


def test_old_installations_begin_with_an_empty_journal(tmp_path: Path) -> None:
    """No backfill. Nothing is inferred from a knowledge file's existence."""

    knowledge_store = JsonCompanyKnowledgeStore(tmp_path / "knowledge")
    knowing = service(tmp_path, ProviderStub(), ExtractorStub(), outcomes(tmp_path))

    asyncio.run(knowing.knowledge("DIS"))

    # A second symbol whose knowledge exists but whose journal does not.
    (tmp_path / "outcomes" / "DIS.jsonl").unlink()

    assert outcomes(tmp_path).history("DIS").events == ()
    assert knowledge_store.latest("DIS"), "the knowledge itself is untouched"


# ── the event's own contract ────────────────────────────────────────


def test_an_event_refuses_a_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="aware timezone"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=datetime(2026, 8, 24, 18, 0),
            state=KnowledgeState.UNAVAILABLE,
        )


def test_an_event_refuses_usable_knowledge_with_no_observations() -> None:
    with pytest.raises(ValueError, match="at least one stored observation"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge_usable=True,
            observations_after=0,
        )


def test_the_history_is_a_projection_and_stores_nothing() -> None:
    history = KnowledgeOutcomeHistory(symbol="DIS")

    assert history.latest is None
    assert history.attempts == 0
    assert history.skipped == 0


# ── provenance: the canonical publication field ─────────────────────


def test_the_event_records_the_sources_own_publication_date(
    tmp_path: Path,
) -> None:
    """Production-shaped: a real `PrimarySource`, its exact ISO date.

    The first cut read `.published` through `getattr` — a field no
    source has ever had — so every event recorded an empty date while
    claiming the source was resolved. The fixture is the real
    `PrimarySource` the service suite uses, published 2025-11-13.
    """

    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    event = store.history("DIS").latest

    assert event is not None
    assert event.source_published == "2025-11-13"


def test_no_production_path_reads_a_published_field() -> None:
    """`published_on` is the canonical field; `.published` never existed.

    Enforced at the AST so the probe cannot come back under a different
    spelling of the same mistake.
    """

    import ast
    import pathlib as _pathlib

    tree = ast.parse(
        _pathlib.Path("app/services/company_knowledge_service.py").read_text(
            encoding="utf-8"
        )
    )

    accessed = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    } | {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert "published" not in accessed
    assert "published_on" in {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }


# ── strict decoding: malformed is unreadable, never repaired ────────


def valid_line(**overrides: object) -> str:
    """A line this writer would produce, with one field bent per test."""

    row: dict[str, object] = {
        "schema": SCHEMA,
        "symbol": "DIS",
        "attempted_at": "2026-08-24T18:00:00+00:00",
        "state": "unavailable",
        "source_key": None,
        "source_published": "",
        "because": "",
        "knowledge_usable": False,
        "usable_source_key": None,
        "observations_after": 0,
        "ended_in_refusal": False,
    }
    row.update(overrides)

    return json.dumps(row) + "\n"


@pytest.mark.parametrize(
    "overrides",
    [
        {"knowledge_usable": "false"},
        {"ended_in_refusal": 0},
        {"observations_after": "1"},
        {"observations_after": -1},
        {"observations_after": True},
        {"attempted_at": "2026-08-24T18:00:00"},
        {"source_published": "13/11/2025"},
        {"symbol": ""},
        {"symbol": 7},
        {"because": None},
        {"state": "acquired"},
        {"source_key": 7},
    ],
    ids=[
        "usable-as-string",
        "refusal-as-zero",
        "count-as-string",
        "count-negative",
        "count-as-boolean",
        "naive-timestamp",
        "invalid-publication-date",
        "empty-symbol",
        "numeric-symbol",
        "null-because",
        "unknown-state",
        "numeric-source-key",
    ],
)
def test_a_malformed_current_schema_line_is_unreadable(
    tmp_path: Path, overrides: dict[str, object]
) -> None:
    """No `bool()`, `int()` or `str()` ever repairs a stored value.

    The decisive row: `"knowledge_usable": "false"` — a coercing reader
    turns it into `True`, because a non-empty string is truthy. A
    journal whose reader can invert a stored fact is worse than no
    journal.
    """

    store = outcomes(tmp_path)
    store.path_for("DIS").parent.mkdir(parents=True, exist_ok=True)
    store.path_for("DIS").write_text(valid_line(**overrides))

    history = store.history("DIS")

    assert history.events == (), "the bent line decoded"
    assert history.unreadable_records == 1
    assert history.is_complete is False


def test_the_unbent_control_line_decodes(tmp_path: Path) -> None:
    """The fixture itself is valid — so each refusal above is the bend."""

    store = outcomes(tmp_path)
    store.path_for("DIS").parent.mkdir(parents=True, exist_ok=True)
    store.path_for("DIS").write_text(valid_line())

    history = store.history("DIS")

    assert history.attempts == 1
    assert history.is_complete is True
    assert history.events[0].knowledge_usable is False


def test_a_boolean_schema_is_never_schema_one(tmp_path: Path) -> None:
    """JSON `true` equals `1` in Python; it is still not schema 1."""

    store = outcomes(tmp_path)
    store.path_for("DIS").parent.mkdir(parents=True, exist_ok=True)
    store.path_for("DIS").write_text(valid_line(schema=True))

    history = store.history("DIS")

    assert history.events == ()
    assert history.unsupported_schemas == (("True", 1),)


# ── construction invariants ─────────────────────────────────────────


def test_an_available_outcome_requires_usable_knowledge() -> None:
    with pytest.raises(ValueError, match="contradiction"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            knowledge_usable=False,
        )


def test_usable_knowledge_requires_its_document() -> None:
    with pytest.raises(ValueError, match="document it was read from"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge_usable=True,
            observations_after=1,
        )


def test_unusable_knowledge_carries_no_key_and_no_count() -> None:
    with pytest.raises(ValueError, match="unusable knowledge"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.UNAVAILABLE,
            knowledge_usable=False,
            usable_source_key="0001744489-25-000155",
        )

    with pytest.raises(ValueError, match="unusable knowledge"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.UNAVAILABLE,
            knowledge_usable=False,
            observations_after=3,
        )


def test_a_refusal_ended_attempt_carries_its_reason() -> None:
    with pytest.raises(ValueError, match="safe reason"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.INVALID_EXTRACTION,
            ended_in_refusal=True,
            because="",
        )


def test_a_document_refusal_carries_its_typed_reason() -> None:
    with pytest.raises(ValueError, match="typed reason"):
        KnowledgeAcquisitionEvent(
            symbol="DIS",
            attempted_at=MOMENT,
            state=KnowledgeState.DOCUMENT_REFUSED,
            because="  ",
        )


# ── symbol identity and path safety ─────────────────────────────────


def test_the_event_normalizes_its_symbol_once() -> None:
    event = KnowledgeAcquisitionEvent(
        symbol="  dis ",
        attempted_at=MOMENT,
        state=KnowledgeState.UNAVAILABLE,
    )

    assert event.symbol == "DIS"


@pytest.mark.parametrize("symbol", ["NESN.ZU", "VOW3.DE", "NOVO-B.CO", "BNP.PA"])
def test_dotted_and_hyphenated_symbols_round_trip(tmp_path: Path, symbol: str) -> None:
    store = outcomes(tmp_path)

    store.append(
        KnowledgeAcquisitionEvent(
            symbol=symbol,
            attempted_at=MOMENT,
            state=KnowledgeState.UNAVAILABLE,
        )
    )

    history = store.history(symbol)

    assert history.attempts == 1
    assert history.events[0].symbol == symbol
    assert store.path_for(symbol).resolve().parent == (tmp_path / "outcomes").resolve()


@pytest.mark.parametrize(
    "hostile", ["../DIS", "A/B", "   ", "DIS\u0000", ".hidden", "a\\b"]
)
def test_path_shaping_symbols_never_reach_the_filesystem(
    tmp_path: Path, hostile: str
) -> None:
    """Validated, never encoded — and refused before any path exists."""

    store = outcomes(tmp_path)

    with pytest.raises(ValueError, match="canonical MOVRvest symbol"):
        store.path_for(hostile)

    with pytest.raises(ValueError, match="canonical MOVRvest symbol"):
        store.history(hostile)

    with pytest.raises(ValueError):
        KnowledgeAcquisitionEvent(
            symbol=hostile,
            attempted_at=MOMENT,
            state=KnowledgeState.UNAVAILABLE,
        )

    assert not (tmp_path / "outcomes").exists() or not any(
        (tmp_path / "outcomes").iterdir()
    ), "a hostile symbol created something"


def test_another_symbols_event_is_unreadable_not_pooled(tmp_path: Path) -> None:
    """A journal keyed by symbol may not serve one symbol's history
    out of another's attempts."""

    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    with store.path_for("DIS").open("a", encoding="utf-8") as stream:
        stream.write(valid_line(symbol="MSFT"))

    history = store.history("DIS")

    assert history.attempts == 1
    assert all(e.symbol == "DIS" for e in history.events)
    assert history.unreadable_records == 1
    assert history.latest is None, "an alien line breaks the complete claim"


# ── prior knowledge on the no-reader observe path ───────────────────


def test_a_no_reader_observe_preserves_prior_knowledge(tmp_path: Path) -> None:
    """Amendment 4's control, exactly as worded.

    First store valid knowledge; then observe through a service with no
    configured reader. The refused attempt records the prior knowledge
    beside its own failure, touches no provider and asks no model — and
    the knowledge itself remains readable.
    """

    store = outcomes(tmp_path)

    asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub(), store).knowledge("DIS")
    )

    provider = ProviderStub()
    unread = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
        sources=ResolverStub(provider),  # type: ignore[arg-type]
        extractor=None,
        outcomes=store,
    )

    outcome = asyncio.run(unread.observe("DIS"))

    event = store.history("DIS").latest

    assert event is not None
    assert event.state is KnowledgeState.UNAVAILABLE
    assert event.knowledge_usable is True
    assert event.usable_source_key is not None
    assert event.observations_after == 1
    assert event.had_prior_knowledge is True

    assert outcome.knowledge is not None, "the earlier reading still serves"
    assert unread.established("DIS").knowledge is not None

    assert provider.lookups == 0, "the refused attempt resolved a source"
    assert provider.documents_read == 0, "the refused attempt fetched"


# ── attempted-at means attempted-at ─────────────────────────────────


def test_attempted_at_is_captured_before_the_funded_body_runs(
    tmp_path: Path,
) -> None:
    """The stamp is the attempt's start, not its end.

    The clock ticks forward one minute per reading, and the extraction
    itself consumes a tick — so a stamp taken after the body would
    carry the second tick, and the event must carry the first.
    """

    from datetime import timedelta

    ticks = [MOMENT + timedelta(minutes=i) for i in range(10)]

    def clock() -> datetime:
        return ticks.pop(0)

    class TimeConsuming(ExtractorStub):
        async def extract(self, symbol: str, document: SourceDocument):
            clock()  # the extraction takes a minute

            return await super().extract(symbol, document)

    store = outcomes(tmp_path)
    knowing = CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path / "knowledge"),
        sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
        extractor=TimeConsuming(),  # type: ignore[arg-type]
        outcomes=store,
        clock=clock,
    )

    asyncio.run(knowing.knowledge("DIS"))

    event = store.history("DIS").latest

    assert event is not None
    assert event.attempted_at == MOMENT, (
        "the event was stamped after the extraction rather than before it"
    )


# ── nothing decision-bearing moved ──────────────────────────────────


def test_the_journal_reaches_no_decision() -> None:
    """This slice persists facts. It replaces no score and moves nothing.

    Guarded at the import graph: nothing in the decision path may reach
    the acquisition journal, and the journal may not reach a decision.
    """

    import pathlib

    for module in (
        "app/cio/artificial_cio.py",
        "app/application/executive/decision_evidence_builder.py",
        "app/domain/decision_rules.py",
    ):
        source = pathlib.Path(module).read_text(encoding="utf-8")

        assert "knowledge_outcome" not in source, module
        assert "KnowledgeAcquisitionEvent" not in source, module

    # Identifiers, not prose: the module explains what it is *not* for,
    # and a substring search would fail on its own explanation.
    import ast

    tree = ast.parse(
        pathlib.Path("app/domain/knowledge_acquisition.py").read_text(encoding="utf-8")
    )
    referenced = (
        {
            node.id if isinstance(node, ast.Name) else node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Name | ast.Attribute)
        }
        | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
    )

    for forbidden in (
        "evidence_score",
        "DecisionEvidence",
        "ArtificialCIO",
        "conviction",
    ):
        assert forbidden not in referenced, forbidden
