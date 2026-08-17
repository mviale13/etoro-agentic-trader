"""What admits an asset to research belongs to the system that judges it.

DV5. DV4 made a digital asset's *judgment* canonical everywhere. Its
*admission to research* was still decided by the company evidence
pipeline: `CandidateResearchService.evidenced` asked whether a provider
row existed, for every asset alike.

Measured on the live corpus: **1INCH, ARB and ADA each hold recorded
committee judgments and a canonical INVESTIGATE, and all three were
withheld from research** — not because anything about them was unknown,
but because a *fundamentals request budget* of forty had not reached
them. Reading what their committees already recorded costs nothing.

Pinned here, in both directions:

1. **A recorded judgment admits, with or without a provider row.**
2. **A provider row admits nothing on its own.** A market price is not a
   judgment, and a token no committee has looked at stays out — named,
   never silently dropped.
3. **An informed MONITOR is not an absence.** TAO's committees both ran
   and recorded that they cannot establish whether their questions
   apply. That is a conclusion, and it is admitted.
4. **Equities, funds and commodities are untouched.**
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.application.workspace.candidate_research_service import (
    CandidateResearchService,
)
from app.brain import Brain, BrainBuilder
from app.cio.decision_state import DecisionState
from app.cio.digital_asset_decision import DigitalAssetDecision
from app.domain.research_candidate import ResearchCandidate
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)
from tests.test_brain_context import make_market, make_policy, make_portfolio
from tests.test_security_evidence import make_company


class StubDigitalAssets(DigitalAssetDecisionService):
    """A crypto judgment path with a declared answer per symbol.

    The suite runs against an empty evidence root, so the live store
    records nothing for any asset. These specimens carry the live shapes
    instead — BTC's answered committee, TAO's informed MONITOR, and a
    token nobody has judged — so the admission rule is pinned whatever
    the store holds.
    """

    def __init__(self, judged: dict[str, DecisionState | None]) -> None:
        super().__init__()
        self._judged = judged

    def decide(self, symbol: str) -> DigitalAssetDecision:
        state = self._judged.get(symbol.upper().strip())

        return DigitalAssetDecision(
            symbol=symbol.upper().strip(),
            state=state or DecisionState.MONITOR,
            rationale="declared by the specimen",
            judged=state is not None,
        )


def candidate(symbol: str, asset_class: str) -> ResearchCandidate:
    return ResearchCandidate(
        symbol=symbol,
        name=symbol,
        source="My Watchlist",
        instrument_id=abs(hash(symbol)) % 10_000,
        asset_class=asset_class,
    )


def make_brain(
    candidates: tuple[ResearchCandidate, ...],
    evidenced: tuple[str, ...] = (),
    attempted: tuple[str, ...] = (),
) -> Brain:
    return BrainBuilder(
        portfolio=replace(make_portfolio(), holdings=()),
        market=make_market(),
        investment_policy=make_policy(),
        candidates=candidates,
        evidence={symbol: (make_company(symbol),) for symbol in evidenced},
        attempted_candidates=attempted,
    ).build()


def research(
    brain: Brain,
    judged: dict[str, DecisionState | None] | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """The three outcomes, as sets of symbols."""

    result = CandidateResearchService(
        digital_assets=StubDigitalAssets(judged or {}),
    ).build(brain)

    return (
        {workspace.symbol for workspace in result.workspaces},
        {item.symbol for item in result.unevidenced},
        {item.symbol for item in result.not_reviewed},
    )


# ── 1. a recorded judgment admits ───────────────────────────────────


def test_a_judged_token_is_researched_without_a_provider_row() -> None:
    """The measured defect: ADA, ARB and 1INCH's shape.

    No provider row, and outside the fundamentals budget entirely — yet
    a committee has concluded something, and reading that costs nothing.
    """

    brain = make_brain((candidate("ARB", "crypto"),))

    judged, unevidenced, not_reviewed = research(
        brain, {"ARB": DecisionState.INVESTIGATE}
    )

    assert judged == {"ARB"}
    assert unevidenced == set()
    assert not_reviewed == set()


def test_an_informed_monitor_is_a_conclusion_and_is_admitted() -> None:
    """TAO's control: applicability unresolved is something we know.

    Collapsing it into *unevidenced* would report a state the platform
    reached by running both committees as a state it never looked at.
    """

    brain = make_brain((candidate("TAO", "crypto"),))

    judged, unevidenced, _ = research(brain, {"TAO": DecisionState.MONITOR})

    assert judged == {"TAO"}
    assert unevidenced == set()


@pytest.mark.parametrize(
    "state",
    [DecisionState.INVESTIGATE, DecisionState.MONITOR],
)
def test_admission_does_not_depend_on_which_posture_was_reached(
    state: DecisionState,
) -> None:
    """MONITOR and INVESTIGATE are both answers; neither is an absence."""

    brain = make_brain((candidate("BTC", "crypto"),))

    judged, _, _ = research(brain, {"BTC": state})

    assert judged == {"BTC"}


# ── 2. a provider row admits nothing ────────────────────────────────


def test_a_provider_row_alone_does_not_admit_a_token() -> None:
    """The inverse control, and the half a naive fix would have missed.

    Market statistics are not a judgment. A token nobody has judged is
    withheld even where the provider answered — and it is *named* as
    unevidenced rather than vanishing, because a security silently
    absent reads as one that was considered and dismissed.
    """

    brain = make_brain(
        (candidate("NEWTOKEN", "crypto"),),
        evidenced=("NEWTOKEN",),
        attempted=("NEWTOKEN",),
    )

    judged, unevidenced, not_reviewed = research(brain, {})

    assert judged == set()
    assert unevidenced == {"NEWTOKEN"}
    assert not_reviewed == set()


def test_an_unjudged_token_outside_the_budget_is_named_as_unreviewed() -> None:
    """Never looked at by either system, and said as that."""

    brain = make_brain((candidate("NEWTOKEN", "crypto"),))

    judged, unevidenced, not_reviewed = research(brain, {})

    assert judged == set()
    assert unevidenced == set()
    assert not_reviewed == {"NEWTOKEN"}


# ── 3. the company path is untouched ────────────────────────────────


@pytest.mark.parametrize("asset_class", ["stock", "etf", "commodity"])
def test_every_other_asset_class_still_admits_on_provider_evidence(
    asset_class: str,
) -> None:
    """Funds and commodities have no company either, and are not tokens.

    `AssetClass.has_no_company` holds for CRYPTO, COMMODITY and ETF, so
    dispatching on it would have sent a fund's admission to the crypto
    judgment path — where it would never be judged at all.
    """

    admitted = make_brain(
        (candidate("AAA", asset_class),),
        evidenced=("AAA",),
        attempted=("AAA",),
    )

    judged, unevidenced, _ = research(admitted, {})

    assert judged == {"AAA"}
    assert unevidenced == set()

    withheld = make_brain(
        (candidate("AAA", asset_class),),
        attempted=("AAA",),
    )

    judged, unevidenced, _ = research(withheld, {})

    assert judged == set()
    assert unevidenced == {"AAA"}


def test_a_crypto_judgment_never_admits_a_company() -> None:
    """The stub answers for every symbol; only a token may ask it."""

    brain = make_brain(
        (candidate("MSFT", "stock"), candidate("BTC", "crypto")),
        attempted=("MSFT", "BTC"),
    )

    judged, unevidenced, _ = research(
        brain,
        {"MSFT": DecisionState.INVESTIGATE, "BTC": DecisionState.INVESTIGATE},
    )

    # MSFT has no provider row, and a crypto judgment cannot stand in.
    assert judged == {"BTC"}
    assert unevidenced == {"MSFT"}


# ── 4. the funnel counts what it names ──────────────────────────────


def test_the_counts_and_the_names_cannot_disagree() -> None:
    """Both derive from one set, which is what makes them consistent.

    Admitting a candidate the request budget never reached made
    `evidenced` exceed `reviewed`, so the funnel reported a count that
    contradicted the list printed beside it.
    """

    brain = make_brain(
        (
            candidate("ARB", "crypto"),  # judged, never requested
            candidate("NEWTOKEN", "crypto"),  # requested, never judged
            candidate("MSFT", "stock"),  # requested and evidenced
            candidate("PG", "stock"),  # neither
        ),
        evidenced=("MSFT",),
        attempted=("NEWTOKEN", "MSFT"),
    )

    result = CandidateResearchService(
        digital_assets=StubDigitalAssets({"ARB": DecisionState.INVESTIGATE}),
    ).build(brain)

    funnel = result.funnel

    assert funnel.candidates == 4
    assert funnel.evidenced == 2  # ARB and MSFT
    assert funnel.reviewed == 3  # those two, plus the requested NEWTOKEN
    assert funnel.unevidenced == 1
    assert funnel.not_reviewed == 1

    assert len(result.unevidenced) == funnel.unevidenced
    assert len(result.not_reviewed) == funnel.not_reviewed
    assert funnel.judged == len(result.workspaces)

    # And every candidate is accounted for exactly once.
    named = (
        {workspace.symbol for workspace in result.workspaces}
        | {item.symbol for item in result.unevidenced}
        | {item.symbol for item in result.not_reviewed}
    )

    assert named == {"ARB", "NEWTOKEN", "MSFT", "PG"}


# ── 5. DV4's laws still hold on the admitted token ──────────────────


def test_an_admitted_token_keeps_the_canonical_judgment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admission changed; judgment did not.

    The route builds a row from the workspace, and DV4 removed the
    `evidence` requirement that would have dropped it. Both halves are
    exercised here: the token is admitted on its judgment, and it
    survives all the way to the wire carrying no conviction, no rank and
    no provider reasoning.
    """

    from fastapi.testclient import TestClient

    from app.api.dependencies import get_brain_builder_service
    from app.api.main import app
    from tests.test_api_routes import StubBrainBuilder

    def declared(
        self: DigitalAssetDecisionService, symbol: str
    ) -> DigitalAssetDecision:
        return DigitalAssetDecision(
            symbol=symbol.upper().strip(),
            state=DecisionState.INVESTIGATE,
            rationale="a committee concluded something",
            judged=True,
        )

    monkeypatch.setattr(DigitalAssetDecisionService, "decide", declared)

    brain = make_brain((candidate("ARB", "crypto"),))

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        brain
    )

    try:
        body = TestClient(app).get("/research/candidates").json()
    finally:
        app.dependency_overrides.pop(get_brain_builder_service, None)

    rows = {row["symbol"]: row for row in body["candidates"]}

    assert "ARB" in rows

    row = rows["ARB"]

    assert row["recommendation"] == "INVESTIGATE"
    assert row["why_not_yet"] == "a committee concluded something"

    # DV2, DV3 and DV4's laws, unchanged by admission.
    assert row["conviction"] is None
    assert row["conviction_label"] is None
    assert row["rank"] is None
    assert row["evidence_score"] is None
    assert row["quality_score"] is None
    assert row["valuation_score"] is None
    assert row["safety_score"] is None
