"""The stream that remembers what the latest-value cache forgets.

#215 measured the forget-flip completing live: SPCX was UNRESOLVED on
the 2026-08-13 payload, the vendor drifted into agreement, and the
fundamentals cache — one replaced file per key — kept only the
agreement. Every case below either pins that an explicit funded
acquisition now preserves what it observed, or pins that nothing else
changed: no historical gate, no resolution vocabulary, no cache
movement, no writes from any read path.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.commands.identity_history import render
from app.domain.identity_observation import (
    DISCLOSURE,
    LIFECYCLE_SENTENCES,
    IdentityHistory,
    ProviderIdentityObservation,
)
from app.domain.provenance import Provenance
from app.domain.provider_identity import (
    IdentityStanding,
    ProviderIdentityClaim,
)
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import JsonCache
from app.infrastructure.evidence.identity_observation_store import (
    IdentityObservationStore,
)
from app.infrastructure.evidence_root import evidence_path
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.value_provider import ObservedValuation

BROKER = ProviderIdentityClaim(
    provider="eToro",
    symbol="SPCX",
    instrument_id="15618",
    name="Space Exploration Technologies Corp",
    taxonomy="5",
)

#: The vendor's two accounts, in the order the live corpus produced
#: them: the disputed one first, the agreeing one after the drift.
DISPUTED = ProviderIdentityClaim(
    provider="Yahoo Finance",
    symbol="SPCX",
    name="SPAC and New Issue ETF",
    taxonomy="ETF",
)
AGREEING = ProviderIdentityClaim(
    provider="Yahoo Finance",
    symbol="SPCX",
    name="Space Exploration Technologies Corp.",
    taxonomy="EQUITY",
)


def snapshot_for(vendor: ProviderIdentityClaim, moment: datetime) -> ValuationSnapshot:
    return ValuationSnapshot(
        forward_pe=20.0,
        trailing_pe=None,
        peg_ratio=None,
        dividend_yield=None,
        vendor_identity=vendor,
        reading=Provenance(source="Yahoo Finance", observed_at=moment),
    )


class ProviderStub:
    """A vendor whose account changes between funded reads."""

    def __init__(self, *readings: ObservedValuation) -> None:
        self._readings = list(readings)
        self.fetches = 0

    def observed(self, symbol: str) -> ObservedValuation:
        self.fetches += 1

        return self._readings.pop(0)

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        return self.observed(symbol).snapshot


def observed(
    vendor: ProviderIdentityClaim,
    moment: datetime,
    first_trade_date_ms: int | None = None,
    ipo_expected_date: str | None = None,
) -> ObservedValuation:
    return ObservedValuation(
        snapshot=snapshot_for(vendor, moment),
        first_trade_date_ms=first_trade_date_ms,
        ipo_expected_date=ipo_expected_date,
    )


def provider_for(tmp_path, *readings: ObservedValuation) -> CachedValueProvider:
    return CachedValueProvider(
        provider=ProviderStub(*readings),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path / "fundamentals", schema=4),
        observations=IdentityObservationStore(tmp_path / "identity"),
    )


def clear(cache: JsonCache, key: str = "SPCX") -> None:
    cache._path_for(key).unlink()  # noqa: SLF001


MONDAY = datetime(2026, 8, 13, 9, 0, tzinfo=UTC)
TUESDAY = datetime(2026, 8, 19, 9, 0, tzinfo=UTC)


def acquire_twice(tmp_path) -> IdentityObservationStore:
    """The forget-flip, replayed against the stream: two funded reads.

    The cache is cleared between them so the second call actually
    acquires — in production the two reads are on different days and
    `is_from_today` lets the second one through.
    """

    store = IdentityObservationStore(tmp_path / "identity")
    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    first = CachedValueProvider(
        provider=ProviderStub(
            observed(DISPUTED, MONDAY, first_trade_date_ms=1781271000000)
        ),  # type: ignore[arg-type]
        cache=cache,
        observations=store,
    )
    first.snapshot_observing("SPCX", BROKER, subject="SPCX")

    clear(cache)

    second = CachedValueProvider(
        provider=ProviderStub(observed(AGREEING, TUESDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=store,
    )
    second.snapshot_observing("SPCX", BROKER, subject="SPCX")

    return store


# ── 1–2: two acquisitions, both retained ────────────────────────────


def test_two_acquisitions_append_two_observations_and_the_first_survives(
    tmp_path,
) -> None:
    store = acquire_twice(tmp_path)

    held = store.observations("SPCX")

    assert len(held) == 2
    assert held[0].captured_at == MONDAY
    assert held[0].vendor.name == "SPAC and New Issue ETF"
    assert held[1].captured_at == TUESDAY
    assert held[1].vendor.name == "Space Exploration Technologies Corp."


def test_unresolved_to_assumed_is_retained_as_two_captures(tmp_path) -> None:
    """The forget-flip, no longer forgetting.

    The first capture's standing is what the claims supported then;
    the second's is what they support now; and both stay queryable —
    which is exactly what the latest-value cache cannot do.
    """

    held = acquire_twice(tmp_path).observations("SPCX")

    assert held[0].standing is IdentityStanding.UNRESOLVED
    assert held[1].standing is IdentityStanding.ASSUMED


# ── 3–4: the read surface's wording ─────────────────────────────────


def test_the_read_surface_reports_previous_dispute_and_current_agreement(
    tmp_path,
) -> None:
    store = acquire_twice(tmp_path)

    history = IdentityHistory(symbol="SPCX", observations=store.observations("SPCX"))

    assert history.previously_disputed
    assert not history.currently_disputed
    assert history.lifecycle_stated == "Previously disputed; current claims agree."

    rendered = render(history)

    assert "Previously disputed; current claims agree." in rendered
    assert "SPAC and New Issue ETF" in rendered, "the disputed claim is shown"


def test_later_agreement_is_never_worded_as_resolved_or_corrected(tmp_path) -> None:
    """No resolution evidence class is uniformly available (#215 §5).

    Checked twice: over the finite lifecycle vocabulary — every
    sentence a history can ever produce — and over the rendered
    surface for the exact history that would tempt the stronger word.
    """

    for sentence in LIFECYCLE_SENTENCES:
        for banned in ("resolved", "corrected", "correction", "fixed"):
            assert banned not in sentence.casefold(), sentence

    store = acquire_twice(tmp_path)
    rendered = render(
        IdentityHistory(symbol="SPCX", observations=store.observations("SPCX"))
    ).casefold()

    assert "resolved" not in rendered
    assert "corrected" not in rendered


def test_the_read_surface_discloses_that_history_never_decides(tmp_path) -> None:
    """The owner's #215 ruling, printed where the history is."""

    assert "not decision-bearing" in DISCLOSURE

    empty = render(IdentityHistory(symbol="KO", observations=()))

    assert DISCLOSURE in empty
    assert "empty history" in empty

    store = acquire_twice(tmp_path)
    full = render(
        IdentityHistory(symbol="SPCX", observations=store.observations("SPCX"))
    )

    assert DISCLOSURE in full


# ── 5–6: what one observation carries ───────────────────────────────


def test_broker_claims_are_persisted_verbatim(tmp_path) -> None:
    """Before this stream, half of every contradiction was unrecordable."""

    held = acquire_twice(tmp_path).observations("SPCX")

    for observation in held:
        assert observation.broker == BROKER
        assert observation.broker.provider == "eToro"
        assert observation.broker.instrument_id == "15618"
        assert observation.broker.taxonomy == "5"


def test_tenancy_fields_are_retained_raw_and_infer_nothing(tmp_path) -> None:
    """PARA impeached `firstTradeDate` as a rule (#215 §5).

    The field is kept exactly as the payload spelled it, and the
    standing beside it is derived from the claims alone: the same
    disputed claims produce the same standing whether the tenancy
    field is present, absent, or wildly different.
    """

    held = acquire_twice(tmp_path).observations("SPCX")

    assert held[0].first_trade_date_ms == 1781271000000
    assert held[0].ipo_expected_date is None
    assert held[1].first_trade_date_ms is None

    # Same claims, no tenancy field → same standing. Nothing infers.
    bare = ProviderIdentityObservation(
        symbol="SPCX",
        captured_at=MONDAY,
        broker=BROKER,
        vendor=DISPUTED,
        standing=IdentityStanding.UNRESOLVED,
    )

    assert bare.standing is held[0].standing
    assert bare.first_trade_date_ms is None


# ── 7: only explicit acquisition writes ─────────────────────────────


class ExplodingStore(IdentityObservationStore):
    def append(self, observation) -> None:  # noqa: ANN001
        raise AssertionError("a read path appended an identity observation")


def test_read_and_evaluate_paths_never_append(tmp_path) -> None:
    """`snapshot`, the stored door, and the CLI render all stay reads."""

    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    acquiring = CachedValueProvider(
        provider=ProviderStub(observed(AGREEING, TUESDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=ExplodingStore(tmp_path / "identity"),
    )

    # The plain acquiring door reads and caches without observing.
    assert acquiring.snapshot("SPCX").reading is not None

    stored = CachedValueProvider(
        cache=cache,
        acquires=False,
        observations=ExplodingStore(tmp_path / "identity"),
    )

    assert stored.snapshot("SPCX").reading is not None

    render(IdentityHistory(symbol="SPCX", observations=()))

    assert not (tmp_path / "identity").exists(), "no read created the stream"


def test_a_cache_served_read_observes_nothing(tmp_path) -> None:
    """Serving today's cached reading is not a funded acquisition."""

    store = IdentityObservationStore(tmp_path / "identity")
    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    provider = CachedValueProvider(
        provider=ProviderStub(  # type: ignore[arg-type]
            observed(AGREEING, datetime.now(UTC))
        ),
        cache=cache,
        observations=store,
    )

    provider.snapshot_observing("SPCX", BROKER, subject="SPCX")
    provider.snapshot_observing("SPCX", BROKER, subject="SPCX")

    assert len(store.observations("SPCX")) == 1


def test_the_observation_lands_before_the_cache_replacement(tmp_path) -> None:
    """The write order is the contract, pinned by a spy.

    At the moment the observation is appended, the cache must still
    hold what it held before — the store that forgets can never get
    ahead of the one that remembers.
    """

    cache = JsonCache(tmp_path / "fundamentals", schema=5)
    seen_at_append: list[str | None] = []

    class OrderSpy(IdentityObservationStore):
        def append(self, observation) -> None:  # noqa: ANN001
            entry = cache.read("SPCX")

            seen_at_append.append(
                None if entry is None else entry.value["vendor_identity"]["name"]  # type: ignore[index]
            )

            super().append(observation)

    first = CachedValueProvider(
        provider=ProviderStub(observed(DISPUTED, MONDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=OrderSpy(tmp_path / "identity"),
    )
    first.snapshot_observing("SPCX", BROKER, subject="SPCX")

    clear(cache)
    cache.write("SPCX", first._encode(snapshot_for(DISPUTED, MONDAY)))  # noqa: SLF001

    second = CachedValueProvider(
        provider=ProviderStub(observed(AGREEING, TUESDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=OrderSpy(tmp_path / "identity"),
    )
    # A same-day cached entry would be served without acquiring, so age
    # the entry by rewriting its stamp — the spy needs a real acquire
    # over a really-populated cache.
    aged = cache._path_for("SPCX")  # noqa: SLF001
    aged.write_text(
        aged.read_text().replace(
            f'"stored_at": "{datetime.now(UTC).year}-', '"stored_at": "2025-'
        )
    )

    second.snapshot_observing("SPCX", BROKER, subject="SPCX")

    assert seen_at_append[0] is None, "first acquire: cache empty at append"
    assert seen_at_append[1] == "SPAC and New Issue ETF", (
        "second acquire: the old value still in the cache at append time"
    )


# ── 8: the fundamentals cache is untouched ──────────────────────────


def test_the_fundamentals_cache_schema_and_latest_value_behavior_are_unchanged(
    tmp_path,
) -> None:
    """Schema 5 since the 2026-08-23 ruling, still a latest-value replacement.

    Written at 4 by #216 to pin that the identity stream changed no
    cache contract; schema 5 adds `financial_currency` (the fundamentals
    fallback ruling), and what this test protects is unchanged — the
    migrations are the identity and the cache holds only the latest
    account.
    """

    live = CachedValueProvider()

    assert live._cache.schema == 5  # noqa: SLF001
    assert set(live._cache.migrations) == {1, 2, 3, 4}  # noqa: SLF001

    store = acquire_twice(tmp_path)
    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    entry = cache.read("SPCX")

    assert entry is not None
    # The cache holds ONLY the latest account — that is its contract,
    # and the stream beside it is why that stopped being a loss.
    assert entry.value["vendor_identity"]["name"] == (  # type: ignore[index]
        "Space Exploration Technologies Corp."
    )
    assert len(store.observations("SPCX")) == 2


def test_the_observing_door_writes_the_same_cache_record_as_the_plain_one(
    tmp_path,
) -> None:
    """One vendor account, two doors, byte-identical cache values."""

    reading = observed(AGREEING, TUESDAY)

    plain_cache = JsonCache(tmp_path / "plain", schema=4)
    CachedValueProvider(
        provider=ProviderStub(reading),  # type: ignore[arg-type]
        cache=plain_cache,
        observations=IdentityObservationStore(tmp_path / "identity"),
    ).snapshot("SPCX")

    observing_cache = JsonCache(tmp_path / "observing", schema=4)
    CachedValueProvider(
        provider=ProviderStub(reading),  # type: ignore[arg-type]
        cache=observing_cache,
        observations=IdentityObservationStore(tmp_path / "identity"),
    ).snapshot_observing("SPCX", BROKER, subject="SPCX")

    plain = plain_cache.read("SPCX")
    observing = observing_cache.read("SPCX")

    assert plain is not None and observing is not None
    assert plain.value == observing.value


# ── 9: hermetic root ────────────────────────────────────────────────


def test_the_default_store_resolves_under_the_evidence_root(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("MOVRVEST_EVIDENCE_ROOT", str(tmp_path))

    store = IdentityObservationStore()

    assert store.path_for("SE") == evidence_path("identity") / "SE.jsonl"
    assert str(store.path_for("SE")).startswith(str(tmp_path))


# ── the stream's own contract ───────────────────────────────────────


def test_a_line_under_an_unknown_schema_is_skipped_not_pooled(tmp_path) -> None:
    store = IdentityObservationStore(tmp_path / "identity")

    acquire_twice(tmp_path)

    path = store.path_for("SPCX")

    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"schema": 99, "symbol": "SPCX", "standing": "assumed"}\n')
        handle.write("not json at all\n")

    assert len(store.observations("SPCX")) == 2


def test_a_fresh_installation_has_empty_history(tmp_path) -> None:
    store = IdentityObservationStore(tmp_path / "identity")

    assert store.observations("SPCX") == ()
    assert store.observations("SE") == ()


def test_no_observation_is_appended_when_the_vendor_makes_no_claim(tmp_path) -> None:
    """An empty vendor account recorded would read as the vendor speaking."""

    store = IdentityObservationStore(tmp_path / "identity")

    silent = ObservedValuation(
        snapshot=ValuationSnapshot(
            forward_pe=20.0,
            trailing_pe=None,
            peg_ratio=None,
            dividend_yield=None,
            vendor_identity=None,
            reading=Provenance(source="Yahoo Finance", observed_at=TUESDAY),
        )
    )

    CachedValueProvider(
        provider=ProviderStub(silent),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path / "fundamentals", schema=4),
        observations=store,
    ).snapshot_observing("SPCX", BROKER, subject="SPCX")

    assert store.observations("SPCX") == ()


def test_a_currently_disputed_history_says_so_without_stronger_words(tmp_path) -> None:
    store = IdentityObservationStore(tmp_path / "identity")

    CachedValueProvider(
        provider=ProviderStub(observed(DISPUTED, MONDAY)),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path / "fundamentals", schema=4),
        observations=store,
    ).snapshot_observing("SPCX", BROKER, subject="SPCX")

    history = IdentityHistory(symbol="SPCX", observations=store.observations("SPCX"))

    assert history.currently_disputed
    assert history.lifecycle_stated.startswith("Currently disputed")


def test_never_disputed_is_its_own_sentence() -> None:
    steady = ProviderIdentityObservation(
        symbol="KO",
        captured_at=MONDAY,
        broker=ProviderIdentityClaim(provider="eToro", symbol="KO", name="Coca-Cola"),
        vendor=ProviderIdentityClaim(
            provider="Yahoo Finance", symbol="KO", name="Coca-Cola Company (The)"
        ),
        standing=IdentityStanding.ASSUMED,
    )

    history = IdentityHistory(symbol="KO", observations=(steady,))

    assert history.lifecycle_stated == "Never disputed across the held captures."


# ── the canonical filing symbol (correction 1) ──────────────────────


def test_history_is_filed_under_the_investor_symbol_and_cache_under_the_vendors(
    tmp_path,
) -> None:
    """Broker BTC, vendor BTC-USD: two symbols, two jobs.

    The fundamentals cache stays keyed by the vendor's translation and
    the identity history by the security the investor holds. Neither
    claim is rewritten to make their symbols agree — the difference is
    part of what was observed.
    """

    store = IdentityObservationStore(tmp_path / "identity")
    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    broker = ProviderIdentityClaim(
        provider="eToro",
        symbol="BTC",
        instrument_id="100000",
        taxonomy="10",
        name="Bitcoin",
    )
    vendor = ProviderIdentityClaim(
        provider="Yahoo Finance",
        symbol="BTC-USD",
        name="Bitcoin USD",
        taxonomy="CRYPTOCURRENCY",
    )

    CachedValueProvider(
        provider=ProviderStub(observed(vendor, TUESDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=store,
    ).snapshot_observing("BTC-USD", broker, subject="BTC")

    # The cache holds the reading under the vendor's key.
    assert cache.read("BTC-USD") is not None
    assert cache.read("BTC") is None

    # The history is under the investor's symbol, and only there.
    held = store.observations("BTC")

    assert len(held) == 1
    assert held[0].symbol == "BTC"
    assert store.observations("BTC-USD") == ()

    # And each claim keeps its own spelling verbatim.
    assert held[0].broker.symbol == "BTC"
    assert held[0].vendor.symbol == "BTC-USD"


def test_a_venue_translated_listing_separates_the_same_way(tmp_path) -> None:
    """Broker NESN.ZU, vendor NESN.SW — the equity translation case."""

    store = IdentityObservationStore(tmp_path / "identity")
    cache = JsonCache(tmp_path / "fundamentals", schema=5)

    broker = ProviderIdentityClaim(
        provider="eToro", symbol="NESN.ZU", name="Nestle", taxonomy="5"
    )
    vendor = ProviderIdentityClaim(
        provider="Yahoo Finance",
        symbol="NESN.SW",
        name="Nestle S.A.",
        taxonomy="EQUITY",
    )

    CachedValueProvider(
        provider=ProviderStub(observed(vendor, TUESDAY)),  # type: ignore[arg-type]
        cache=cache,
        observations=store,
    ).snapshot_observing("NESN.SW", broker, subject="NESN.ZU")

    assert cache.read("NESN.SW") is not None
    assert store.observations("NESN.ZU")[0].symbol == "NESN.ZU"
    assert store.observations("NESN.SW") == ()
    assert store.observations("NESN.ZU")[0].vendor.symbol == "NESN.SW"


def test_the_vendor_key_history_does_not_impersonate_the_investors(tmp_path) -> None:
    """`identity-history BTC-USD` finds nothing filed as the investor's."""

    store = IdentityObservationStore(tmp_path / "identity")

    rendered = render(IdentityHistory.from_stream("BTC-USD", store.stream("BTC-USD")))

    assert "No identity observations are held" in rendered


# ── an incomplete stream never claims a complete lifecycle (correction 2) ──


def append_raw(store: IdentityObservationStore, symbol: str, line: str) -> None:
    path = store.path_for(symbol)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def test_a_skipped_unknown_schema_line_forbids_never_disputed(tmp_path) -> None:
    """The pin the correction names.

    A readable ASSUMED beside a skipped UNRESOLVED-shaped line under an
    unknown schema: the readable remainder must not speak for the
    stream. "Never disputed" is a claim about the complete history, and
    this reader did not read all of it.
    """

    store = IdentityObservationStore(tmp_path / "identity")

    CachedValueProvider(
        provider=ProviderStub(observed(AGREEING, TUESDAY)),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path / "fundamentals", schema=4),
        observations=store,
    ).snapshot_observing("SPCX", BROKER, subject="SPCX")

    append_raw(
        store,
        "SPCX",
        '{"schema": 2, "symbol": "SPCX", "standing": "unresolved"}',
    )

    reading = store.stream("SPCX")

    assert len(reading.observations) == 1
    assert reading.unsupported_schemas == (("2", 1),)
    assert not reading.is_complete

    history = IdentityHistory.from_stream("SPCX", reading)

    assert "incomplete" in history.lifecycle_stated
    assert "Never disputed" not in history.lifecycle_stated
    assert "no complete lifecycle is claimed" in history.lifecycle_stated


def test_a_corrupt_later_line_forbids_currently_disputed(tmp_path) -> None:
    """A readable UNRESOLVED with an unreadable line after it.

    The unread line may be the newer capture; claiming "currently
    disputed" would present a partial read as the current state of the
    complete stream.
    """

    store = IdentityObservationStore(tmp_path / "identity")

    CachedValueProvider(
        provider=ProviderStub(observed(DISPUTED, MONDAY)),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path / "fundamentals", schema=4),
        observations=store,
    ).snapshot_observing("SPCX", BROKER, subject="SPCX")

    append_raw(store, "SPCX", "{not json")

    reading = store.stream("SPCX")

    assert reading.unreadable_records == 1
    assert len(reading.observations) == 1
    assert reading.observations[0].standing is IdentityStanding.UNRESOLVED

    history = IdentityHistory.from_stream("SPCX", reading)

    assert "Currently disputed" not in history.lifecycle_stated
    assert "incomplete" in history.lifecycle_stated


def test_empty_and_incomplete_histories_are_distinct(tmp_path) -> None:
    store = IdentityObservationStore(tmp_path / "identity")

    # Empty: read completely, holds nothing, no lifecycle claimed.
    empty = render(IdentityHistory.from_stream("KO", store.stream("KO")))

    assert "empty history" in empty
    assert "incomplete" not in empty
    assert "Lifecycle:" not in empty

    # Incomplete-and-nothing-readable: a different fact, said differently.
    append_raw(store, "SE", "corrupt")

    broken = render(IdentityHistory.from_stream("SE", store.stream("SE")))

    assert "could not be read" in broken
    assert "empty history" not in broken
    assert "incomplete" in broken


def test_the_cli_discloses_the_skipped_counts(tmp_path) -> None:
    store = acquire_twice(tmp_path)

    append_raw(store, "SPCX", '{"schema": 7, "symbol": "SPCX"}')
    append_raw(store, "SPCX", "corrupt line")

    history = IdentityHistory.from_stream("SPCX", store.stream("SPCX"))
    rendered = render(history)

    assert "2 stored record(s) could not be read" in rendered
    assert "1 unreadable" in rendered
    assert "1 under schema 7" in rendered
    assert "readable ones only" in rendered
    # Both real observations still shown; nothing decision-bearing said.
    assert "SPAC and New Issue ETF" in rendered
    assert DISCLOSURE in rendered


def test_fully_readable_histories_keep_the_three_complete_sentences(
    tmp_path,
) -> None:
    store = acquire_twice(tmp_path)

    history = IdentityHistory.from_stream("SPCX", store.stream("SPCX"))

    assert history.is_complete
    assert history.lifecycle_stated == "Previously disputed; current claims agree."


def test_the_incomplete_sentence_is_in_the_finite_vocabulary() -> None:
    assert any("incomplete" in sentence for sentence in LIFECYCLE_SENTENCES)
    assert len(LIFECYCLE_SENTENCES) == 4


# ── the production route, pinned (correction 3) ─────────────────────


def test_only_the_acquisition_constructs_an_acquiring_provider() -> None:
    """AST over the whole app tree: who can fetch, and who cannot.

    Pins the boundary as it is: exactly one production composition
    builds an acquiring `CachedValueProvider`, and every read surface
    goes through the `stored()` door, which cannot fetch.
    """

    import ast
    import pathlib

    constructs: dict[str, list[str]] = {"acquiring": [], "stored": []}

    for path in pathlib.Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text())

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "CachedValueProvider"
            ):
                constructs["acquiring"].append(path.as_posix())

            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "stored"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "CachedValueProvider"
            ):
                constructs["stored"].append(path.as_posix())

    assert constructs["acquiring"] == ["app/services/market_acquisition_service.py"], (
        "a second production composition can fetch"
    )

    assert sorted(set(constructs["stored"])) == [
        "app/api/routes/executive.py",
        # The price-history provider asks it one question and never
        # about a figure: whether the vendor's own name for a crypto
        # pair listing is this token. It is the one thing here that
        # does reach the network, so its identity check must not.
        "app/providers/yahoo_price_history.py",
        "app/services/company_facts_service.py",
        "app/services/token_facts_service.py",
    ], "a read surface stopped using the stored door"


def test_the_observing_door_has_exactly_one_production_caller() -> None:
    """`snapshot_observing` is called from the acquisition and nowhere else."""

    import ast
    import pathlib

    callers = []

    for path in pathlib.Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text())

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "snapshot_observing"
            ):
                callers.append(path.as_posix())

    assert callers == ["app/services/market_acquisition_service.py"]


def test_the_plain_door_is_reached_only_without_a_broker_claim() -> None:
    """Inside `_fundamentals`, the observing call sits under the
    broker-claim guard and the plain call is the brokerless fall-through
    — a market-strip instrument, which no broker describes."""

    import ast
    import pathlib

    tree = ast.parse(
        pathlib.Path("app/services/market_acquisition_service.py").read_text()
    )

    fundamentals = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_fundamentals"
    )

    guarded = [
        node
        for node in ast.walk(fundamentals)
        if isinstance(node, ast.If)
        and any(
            isinstance(name, ast.Name) and name.id == "broker"
            for name in ast.walk(node.test)
        )
    ]

    assert len(guarded) == 1, "one broker-claim guard"

    inside = {
        call.func.attr
        for call in ast.walk(guarded[0])
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    }

    assert "snapshot_observing" in inside
    assert "snapshot" not in inside, "the plain door is not under the guard"

    everywhere = [
        call.func.attr
        for call in ast.walk(fundamentals)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr in ("snapshot", "snapshot_observing")
    ]

    assert sorted(everywhere) == ["snapshot", "snapshot_observing"]
