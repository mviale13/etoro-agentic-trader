"""The homepage reads a recorded cycle; it no longer makes one.

`/executive/portfolio` builds a Brain, runs the executive pipeline and
appends `DecisionJournal` entries — during the page request. So opening
the homepage acquired evidence, produced decisions and wrote journal
events, which meant **page traffic and not the cycle** was the origin of
what the investor read, and two visits could disagree for reasons that
had nothing to do with the account.

These pin the replacement: one read of the append-only store, every
lifecycle and comparison state rendered distinctly, no security lost,
and a newer failure never hidden behind an older success.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_daily_cycle_store
from app.api.main import app
from app.api.models.cycle import CycleExecution, CycleReviewResponse
from app.domain.daily_cycle import (
    NO_ACTION,
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    StageOutcome,
)
from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

MOMENT = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def summary(symbol: str, state: str = "PREPARE", **overrides) -> DecisionSummary:
    values = dict(
        symbol=symbol,
        state=state,
        rationale=f"{symbol} rationale",
        action_kind="hold",
        action_statement="Keep the position as it is.",
        action_because="nothing moved",
        asks_for_something=False,
    )
    values.update(overrides)

    return DecisionSummary(**values)


def finished(
    cycle_id: str,
    *,
    status: CycleStatus = CycleStatus.COMPLETE,
    at: datetime = MOMENT,
    decisions: tuple[DecisionSummary, ...] = (),
    comparison: ComparisonBasis | None = None,
    stages: tuple[CycleStage, ...] | None = None,
    **overrides,
) -> CycleFinished:
    return CycleFinished(
        cycle_id=cycle_id,
        finished_at=at,
        status=status,
        stages=(
            stages
            if stages is not None
            else (CycleStage(name="decisions", outcome=StageOutcome.RAN),)
        ),
        decisions=decisions,
        comparison=(
            comparison
            if comparison is not None
            else ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE)
        ),
        **overrides,
    )


@pytest.fixture
def store(tmp_path) -> DailyCycleStore:
    return DailyCycleStore(tmp_path / "cycles")


@pytest.fixture
def client(store: DailyCycleStore) -> Iterator[TestClient]:
    app.dependency_overrides[get_daily_cycle_store] = lambda: store

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ── the cutover itself ──────────────────────────────────────────────


def test_1_the_route_reaches_no_builder_pipeline_journal_or_provider() -> None:
    """Absent, not merely unused: no import a later edit could call."""

    import ast
    import pathlib

    source = pathlib.Path("app/api/routes/cycle.py").read_text()
    tree = ast.parse(source)

    imported = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    for banned in (
        "brain_builder",
        "executive_pipeline",
        "decision_journal",
        "portfolio_briefing",
        "provider",
        "market_acquisition",
    ):
        assert not any(banned in module for module in imported), banned

    # And the projection beneath it is pure: no I/O in the model module.
    model = pathlib.Path("app/api/models/cycle.py").read_text()

    for banned in ("requests", "httpx", "open(", "Path("):
        assert banned not in model, banned


def test_2_the_homepage_no_longer_sources_decisions_from_the_pipeline() -> None:
    """Scanned over code, not prose.

    The page's own comment names the endpoint it stopped calling, and a
    raw-text scan would read that explanation as the call it forbids —
    the same literal-versus-source trap this repository has recorded
    repeatedly. Comments are stripped first.
    """

    import pathlib
    import re

    page = pathlib.Path("apps/web/movrvest-web/app/page.tsx").read_text()
    code = re.sub(r"/\*.*?\*/", "", page, flags=re.S)
    code = re.sub(r"^\s*//.*$", "", code, flags=re.M)

    assert "getCycleReview" in code
    assert "getExecutiveWorkspace" not in code, (
        "the homepage must not call the endpoint that builds decisions"
    )
    assert "executive/portfolio" not in code
    assert "/brain/" not in code, "nor the endpoint that acquires"


def test_3_a_page_visit_appends_no_cycle_event(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    before = store.path.read_bytes()

    for _ in range(3):
        assert client.get("/cycle/latest").status_code == 200

    assert store.path.read_bytes() == before, "a read wrote to the store"


def test_4_repeated_visits_are_byte_stable(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished("c1", decisions=(summary("KO"), summary("PG", "RECOMMEND")))
    )

    bodies = {client.get("/cycle/latest").text for _ in range(4)}

    assert len(bodies) == 1, "an unchanged store produced differing payloads"


# ── every lifecycle and comparison state renders distinctly ─────────


def test_5_no_cycle_recorded(client: TestClient) -> None:
    body = client.get("/cycle/latest").json()

    assert body["execution"] == CycleExecution.NONE_RECORDED.value
    assert body["courses"] == []
    assert body["no_action_suggested"] is None, "silence is not a quiet day"
    assert body["last_known"] is None


def test_6_an_interrupted_latest_attempt_is_shown_as_interrupted(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))

    body = client.get("/cycle/latest").json()

    assert body["execution"] == CycleExecution.INTERRUPTED.value
    assert body["execution"] not in (
        CycleExecution.COMPLETE.value,
        CycleExecution.FAILED.value,
    )
    assert body["no_action_suggested"] is None


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (CycleStatus.FAILED, CycleExecution.FAILED),
        (CycleStatus.PARTIAL, CycleExecution.PARTIAL),
        (CycleStatus.COMPLETE, CycleExecution.COMPLETE),
    ],
    ids=["failed", "partial", "complete"],
)
def test_7_each_terminal_status_renders_as_itself(
    client: TestClient,
    store: DailyCycleStore,
    status: CycleStatus,
    expected: CycleExecution,
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", status=status, decisions=(summary("KO"),)))

    assert client.get("/cycle/latest").json()["execution"] == expected.value


@pytest.mark.parametrize(
    "basis",
    [
        ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
        ComparisonBasis(outcome=ComparisonOutcome.COMPARED, prior_cycle_id="c0"),
        ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED, because="the stream is incomplete"
        ),
    ],
    ids=["initial_baseline", "compared", "refused"],
)
def test_8_each_comparison_basis_renders_as_itself(
    client: TestClient, store: DailyCycleStore, basis: ComparisonBasis
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),), comparison=basis))

    body = client.get("/cycle/latest").json()

    assert body["comparison_outcome"] == basis.outcome.value
    assert body["comparison_prior_cycle_id"] == basis.prior_cycle_id
    assert body["comparison_because"] == basis.because


def test_9_an_incomplete_stream_is_disclosed(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write("{not json at all\n")

    body = client.get("/cycle/latest").json()

    assert body["stream_complete"] is False
    assert body["unreadable_records"] >= 1


# ── the two claims that must never be manufactured ──────────────────


def test_10_no_action_is_said_only_through_the_domain_predicate(
    client: TestClient, store: DailyCycleStore
) -> None:
    """A complete, compared, quiet cycle earns the sentence."""

    store.append_started(CycleStarted(cycle_id="c0", started_at=MOMENT))
    store.append_finished(finished("c0", decisions=(summary("KO"),)))
    store.append_started(
        CycleStarted(cycle_id="c1", started_at=MOMENT + timedelta(hours=1))
    )
    store.append_finished(
        finished(
            "c1",
            at=MOMENT + timedelta(hours=1),
            decisions=(summary("KO"),),
            comparison=ComparisonBasis(
                outcome=ComparisonOutcome.COMPARED, prior_cycle_id="c0"
            ),
            unchanged=("KO",),
        )
    )

    assert client.get("/cycle/latest").json()["no_action_suggested"] == NO_ACTION


@pytest.mark.parametrize(
    "basis",
    [
        ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
        ComparisonBasis(outcome=ComparisonOutcome.REFUSED, because="incomplete"),
    ],
    ids=["initial-is-not-unchanged", "refused-is-not-unchanged"],
)
def test_11_an_unclassified_day_never_earns_the_sentence(
    client: TestClient, store: DailyCycleStore, basis: ComparisonBasis
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),), comparison=basis))

    assert client.get("/cycle/latest").json()["no_action_suggested"] is None


def test_12_a_degraded_day_never_earns_the_sentence(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished(
            "c1",
            status=CycleStatus.PARTIAL,
            decisions=(summary("KO"),),
            comparison=ComparisonBasis(
                outcome=ComparisonOutcome.COMPARED, prior_cycle_id="c0"
            ),
        )
    )

    assert client.get("/cycle/latest").json()["no_action_suggested"] is None


# ── a newer failure is never hidden behind an older success ─────────


def test_13_a_failed_latest_attempt_stays_visible_and_dates_the_older_one(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c0", started_at=MOMENT))
    store.append_finished(finished("c0", decisions=(summary("KO"), summary("PG"))))

    later = MOMENT + timedelta(hours=2)
    store.append_started(CycleStarted(cycle_id="c1", started_at=later))
    store.append_finished(
        finished(
            "c1",
            status=CycleStatus.FAILED,
            at=later,
            stages=(
                CycleStage(
                    name="decisions",
                    outcome=StageOutcome.FAILED,
                    because="the decisions stage failed (RuntimeError)",
                ),
            ),
        )
    )

    body = client.get("/cycle/latest").json()

    assert body["execution"] == CycleExecution.FAILED.value
    assert body["cycle_id"] == "c1", "the newer attempt is what is described"

    last_known = body["last_known"]

    assert last_known is not None, "the older cycle is offered, not substituted"
    assert last_known["cycle_id"] == "c0"
    assert last_known["finished_at"], "and it carries its own date"
    assert {c["symbol"] for c in last_known["courses"]} == {"KO", "PG"}

    # The failed stage's own words survive.
    assert any("decisions stage failed" in s["because"] for s in body["stages"])


def test_14_an_interrupted_latest_attempt_also_dates_the_older_one(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c0", started_at=MOMENT))
    store.append_finished(finished("c0", decisions=(summary("KO"),)))
    store.append_started(
        CycleStarted(cycle_id="c1", started_at=MOMENT + timedelta(hours=2))
    )

    body = client.get("/cycle/latest").json()

    assert body["execution"] == CycleExecution.INTERRUPTED.value
    assert body["last_known"]["cycle_id"] == "c0"


def test_15_a_successful_latest_cycle_offers_no_last_known(
    client: TestClient, store: DailyCycleStore
) -> None:
    """Nothing stale travels beside a current result."""

    store.append_started(CycleStarted(cycle_id="c0", started_at=MOMENT))
    store.append_finished(finished("c0", decisions=(summary("KO"),)))
    store.append_started(
        CycleStarted(cycle_id="c1", started_at=MOMENT + timedelta(hours=2))
    )
    store.append_finished(
        finished("c1", at=MOMENT + timedelta(hours=2), decisions=(summary("KO"),))
    )

    assert client.get("/cycle/latest").json()["last_known"] is None


# ── every stored security survives, with its course ─────────────────


def test_16_no_security_disappears_and_each_course_is_carried_verbatim(
    client: TestClient, store: DailyCycleStore
) -> None:
    from app.domain.capital_envelope import EnvelopeKind
    from tests.test_capital_action_envelope import envelope as build_envelope

    stored = (
        summary(
            "KO",
            "RECOMMEND",
            action_kind="open",
            asks_for_something=True,
            action_statement="Consider opening a position.",
            envelope=build_envelope("open"),
        ),
        summary("PG", "PREPARE"),
        summary(
            "TSLA",
            "REJECT",
            action_kind="wait",
            action_statement="Wait.",
            conviction=41,
            evidence_as_of="Yahoo Finance, 2 hours ago",
        ),
    )

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished("c1", decisions=stored, refusals=("HYPE: no price came back",))
    )

    body = client.get("/cycle/latest").json()
    courses = {item["symbol"]: item for item in body["courses"]}

    assert set(courses) == {"KO", "PG", "TSLA"}, "no security was dropped"

    assert courses["KO"]["action_statement"] == "Consider opening a position."
    assert courses["KO"]["asks_for_something"] is True
    assert courses["KO"]["envelope"]["kind"] == EnvelopeKind.UPWARD_BOUNDED.value
    assert courses["KO"]["envelope"]["stated"], "the domain's own sentence travels"

    assert courses["PG"]["envelope"] is None, "a non-capital course carries none"
    assert courses["TSLA"]["conviction"] == 41
    assert courses["TSLA"]["evidence_as_of"] == "Yahoo Finance, 2 hours ago"

    assert body["refusals"] == ["HYPE: no price came back"]


def test_17_the_projection_is_a_pure_function_of_the_log(
    store: DailyCycleStore,
) -> None:
    """No route, no client: the mapping itself is testable and total."""

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    log = store.log()

    first = CycleReviewResponse.from_log(log)
    second = CycleReviewResponse.from_log(log)

    assert first == second
    assert first.execution is CycleExecution.COMPLETE


def test_18_a_page_visit_makes_no_outbound_network_call(
    client: TestClient, store: DailyCycleStore, monkeypatch
) -> None:
    """Behavioural, not structural: every real transport raises if touched.

    Patched at the *transport* layer, not at `Client.request`. TestClient
    is itself an httpx client speaking ASGI in-process, so forbidding
    `httpx.Client.request` would forbid the test's own call to the app
    and prove nothing. `HTTPTransport` is the one that opens a socket.
    """

    import httpx
    import requests

    def forbidden(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("a homepage read attempted a network call")

    for target, attribute in (
        (httpx.HTTPTransport, "handle_request"),
        (httpx.AsyncHTTPTransport, "handle_async_request"),
        (requests.adapters.HTTPAdapter, "send"),
    ):
        monkeypatch.setattr(target, attribute, forbidden, raising=False)

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    assert client.get("/cycle/latest").status_code == 200


def test_19_a_page_visit_writes_nothing_anywhere_under_the_evidence_root(
    client: TestClient, store: DailyCycleStore, tmp_path, monkeypatch
) -> None:
    """No journal entry, no event, no file of any kind."""

    from app.infrastructure.evidence_root import ROOT_ENV

    root = tmp_path / "evidence"
    root.mkdir()
    monkeypatch.setenv(ROOT_ENV, str(root))

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    before = sorted(path.name for path in root.rglob("*"))

    for _ in range(3):
        assert client.get("/cycle/latest").status_code == 200

    assert sorted(path.name for path in root.rglob("*")) == before, (
        "a page view created evidence"
    )
