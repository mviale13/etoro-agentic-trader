"""The research pipeline: which watched securities the CIO judges, and why."""

import asyncio
from dataclasses import replace

from app.application.brain.perception.opportunity_perception import (
    OpportunityPerception,
)
from app.application.workspace.candidate_research_service import (
    CandidateResearchService,
)
from app.brain import Brain, BrainBuilder
from app.domain.portfolio_position import PortfolioPosition
from app.domain.research_candidate import ResearchCandidate
from app.domain.watchlist import Watchlist
from app.domain.watchlist_item import WatchlistItem
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)
from tests.test_security_evidence import make_company


def make_item(
    instrument_id: int,
    symbol: str,
    name: str,
) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=name,
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )


class StubWatchlistService:
    """Stands in for the broker; returns watchlists without a network call."""

    def __init__(self, *watchlists: Watchlist) -> None:
        self._watchlists = watchlists

    async def get(self) -> tuple[Watchlist, ...]:
        return self._watchlists


def make_watchlists() -> StubWatchlistService:
    return StubWatchlistService(
        Watchlist(
            watchlist_id="1",
            name="My Watchlist",
            watchlist_type="custom",
            is_default=True,
            rank=1,
            items=(
                make_item(1, "MSFT", "Microsoft"),
                make_item(2, "NVDA", "NVIDIA"),
            ),
        ),
        Watchlist(
            watchlist_id="2",
            name="Recently Invested",
            watchlist_type="system",
            is_default=False,
            rank=2,
            items=(
                make_item(2, "NVDA", "NVIDIA"),
                make_item(3, "ASML", "ASML Holding"),
            ),
        ),
    )


def make_perception() -> OpportunityPerception:
    return OpportunityPerception(
        watchlist_service=make_watchlists(),  # type: ignore[arg-type]
    )


def test_candidates_are_the_watched_securities() -> None:
    candidates = asyncio.run(make_perception().execute(make_portfolio()))

    assert [candidate.symbol for candidate in candidates] == [
        "MSFT",
        "NVDA",
        "ASML",
    ]
    assert candidates[0].name == "Microsoft"
    assert candidates[0].source == "My Watchlist"
    assert candidates[2].source == "Recently Invested"


def test_a_held_security_is_not_a_candidate() -> None:
    portfolio = replace(
        make_portfolio(),
        holdings=(
            PortfolioPosition(
                symbol="MSFT",
                quantity=3.0,
                invested_usd=900.0,
                market_value_usd=1_000.0,
                unrealized_pnl_usd=100.0,
                instrument_id=1,
            ),
        ),
    )

    candidates = asyncio.run(make_perception().execute(portfolio))

    assert [candidate.symbol for candidate in candidates] == ["NVDA", "ASML"]


def make_brain(evidenced: tuple[str, ...]) -> Brain:
    candidates = (
        ResearchCandidate(
            symbol="MSFT",
            name="Microsoft",
            source="My Watchlist",
            instrument_id=1,
        ),
        ResearchCandidate(
            symbol="NVDA",
            name="NVIDIA",
            source="My Watchlist",
            instrument_id=2,
        ),
    )

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        candidates=candidates,
        evidence={symbol: (make_company(symbol),) for symbol in evidenced},
    ).build()


def test_only_evidenced_candidates_are_judged() -> None:
    research = CandidateResearchService().build(
        make_brain(evidenced=("MSFT",)),
        reviewed=2,
    )

    assert [workspace.symbol for workspace in research.workspaces] == ["MSFT"]
    assert research.funnel.candidates == 2
    assert research.funnel.reviewed == 2
    assert research.funnel.evidenced == 1
    assert research.funnel.unevidenced == 1
    assert research.funnel.judged == 1


def test_the_funnel_reports_what_it_could_not_look_at() -> None:
    research = CandidateResearchService().build(
        make_brain(evidenced=("MSFT",)),
        reviewed=1,
    )

    assert research.funnel.not_reviewed == 1
    assert research.funnel.unevidenced == 0


def test_a_candidate_carries_the_scores_it_was_judged_on() -> None:
    research = CandidateResearchService().build(
        make_brain(evidenced=("MSFT", "NVDA")),
        reviewed=2,
    )

    workspace = research.workspaces[0]

    assert workspace.evidence is not None
    assert workspace.decision is not None
    assert workspace.evidence.symbol == workspace.symbol
    assert 0 <= workspace.evidence.quality_score <= 100
    assert 0 <= workspace.evidence.valuation_score <= 100


def test_candidates_are_ranked_by_conviction() -> None:
    research = CandidateResearchService().build(
        make_brain(evidenced=("MSFT", "NVDA")),
        reviewed=2,
    )

    convictions = [
        workspace.decision.conviction
        for workspace in research.workspaces
        if workspace.decision is not None
    ]

    assert convictions == sorted(convictions, reverse=True)


def test_the_candidate_behind_each_evaluation_is_reported() -> None:
    research = CandidateResearchService().build(
        make_brain(evidenced=("MSFT",)),
        reviewed=1,
    )

    assert research.candidates["MSFT"].name == "Microsoft"
    assert research.candidates["MSFT"].source == "My Watchlist"


def test_nothing_watched_reports_an_empty_pipeline() -> None:
    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    research = CandidateResearchService().build(brain)

    assert research.workspaces == ()
    assert research.funnel.candidates == 0
    assert research.funnel.judged == 0
