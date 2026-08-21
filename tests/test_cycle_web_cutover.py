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


# ── the backend must always satisfy the strict frontend contract ────


#: Every key the strict TypeScript parser requires, with the JSON types
#: it accepts. The frontend rejects anything else outright, so a backend
#: that stopped emitting one of these would blank the homepage — and
#: only this test, which runs in CI, would catch it. The frontend suite
#: does not: CI has no node step.
REQUIRED_CONTRACT: dict[str, tuple[type, ...]] = {
    "execution": (str,),
    "stages": (list,),
    "comparison_prior_cycle_id": (str,),
    "comparison_because": (str,),
    "securities_asked": (int,),
    "securities_priced": (int,),
    "refusals": (list,),
    "newly_produced": (list,),
    "changed": (list,),
    "unchanged": (list,),
    "attention": (list,),
    "courses": (list,),
    "stream_complete": (bool,),
    "unreadable_records": (int,),
    "unsupported_schemas": (int,),
    "lifecycle_anomalies": (int,),
}

#: Keys the parser accepts as null, and only these.
NULLABLE = {
    "cycle_id",
    "started_at",
    "finished_at",
    "comparison_outcome",
    "no_action_suggested",
    "last_known",
}

COURSE_CONTRACT: dict[str, tuple[type, ...]] = {
    "symbol": (str,),
    "disposition": (str,),
    "rationale": (str,),
    "evidence_as_of": (str,),
    "action_kind": (str,),
    "action_statement": (str,),
    "action_because": (str,),
    "asks_for_something": (bool,),
}


def test_20_every_lifecycle_state_satisfies_the_strict_frontend_contract(
    client: TestClient, store: DailyCycleStore
) -> None:
    """The two sides cannot drift without this failing.

    The frontend now fails closed on a missing or malformed field, which
    is right — and it means a backend that quietly drops one blanks the
    homepage. The frontend suite cannot catch that: CI runs no node
    step. This does.
    """

    scenarios = [
        (CycleStatus.COMPLETE, (summary("KO"),)),
        (CycleStatus.PARTIAL, (summary("PG", "RECOMMEND"),)),
        (CycleStatus.FAILED, ()),
    ]

    for index, (status, decisions) in enumerate(scenarios):
        cycle_id = f"c{index}"
        at = MOMENT + timedelta(hours=index)

        store.append_started(CycleStarted(cycle_id=cycle_id, started_at=at))
        store.append_finished(
            finished(cycle_id, status=status, at=at, decisions=decisions)
        )

        body = client.get("/cycle/latest").json()

        for field, types in REQUIRED_CONTRACT.items():
            assert field in body, f"{status.value}: {field} is absent"
            assert body[field] is not None, f"{status.value}: {field} is null"
            assert isinstance(body[field], types), f"{status.value}: {field}"

        for field in NULLABLE:
            assert field in body, f"{status.value}: {field} is absent entirely"

    # An interrupted record and an empty store must satisfy it too.
    store.append_started(
        CycleStarted(cycle_id="c9", started_at=MOMENT + timedelta(hours=9))
    )

    for body in (client.get("/cycle/latest").json(),):
        for field, types in REQUIRED_CONTRACT.items():
            assert field in body and isinstance(body[field], types), field


def test_21_a_course_and_its_envelope_satisfy_the_strict_contract(
    client: TestClient, store: DailyCycleStore
) -> None:
    from tests.test_capital_action_envelope import envelope as build_envelope

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished(
            "c1",
            decisions=(
                summary(
                    "KO",
                    "RECOMMEND",
                    action_kind="open",
                    envelope=build_envelope("open"),
                ),
            ),
        )
    )

    course = client.get("/cycle/latest").json()["courses"][0]

    for field, types in COURSE_CONTRACT.items():
        assert field in course, field
        assert isinstance(course[field], types), field

    assert "conviction" in course, "nullable, but never absent"

    envelope = course["envelope"]

    for field in (
        "kind",
        "stated",
        "policy_source",
        "policy_version",
        "evidence_ceiling",
        "binding_constraint",
        "because",
        "price_as_of",
        "portfolio_as_of",
        "liquidity",
    ):
        assert isinstance(envelope[field], str), field

    assert isinstance(envelope["named_gaps"], list)
    assert isinstance(envelope["starter_capped"], bool)
    assert "capacity_ceiling_pct" in envelope
    assert "final_pct" in envelope
    assert "quality_authority" in envelope


def test_22_every_timestamp_the_contract_emits_is_parseable(
    client: TestClient, store: DailyCycleStore
) -> None:
    """The parser rejects an unparseable date; the backend must not send one."""

    store.append_started(CycleStarted(cycle_id="c0", started_at=MOMENT))
    store.append_finished(finished("c0", decisions=(summary("KO"),)))
    store.append_started(
        CycleStarted(cycle_id="c1", started_at=MOMENT + timedelta(hours=2))
    )

    body = client.get("/cycle/latest").json()

    for field in ("started_at", "finished_at"):
        value = body[field]

        if value is not None:
            datetime.fromisoformat(value)

    assert body["last_known"] is not None
    datetime.fromisoformat(body["last_known"]["finished_at"])


# ── the cycle records what it already builds ────────────────────────


def portfolio_record(**overrides):
    from app.domain.daily_cycle import (
        RecordedAllocation,
        RecordedHolding,
        RecordedPortfolio,
    )

    values = dict(
        total_value=100_000.0,
        available_cash_usd=25_000.0,
        cash_pct=25.0,
        observed="eToro account response received at 2026-08-20 12:00 UTC",
        holdings=(
            RecordedHolding(symbol="KO", market_value_usd=50_000.0, weight_pct=50.0),
            RecordedHolding(symbol="PG", market_value_usd=25_000.0, weight_pct=25.0),
        ),
        allocations=(
            RecordedAllocation(
                asset="stocks", current_pct=75.0, target_pct=60.0, difference_pct=15.0
            ),
            RecordedAllocation(
                asset="cash", current_pct=25.0, target_pct=15.0, difference_pct=10.0
            ),
        ),
        compliant=False,
    )
    values.update(overrides)

    return RecordedPortfolio(**values)


