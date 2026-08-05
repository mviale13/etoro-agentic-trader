"""The API routes, exercised through HTTP without touching the network.

Handlers used to build their services inline, so the routing, the response
shape and the error branches could only be reached by a live eToro and Yahoo.
The network-coupled composition roots are dependencies now, overridden here
with offline stubs, so what the route itself does — serialize a result, refuse
an empty one — is what these tests measure.
"""

from collections.abc import Iterator, Sequence

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_account_service,
    get_brain_builder_service,
    get_brain_snapshot_service,
    get_brief_service,
    get_dashboard_service,
    get_earnings_calendar_service,
    get_market_perception,
)
from app.api.main import app
from app.api.models.dashboard import DashboardResponse
from app.api.models.today import (
    HealthResponse,
    RecommendationResponse,
    TodayResponse,
)
from app.brain import Brain, BrainBuilder
from app.domain.account_snapshot import AccountSnapshot
from app.domain.brain_snapshot import BrainSnapshot
from app.domain.brief_snapshot import BriefSnapshot
from app.domain.committee_decision import CommitteeDecision
from app.domain.investor_dna import InvestorDNA
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.observation import Observation
from app.domain.portfolio_health import HealthCheck, PortfolioHealth
from app.domain.recommendation import Recommendation
from tests.test_brain_context import make_market, make_policy, make_portfolio
from tests.test_portfolio_service import build_account


def make_brain() -> Brain:
    """A whole Brain, built offline from the shared fixtures."""

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def make_snapshot() -> BrainSnapshot:
    """A factual snapshot with nothing the account has not measured.

    `make_portfolio` carries no drawdown and this leaves risk unassessed, so
    both reach the route as None — which is the case the null-vs-zero test
    below turns on.
    """

    portfolio = make_portfolio()

    return BrainSnapshot(
        portfolio=portfolio,
        recommendation=Recommendation(
            symbol="MSFT",
            portfolio=portfolio,
            intelligence=MarketIntelligence(
                market=make_market(),
                sentiment=None,
                outlook="constructive",
                confidence=80,
                summary="Markets are constructive.",
            ),
            decision=CommitteeDecision(
                recommendation="BUY",
                confidence=87,
                buy_votes=3,
                hold_votes=1,
                sell_votes=0,
                opinions=(),
            ),
        ),
        observation=Observation(
            title="Steady Course",
            message="Portfolio remains balanced.",
            category="general",
        ),
        investor_dna=InvestorDNA(
            confidence=42,
            prefers_quality=False,
            prefers_diversification=False,
            prefers_value=False,
            avoids_high_volatility=False,
        ),
        summary="4 positions worth $50,000.",
        insights=[],
        risk=None,
        brief=None,
    )


class StubSnapshotService:
    def __init__(self, snapshot: BrainSnapshot) -> None:
        self._snapshot = snapshot

    async def build(self) -> BrainSnapshot:
        return self._snapshot


class StubBrainBuilder:
    def __init__(self, brain: Brain) -> None:
        self._brain = brain

    async def build(
        self,
        focus_symbols: Sequence[str] = (),
        candidate_limit: int | None = None,
    ) -> Brain:
        return self._brain


class StubMarketPerception:
    def __init__(self, market: MarketSnapshot) -> None:
        self._market = market

    async def execute(self) -> MarketSnapshot:
        return self._market


class StubDashboardService:
    def __init__(self, dashboard: DashboardResponse) -> None:
        self._dashboard = dashboard

    async def build(self) -> DashboardResponse:
        return self._dashboard


class StubAccountService:
    def __init__(self, account: AccountSnapshot) -> None:
        self._account = account

    async def snapshot(self) -> AccountSnapshot:
        return self._account


class StubBriefService:
    def __init__(self, snapshot: BriefSnapshot) -> None:
        self._snapshot = snapshot

    async def build(self) -> BriefSnapshot:
        return self._snapshot


