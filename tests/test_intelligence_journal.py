"""The intelligence journal: what was observed, when, and how often.

The ten acceptance demonstrations the ruling asked for, each as a named
test, plus the boundaries. Every case is built from controlled captures
rather than from live evidence — a temporal layer tested against a
moving corpus proves nothing, because the thing under test is precisely
what happens *between* two readings.

The two that matter most cannot be read off the code:

- an **unavailable** reading must never become an economic observation,
  because *"holdings fell to zero"* assembled out of a provider outage
  is a lie made of true parts;
- and **three captures are not three weeks**, so every temporal sentence
  is worded from a count of captures and a largest gap rather than from
  a duration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.domain.crypto_intelligence import ClaimType, EventKind
from app.domain.intelligence_journal import (
    Capture,
    ChangeNature,
    JournalEntry,
    ObservationStatus,
    TemporalStatus,
    capture_id_for,
    project,
)
from app.infrastructure.evidence.intelligence_journal_store import (
    IntelligenceJournalStore,
)
from app.services.intelligence_journal_service import IntelligenceJournalService
from tests.reachability import reachable

DAY = timedelta(days=1)
START = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _entry(
    capture_id: str,
    at: datetime,
    key: str = "flow.30d",
    stated: str = "Funds took $128m net.",
    value: float | None = 128_000_000.0,
    unit: str | None = "USD",
    status: ObservationStatus = ObservationStatus.OBSERVED,
    source: str = "SoSoValue",
    source_at: datetime | None = None,
) -> JournalEntry:
    return JournalEntry(
        capture_id=capture_id,
        asset="BTC",
        captured_at=at,
        key=key,
        family=EventKind.CAPITAL_FLOW,
        claim_type=ClaimType.MEASURED,
        status=status,
        stated=stated,
        value=value,
        unit=unit,
        source=source,
        source_observed_at=source_at if source_at is not None else at,
    )


def _capture(index: int, at: datetime, *entries: JournalEntry) -> Capture:
    return Capture(
        capture_id=f"c{index}",
        asset="BTC",
        captured_at=at,
        entries=entries,
    )


def _store(tmp_path: Path) -> IntelligenceJournalStore:
    return IntelligenceJournalStore(root=tmp_path / "journal")


# ── 1: unchanged evidence is not a new development ──────────────────


def test_unchanged_evidence_does_not_become_a_development() -> None:
    """Acceptance 1.

    Three captures reading the same figure are one observation seen
    three times. A layer that reported a change per capture would
    manufacture two developments out of a quiet week.
    """

    history = [
        _capture(i, START + i * DAY, _entry(f"c{i}", START + i * DAY)) for i in range(3)
    ]

    facts = project("BTC", history)

    assert len(facts) == 1
    assert facts[0].status is TemporalStatus.STILL_PRESENT
    assert facts[0].run_length == 3
    assert not facts[0].status.is_change


# ── 2: a genuine measured change is detected ────────────────────────


def test_a_measured_change_is_detected_with_its_direction() -> None:
    """Acceptance 2, and the direction only where a measurement supports
    one."""

    facts = project(
        "BTC",
        [
            _capture(0, START, _entry("c0", START, value=128_000_000.0)),
            _capture(
                1,
                START + DAY,
                _entry("c1", START + DAY, value=540_000_000.0),
            ),
        ],
    )

    assert facts[0].status is TemporalStatus.INCREASED
    assert facts[0].previous_value == 128_000_000.0
    assert facts[0].current_value == 540_000_000.0
    assert "$128m" in facts[0].stated


def test_a_qualitative_change_has_no_direction() -> None:
    """§2: no universal numeric representation is invented just to make
    comparison easier. A regulatory action that changed is `CHANGED`."""

    facts = project(
        "BTC",
        [
            _capture(
                0,
                START,
                _entry(
                    "c0",
                    START,
                    key="reg",
                    stated="Registration suspended.",
                    value=None,
                    unit=None,
                ),
            ),
            _capture(
                1,
                START + DAY,
                _entry(
                    "c1",
                    START + DAY,
                    key="reg",
                    stated="Registration reinstated.",
                    value=None,
                    unit=None,
                ),
            ),
        ],
    )

    assert facts[0].status is TemporalStatus.CHANGED
    assert facts[0].current_value is None


# ── 3: new versus changed ───────────────────────────────────────────


def test_a_new_finding_is_distinguishable_from_a_changed_one() -> None:
    """Acceptance 3."""

    facts = {
        fact.key: fact
        for fact in project(
            "BTC",
            [
                _capture(0, START, _entry("c0", START)),
                _capture(
                    1,
                    START + DAY,
                    _entry("c1", START + DAY, value=200_000_000.0),
                    _entry("c1", START + DAY, key="holdings", value=1_223_634.0),
                ),
            ],
        )
    }

    assert facts["flow.30d"].status is TemporalStatus.INCREASED
    assert facts["holdings"].status is TemporalStatus.FIRST_OBSERVED
    assert facts["holdings"].span.count == 1


# ── 4 and 5: unavailable is not a negative observation ──────────────


def test_unavailable_evidence_is_not_a_measurement() -> None:
    """Acceptance 4 and 5, and the defect this layer exists to prevent.

    A provider outage arriving as *"flows fell to zero"* would be a lie
    assembled out of true parts. An unavailable reading gets its own
    status, is never compared with a value, and says in words that it is
    a fact about the reading rather than about the asset.
    """

    facts = project(
        "BTC",
        [
            _capture(0, START, _entry("c0", START, value=128_000_000.0)),
            _capture(
                1,
                START + DAY,
                _entry(
                    "c1",
                    START + DAY,
                    stated="SoSoValue could not be read.",
                    value=None,
                    unit=None,
                    status=ObservationStatus.UNAVAILABLE,
                ),
            ),
        ],
    )

    assert facts[0].status is TemporalStatus.UNAVAILABLE
    assert facts[0].nature is ChangeNature.READING_CHANGED
    assert facts[0].current_value is None
    assert facts[0].previous_value is None

    assert "not about the asset" in facts[0].stated

    assert facts[0].status is not TemporalStatus.DECREASED


def test_an_unavailable_reading_equals_nothing_including_itself() -> None:
    """Two outages are not a stable observation."""

    outage = _entry(
        "c0", START, value=None, unit=None, status=ObservationStatus.UNAVAILABLE
    )

    assert not outage.same_reading_as(outage)


def test_a_not_applicable_finding_produces_no_temporal_fact() -> None:
    """Hyperliquid has no US spot ETF. That is not a gap in the record."""

    facts = project(
        "BTC",
        [
            _capture(
                0,
                START,
                _entry(
                    "c0",
                    START,
                    stated="No fund group exists.",
                    value=None,
                    unit=None,
                    status=ObservationStatus.NOT_APPLICABLE,
                ),
            )
        ],
    )

    assert facts == ()


def test_a_finding_that_stops_being_produced_is_not_a_change() -> None:
    """Disappeared and unavailable are different: one was not produced,
    the other could not be read."""

    facts = project(
        "BTC",
        [
            _capture(0, START, _entry("c0", START)),
            _capture(
                1,
                START + DAY,
                _entry("c1", START + DAY, key="other", stated="Something else."),
            ),
        ],
    )

    flow = next(fact for fact in facts if fact.key == "flow.30d")

    assert flow.status is TemporalStatus.DISAPPEARED
    assert "not produced by the latest capture" in flow.stated


# ── 6: the world changed vs our evidence changed ────────────────────


def test_a_revision_is_distinguished_from_the_world_moving() -> None:
    """§6, made structural.

    The source's own timestamp decides: a new figure for a later moment
    is the world; a new figure for a moment already reported is the
    source revising itself. Committees consuming temporal evidence will
    need to weigh those very differently.
    """

    settled = datetime(2026, 8, 7, tzinfo=UTC)

    revised = project(
        "BTC",
        [
            _capture(0, START, _entry("c0", START, value=100.0, source_at=settled)),
            _capture(
                1,
                START + DAY,
                _entry("c1", START + DAY, value=120.0, source_at=settled),
            ),
        ],
    )

    assert revised[0].nature is ChangeNature.SOURCE_REVISED
    assert "revised a figure it had already given" in revised[0].stated

    moved = project(
        "BTC",
        [
            _capture(0, START, _entry("c0", START, value=100.0, source_at=settled)),
            _capture(
                1,
                START + DAY,
                _entry("c1", START + DAY, value=120.0, source_at=settled + DAY),
            ),
        ],
    )

    assert moved[0].nature is ChangeNature.WORLD_MOVED


def test_an_undated_source_says_so_rather_than_guessing() -> None:
    """A source that dates nothing cannot be told apart from one that
    revised itself, and the record says that rather than picking."""

    def undated(capture_id: str, at: datetime, value: float) -> JournalEntry:
        return JournalEntry(
            capture_id=capture_id,
            asset="BTC",
            captured_at=at,
            key="flow.30d",
            family=EventKind.CAPITAL_FLOW,
            claim_type=ClaimType.MEASURED,
            status=ObservationStatus.OBSERVED,
            stated="Funds took a net figure.",
            value=value,
            unit="USD",
            source_observed_at=None,
        )

    facts = project(
        "BTC",
        [
            _capture(0, START, undated("c0", START, 100.0)),
            _capture(1, START + DAY, undated("c1", START + DAY, 120.0)),
        ],
    )

    assert facts[0].nature is ChangeNature.UNDETERMINED
    assert "cannot be told apart" in facts[0].stated


# ── 7 (of §5): sparse observation is never continuous monitoring ────


def test_sparse_captures_are_not_rewritten_as_continuous_monitoring() -> None:
    """§5, and the sentence the whole layer is judged on.

    Three captures across twenty-one days with a fourteen-day hole are
    not three weeks of observation. The wording must carry the count and
    the gap, and must never say *"for three weeks"*.
    """

    times = [START, START + 7 * DAY, START + 21 * DAY]

    facts = project(
        "BTC",
        [_capture(i, at, _entry(f"c{i}", at)) for i, at in enumerate(times)],
    )

    stated = facts[0].stated

    assert "on 3 captures" in stated
    assert "spanning 21 day(s)" in stated
    assert "the longest gap between them 14 day(s)" in stated

    # It never claims duration alone.
    assert "for three weeks" not in stated
    assert "for 21 days" not in stated

    assert facts[0].span.count == 3
    assert facts[0].span.largest_gap == 14 * DAY


def test_a_run_is_counted_in_captures_and_never_in_time() -> None:
    facts = project(
        "BTC",
        [
            _capture(i, START + i * 7 * DAY, _entry(f"c{i}", START + i * 7 * DAY))
            for i in range(3)
        ],
    )

    assert facts[0].run_length == 3
    assert "across the last 3 capture(s)" in facts[0].stated


# ── 8: history is immutable ─────────────────────────────────────────


def test_historical_entries_are_unchanged_by_later_runs(tmp_path: Path) -> None:
    """Acceptance 6.

    The record answers *what did MOVRvest know on 1 August*, not *what
    would today's pipeline say about 1 August*. A later capture appends;
    it does not edit.
    """

    store = _store(tmp_path)

    store.append(_capture(0, START, _entry("c0", START, value=100.0)))

    path = store.path_for("BTC")

    first = path.read_text(encoding="utf-8")

    store.append(_capture(1, START + DAY, _entry("c1", START + DAY, value=999.0)))

    after = path.read_text(encoding="utf-8")

    # The original line survives byte for byte.
    assert after.startswith(first)

    held = store.captures("BTC")

    assert len(held) == 2
    assert held[0].entries[0].value == 100.0


def test_replaying_the_same_capture_appends_nothing(tmp_path: Path) -> None:
    store = _store(tmp_path)

    capture = _capture(0, START, _entry("c0", START))

    assert store.append(capture) is True
    assert store.append(capture) is False

    assert len(store.captures("BTC")) == 1


def test_a_correction_is_recorded_rather_than_applied(tmp_path: Path) -> None:
    """§3. A correction is a new entry naming what it corrects — history
    keeps both, because the mistake is itself a fact about this
    platform."""

    store = _store(tmp_path)

    store.append(_capture(0, START, _entry("c0", START, value=100.0)))

    corrected = JournalEntry(
        capture_id="c1",
        asset="BTC",
        captured_at=START + DAY,
        key="flow.30d",
        family=EventKind.CAPITAL_FLOW,
        claim_type=ClaimType.MEASURED,
        status=ObservationStatus.OBSERVED,
        stated="Funds took $110m net.",
        value=110_000_000.0,
        unit="USD",
        corrects="c0:flow.30d",
    )

    store.append(
        Capture(
            capture_id="c1",
            asset="BTC",
            captured_at=START + DAY,
            entries=(corrected,),
        )
    )

    held = store.captures("BTC")

    assert len(held) == 2
    assert held[0].entries[0].value == 100.0
    assert held[1].entries[0].corrects == "c0:flow.30d"


def test_one_unreadable_line_does_not_cost_the_record(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.append(_capture(0, START, _entry("c0", START)))

    path = store.path_for("BTC")

    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json at all\n")

    store.append(_capture(1, START + DAY, _entry("c1", START + DAY)))

    assert len(store.captures("BTC")) == 2


def test_every_line_carries_its_own_schema(tmp_path: Path) -> None:
    """A file that is never rewritten cannot be migrated, so the version
    rides on the line."""

    store = _store(tmp_path)

    store.append(_capture(0, START, _entry("c0", START)))

    row = json.loads(store.path_for("BTC").read_text(encoding="utf-8").splitlines()[0])

    assert row["schema"] == 1
    assert row["capture_id"] == "c0"
    assert row["source_observed_at"]


# ── 9: the synthesis can cite a grounded temporal fact ──────────────


def test_a_temporal_fact_reaches_the_synthesis_as_a_grounded_finding() -> None:
    """Acceptance 7, and §7's rule.

    Code establishes history; the model explains grounded history. So a
    temporal fact arrives as a finding with journal entry ids beneath
    it, and the model can cite it exactly as it cites any other.
    """

    from app.renderers.intelligence_synthesist import build_findings
    from tests.test_intelligence_synthesis import _snapshot

    history = project(
        "BTC",
        [
            _capture(i, START + i * DAY, _entry(f"c{i}", START + i * DAY))
            for i in range(3)
        ],
    )

    findings = build_findings(_snapshot(), history)

    temporal = [finding for finding in findings if finding.id.startswith("H")]

    assert temporal
    assert "on 3 captures" in temporal[0].statement
    assert "recorded observation(s)" in temporal[0].source
    assert "c2:flow.30d" in temporal[0].source


def test_deleting_the_observations_removes_the_claim(tmp_path: Path) -> None:
    """Acceptance 8. The temporal claim is not reconstructable — it is
    unavailable, which is a different and honest state."""

    service = IntelligenceJournalService(store=_store(tmp_path))

    store = _store(tmp_path)

    for index in range(3):
        store.append(
            _capture(
                index,
                START + index * DAY,
                _entry(f"c{index}", START + index * DAY),
            )
        )

    assert service.history("BTC")

    store.path_for("BTC").unlink()

    assert service.history("BTC") == ()

    from app.renderers.intelligence_synthesist import build_findings
    from tests.test_intelligence_synthesis import _snapshot

    findings = build_findings(_snapshot(), service.history("BTC"))

    assert not [finding for finding in findings if finding.id.startswith("H")]


# ── 10: nothing decides ─────────────────────────────────────────────


def test_the_journal_cannot_reach_anything_that_decides() -> None:
    """Acceptance 10, structurally."""

    for module in (
        "app/domain/intelligence_journal.py",
        "app/infrastructure/evidence/intelligence_journal_store.py",
        "app/services/intelligence_journal_service.py",
        "app/commands/intelligence_journal.py",
    ):
        code = reachable(module)

        for forbidden in (
            "crypto_quality",
            "asset_quality",
            "ExecutiveDecision",
            "InvestmentDecision",
            "Recommendation",
            "DecisionSynthesis",
            "CommitteeOpinion",
        ):
            assert forbidden not in code, (module, forbidden)


def test_the_journal_asks_no_model() -> None:
    """§2: the journal must not ask an LLM to remember history, and must
    not store synthesis prose as historical truth."""

    for module in (
        "app/domain/intelligence_journal.py",
        "app/services/intelligence_journal_service.py",
        "app/commands/intelligence_journal.py",
    ):
        code = reachable(module, with_literals=True)

        for forbidden in (
            "openai",
            "anthropic",
            "prompt",
            "IntelligenceSynthesis",
            "SynthesisItem",
            "synthesise",
        ):
            assert forbidden not in code, (module, forbidden)


def test_temporal_status_describes_observations_and_not_meaning() -> None:
    """No temporal status carries investment meaning. `INCREASED` means
    a figure is larger, not that demand strengthened."""

    words = " ".join(status.stated for status in TemporalStatus).lower()

    for forbidden in (
        "bullish",
        "bearish",
        "strong",
        "weak",
        "demand",
        "positive",
        "negative",
    ):
        assert forbidden not in words, forbidden


# ── recording, end to end ───────────────────────────────────────────


def test_a_snapshot_is_recorded_with_absences_and_their_reasons(
    tmp_path: Path,
) -> None:
    """A surface that could not be read is recorded as unreadable rather
    than dropped — otherwise the next capture cannot tell an outage from
    a change."""

    from dataclasses import replace

    from tests.test_intelligence_synthesis import _snapshot

    service = IntelligenceJournalService(store=_store(tmp_path))

    snapshot = replace(
        _snapshot(),
        surfaces_unread=("CoinGecko Insights could not be read — Timeout",),
    )

    capture = service.record(snapshot, now=START)

    assert capture is not None

    unavailable = [
        entry
        for entry in capture.entries
        if entry.status is ObservationStatus.UNAVAILABLE
    ]

    assert len(unavailable) == 1
    assert "could not be read" in unavailable[0].stated


def test_a_capture_id_is_derived_from_content_not_assigned() -> None:
    """Two runs over identical content at the identical moment are one
    capture; the same content an hour later is a second look."""

    first = capture_id_for("BTC", START, "flow=128m")
    same = capture_id_for("BTC", START, "flow=128m")
    later = capture_id_for("BTC", START + DAY, "flow=128m")
    other = capture_id_for("BTC", START, "flow=540m")

    assert first == same
    assert first != later
    assert first != other