def test_23_the_recorded_portfolio_round_trips_and_reaches_the_endpoint(
    client: TestClient, store: DailyCycleStore
) -> None:
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished("c1", decisions=(summary("KO"),), portfolio=portfolio_record())
    )

    stored = store.log().records[0].finished

    assert stored is not None
    assert stored.portfolio == portfolio_record(), "exact round-trip"

    body = client.get("/cycle/latest").json()["portfolio"]

    assert body["total_value"] == 100_000.0
    assert body["available_cash_usd"] == 25_000.0
    assert [h["symbol"] for h in body["holdings"]] == ["KO", "PG"]
    assert body["compliant"] is False
    assert body["observed"].startswith("eToro account response received at"), (
        "the receipt-time wording survives into the record and the payload"
    )


def test_24_absent_cash_survives_into_the_record(
    client: TestClient, store: DailyCycleStore
) -> None:
    """#223's rule, carried one layer further out."""

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished(
            "c1",
            decisions=(summary("KO"),),
            portfolio=portfolio_record(available_cash_usd=None, cash_pct=None),
        )
    )

    body = client.get("/cycle/latest").json()["portfolio"]

    assert body["available_cash_usd"] is None
    assert body["cash_pct"] is None

    # And a measured zero stays a measured zero.
    store.append_started(
        CycleStarted(cycle_id="c2", started_at=MOMENT + timedelta(hours=1))
    )
    store.append_finished(
        finished(
            "c2",
            at=MOMENT + timedelta(hours=1),
            decisions=(summary("KO"),),
            portfolio=portfolio_record(available_cash_usd=0.0, cash_pct=0.0),
        )
    )

    measured = client.get("/cycle/latest").json()["portfolio"]

    assert measured["available_cash_usd"] == 0.0
    assert measured["cash_pct"] == 0.0


def test_25_an_unmeasured_allocation_difference_is_never_zero(
    client: TestClient, store: DailyCycleStore
) -> None:
    from app.domain.daily_cycle import RecordedAllocation

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished(
            "c1",
            decisions=(summary("KO"),),
            portfolio=portfolio_record(
                allocations=(
                    RecordedAllocation(
                        asset="cash",
                        current_pct=None,
                        target_pct=15.0,
                        difference_pct=None,
                    ),
                ),
                compliant=None,
            ),
        )
    )

    body = client.get("/cycle/latest").json()["portfolio"]

    assert body["allocations"][0]["difference_pct"] is None
    assert body["allocations"][0]["current_pct"] is None
    assert body["compliant"] is None, "an unread allocation is not compliance"


def covered(symbol: str, conviction: int | None, absent: tuple[str, ...] = ()):
    """A candidate whose conviction states the families it was computed over."""

    return summary(
        symbol,
        conviction=conviction,
        conviction_participating=(None if conviction is None else 5 - len(absent)),
        conviction_expected=(None if conviction is None else 5),
        conviction_absent_families=absent,
    )


def test_26_candidates_are_ranked_by_conviction_highest_first(
    client: TestClient, store: DailyCycleStore
) -> None:
    """Ranked — because every conviction here covers the same families."""

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        finished(
            "c1",
            decisions=(summary("KO"),),
            candidates=(
                covered("AAA", 41),
                covered("BBB", 88),
                covered("CCC", None),
                covered("DDD", 63),
            ),
        )
    )

    body = client.get("/cycle/latest").json()
    ranked = [c["symbol"] for c in body["candidates"]]

    assert body["candidates_ranked"] is True
    assert ranked[:3] == ["BBB", "DDD", "AAA"]
    assert ranked[-1] == "CCC", (
        "a candidate with no conviction is never ranked above one that has it"
    )


def test_27_no_candidates_means_none_were_evaluated(
    client: TestClient, store: DailyCycleStore
) -> None:
    """The distinction a surface must not collapse."""

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    body = client.get("/cycle/latest").json()

    assert body["candidates"] == []
    # Nothing in the payload claims a judgment about them.
    assert "no_opportunities" not in body
    assert "nothing worth" not in client.get("/cycle/latest").text.lower()


def test_28_a_record_without_the_new_fields_still_decodes(
    tmp_path,
) -> None:
    """Backward compatible under the same schema, as the envelope was."""

    import json

    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(finished("c1", decisions=(summary("KO"),)))

    path = store.path
    lines = []

    for line in path.read_text().splitlines():
        row = json.loads(line)

        if row.get("kind") == "finished":
            # A record written before either field existed.
            row.pop("portfolio", None)
            row.pop("candidates", None)

        lines.append(json.dumps(row))

    path.write_text("\n".join(lines) + "\n")

    log = store.log()

    assert log.unreadable_records == 0
    assert log.records[0].finished is not None
    assert log.records[0].finished.portfolio is None
    assert log.records[0].finished.candidates == ()


def test_29_a_cycle_pays_for_candidates_only_when_asked() -> None:
    """The budget is explicit, and defaults to none."""

    import inspect

    from app.commands.cycle import run

    signature = inspect.signature(run)

    assert signature.parameters["candidates"].default == 0, (
        "no existing cycle costs more than it did"
    )

    source = inspect.getsource(run)

    assert "candidate_limit=candidates" in source, (
        "the budget reaches the brain builder rather than being ignored"
    )
    assert "if candidates > 0:" in source, "and nothing is evaluated without one"