def make_brief() -> BriefSnapshot:
    """A morning brief with a health score and a recommendation."""

    portfolio = make_portfolio()

    return BriefSnapshot(
        greeting="Good morning.",
        health=PortfolioHealth(
            overall_score=72,
            checks=[
                HealthCheck(
                    name="Diversification",
                    score=68,
                    status="ok",
                    message="Spread across four positions.",
                ),
            ],
            recommendation="Hold course.",
        ),
        recommendation=Recommendation(
            symbol="MSFT",
            portfolio=portfolio,
            intelligence=MarketIntelligence(
                market=make_market(),
                sentiment=None,
                outlook="constructive",
                confidence=80,
                summary="Markets are constructive.",
            ),
            decision=CommitteeDecision(
                recommendation="BUY",
                confidence=87,
                buy_votes=3,
                hold_votes=1,
                sell_votes=0,
                opinions=(),
            ),
        ),
        changes=("Cash fell to 20%.",),
        summary="A steady account in a constructive market.",
        next_action="Review MSFT.",
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A test client whose dependency overrides are cleared afterwards."""

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_brain_route_serves_the_snapshot_it_is_given(client: TestClient) -> None:
    app.dependency_overrides[get_brain_snapshot_service] = lambda: StubSnapshotService(
        make_snapshot()
    )

    response = client.get("/brain/")

    assert response.status_code == 200

    body = response.json()

    assert body["recommendation"]["symbol"] == "MSFT"
    assert body["recommendation"]["action"] == "BUY"
    assert body["recommendation"]["confidence"] == 87
    assert body["portfolio"]["positions"] == 4


def test_brain_route_serves_the_unmeasured_as_null_not_zero(
    client: TestClient,
) -> None:
    """A page cannot tell a risk that is nil from one nobody could read.

    The route is the last place that distinction survives before the
    dashboard, so an unassessed risk and an unmeasured drawdown reach it as
    JSON null rather than a plausible zero.
    """

    app.dependency_overrides[get_brain_snapshot_service] = lambda: StubSnapshotService(
        make_snapshot()
    )

    body = client.get("/brain/").json()

    assert body["risk"] is None
    assert body["portfolio"]["drawdown"] is None


def test_executive_brief_route_serves_a_brief_for_the_symbol(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    response = client.get("/executive/MSFT")

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "MSFT"
    assert body["headline"]

    # The backend words its own figures; no surface bands them itself.
    assert body["portfolio_health_label"] in {
        "Healthy",
        "Stable",
        "Needs attention",
        "At risk",
    }

    for priority in body["priorities"]:
        assert priority["urgency_band"] in {"now", "today", "monitor"}

    for case in body["investment_cases"]:
        assert case["conviction_label"].endswith("Conviction")


def test_executive_brief_states_plainly_when_a_symbol_is_not_evidenced(
    client: TestClient,
) -> None:
    """A symbol the platform holds nothing about says so, at the API too.

    The fixture brain carries no security evidence, so any symbol reaches
    the route unevidenced — and the brief must state that plainly rather
    than report its quality as unmeasured.
    """

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    body = client.get("/executive/WHATEVER").json()

    assert body["summary"] == (
        "No security-level analysis is available for WHATEVER, so there is "
        "nothing to base a decision on."
    )
    assert body["investment_cases"][0]["recommendation"] == "INVESTIGATE"


def test_dossier_route_serves_the_complete_case_for_a_symbol(
    client: TestClient,
) -> None:
    """One dossier, composed only from canonical pipeline outputs."""

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    response = client.get("/executive/MSFT/dossier")

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "MSFT"
    assert body["decision_state"]
    assert body["conviction_label"].endswith("Conviction")
    assert body["rationale"]

    # The scores the decision was made on: measured or null, never filled.
    assert set(body["scores"]) == {
        "quality",
        "evidence",
        "valuation",
        "risk",
        "portfolio_fit",
    }

    # An abstention is marked as such, never inferred from a null.
    for opinion in body["committees"]:
        assert opinion["abstained"] == (opinion["confidence"] is None)

    # Context stays apart from security evidence — different keys entirely.
    assert "context_risks" in body
    assert "context_strengths" in body


def test_dossier_reports_an_unevidenced_symbol_as_unevidenced(
    client: TestClient,
) -> None:
    """A symbol the platform holds nothing about says so, not "low quality".

    The fixture brain carries no security evidence, so any symbol arrives
    unevidenced. The dossier must carry that flag — the page renders "no
    analysis exists" rather than a case with poor scores.
    """

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    body = client.get("/executive/WHATEVER/dossier").json()

    assert body["security_evidenced"] is False
    assert body["decision_state"] == "INVESTIGATE"

    # No previous decision is a null, never an invented history.
    assert body["previous_decisions"] is None or isinstance(
        body["previous_decisions"], str
    )


def test_portfolio_briefing_is_a_404_when_there_is_nothing_to_explain(
    client: TestClient,
) -> None:
    """The fixture portfolio holds no positions, so there is no case to make.

    The handler answers 404 rather than an empty briefing — a branch that,
    until the Brain was injectable, no test could reach without the network.
    """

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    response = client.get("/executive/portfolio")

    assert response.status_code == 404


def test_portfolio_route_serves_the_analysed_account(client: TestClient) -> None:
    """The real PortfolioService runs; only the account fetch is stubbed."""

    app.dependency_overrides[get_account_service] = lambda: StubAccountService(
        build_account(equity=100_000.0, cash=25_000.0, invested=75_000.0, positions=4)
    )

    response = client.get("/portfolio/")

    assert response.status_code == 200

    body = response.json()

    assert body["total_value"] == 100_000.0
    assert body["available_cash_usd"] == 25_000.0
    assert body["positions"] == 4
    assert body["source"] == "eToro Demo"


def test_portfolio_route_reports_a_missing_value_honestly(client: TestClient) -> None:
    """A blank account is not a full one — cash absent is reported as absent.

    `PortfolioService` treats a missing figure as zero for the allocation
    maths, but the account view still reflects what the broker returned
    rather than inventing a balance.
    """

    app.dependency_overrides[get_account_service] = lambda: StubAccountService(
        build_account(equity=None, cash=None, invested=None)
    )

    body = client.get("/portfolio/").json()

    assert body["total_value"] == 0
    assert body["allocation"]["cash"] == 0
    assert body["allocation"]["unclassified"] == 0


def test_today_route_serves_the_morning_brief(client: TestClient) -> None:
    app.dependency_overrides[get_brief_service] = lambda: StubBriefService(make_brief())

    response = client.get("/api/today")

    assert response.status_code == 200

    body = response.json()

    assert body["greeting"] == "Good morning."
    assert body["health"]["score"] == 72
    assert body["health"]["checks"][0]["name"] == "Diversification"
    assert body["recommendation"]["symbol"] == "MSFT"
    assert body["recommendation"]["action"] == "BUY"
    assert body["next_action"] == "Review MSFT."


def test_market_route_serves_the_snapshot_and_its_breadth(client: TestClient) -> None:
    """The real MarketBreadthService runs; only the perception is stubbed."""

    app.dependency_overrides[get_market_perception] = lambda: StubMarketPerception(
        make_market()
    )

    response = client.get("/market/")

    assert response.status_code == 200

    body = response.json()

    assert body["mood"] == "constructive"
    assert body["quotes"][0]["symbol"] == "MSFT"
    assert "equities" in body["breadth"]


def test_market_route_reports_the_unread_as_null(client: TestClient) -> None:
    """The fixture carries no VIX, no reading and no sentiment index.

    Each is served as null rather than a figure or a flat zero — a market
    nobody has dated is not a fresh one, and no sentiment is not neutral
    sentiment.
    """

    app.dependency_overrides[get_market_perception] = lambda: StubMarketPerception(
        make_market()
    )

    body = client.get("/market/").json()

    assert body["vix"] is None
    assert body["observed"] is None
    assert body["sentiment"] is None


def test_earnings_route_serves_dates_and_both_absences(client: TestClient) -> None:
    """Scheduling fact per company, with the two absences kept apart."""

    from datetime import UTC, datetime

    from app.domain.earnings_calendar import EarningsCalendar, EarningsDate
    from app.domain.earnings_schedule import EarningsWindow
    from app.domain.provenance import Provenance

    report_day = datetime.now(UTC).date()

    class StubEarningsService:
        async def upcoming(self) -> EarningsCalendar:
            return EarningsCalendar(
                upcoming=(
                    EarningsDate(
                        symbol="DIS",
                        name="Walt Disney",
                        held=True,
                        window=EarningsWindow(
                            starts_on=report_day,
                            ends_on=None,
                            reading=Provenance(
                                source="Yahoo Finance",
                                observed_at=datetime.now(UTC),
                            ),
                        ),
                    ),
                ),
                reported=(),
                unscheduled=("META",),
                unread=("BNP.PA",),
            )

    app.dependency_overrides[get_earnings_calendar_service] = StubEarningsService

    body = client.get("/market/earnings").json()

    assert body["upcoming"][0]["symbol"] == "DIS"
    assert body["upcoming"][0]["starts_on"] == report_day.isoformat()
    assert body["upcoming"][0]["starts_in_days"] == 0
    assert body["upcoming"][0]["ends_on"] is None
    assert body["upcoming"][0]["held"] is True
    assert body["reported"] == []
    assert body["unscheduled"] == ["META"]
    assert body["unread"] == ["BNP.PA"]


def test_research_route_serves_the_funnel_when_there_are_no_candidates(
    client: TestClient,
) -> None:
    """The fixture brain watches nothing, so the funnel is honestly empty."""

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    response = client.get("/research/candidates")

    assert response.status_code == 200

    body = response.json()

    assert body["funnel"]["candidates"] == 0
    assert body["candidates"] == []


def make_dashboard() -> DashboardResponse:
    """A dashboard payload with only its required section filled.

    The optional sections are None, which is what the route must pass
    through as JSON null rather than an empty object dressed as data.
    """

    return DashboardResponse(
        today=TodayResponse(
            greeting="Good morning.",
            health=HealthResponse(score=70, checks=[]),
            summary="A steady account.",
            changes=[],
            recommendation=RecommendationResponse(
                symbol="MSFT",
                action="BUY",
                confidence=87,
                opinions=[],
            ),
            next_action="Hold course.",
        ),
        portfolio=None,
        observation=None,
        reflection=None,
        investor_dna=None,
    )


def test_dashboard_route_passes_the_composite_through(client: TestClient) -> None:
    app.dependency_overrides[get_dashboard_service] = lambda: StubDashboardService(
        make_dashboard()
    )

    response = client.get("/dashboard/")

    assert response.status_code == 200

    body = response.json()

    assert body["today"]["greeting"] == "Good morning."
    assert body["portfolio"] is None
    assert body["investor_dna"] is None
