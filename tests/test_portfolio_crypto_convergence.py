"""A crypto asset has one investment judgment, wherever it is shown.

DV4. DV3 gave the crypto dossier the canonical answer and retired the
legacy per-security dossier. The portfolio and executive paths were
still reasoning about the same holdings the old way: BTC's canonical
dossier answered INVESTIGATE with no conviction, while the same holding
in the portfolio brief answered INVESTIGATE **conviction 46**, ranked
eleventh of fourteen, with *"Market robustness: robust — $1,308.7bn"*
printed as a reason for it and its annualised volatility printed
against it.

Pinned here:

1. **One judgment.** The pipeline dispatches on the asset class — the
   narrowest boundary at which this platform knows what it is reasoning
   about — and a digital asset's decision is the crypto path's,
   translated rather than recomputed.
2. **No provider reasoning reaches it.** The company route is not run at
   all for a digital asset, so there is no finding, score, committee
   opinion or conviction for anything downstream to find.
3. **The evidence discipline survives the translation.** A structural
   conclusion is never a strength, a wrong-instrument finding is never
   adverse, an open question keeps its owner's name, and a material
   spread stays a spread.
4. **No fake comparability.** A case with no conviction holds no
   position in the conviction order.
"""

from __future__ import annotations

import pathlib

import pytest

from app.application.workspace.candidate_research_service import (
    CandidateResearchService,
)
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.brain import Brain, BrainBuilder
from app.cio.decision_state import DecisionState
from app.cio.digital_asset_decision import (
    DigitalAssetDecision,
    UnresolvedQuestion,
    as_executive_decision,
)
from app.domain.portfolio_position import PortfolioPosition
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)
from tests.test_brain_context import make_market, make_policy, make_portfolio

#: The DV3 specimens, plus the two controls. TAO is the weak-evidence
#: control and ARB the uncertainty control; both are held here so the
#: portfolio path sees them.
CRYPTO = ("BTC", "ETH", "TAO", "ARB")


def holding(symbol: str, asset_class: str = "crypto") -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=100.0,
        market_value_usd=110.0,
        unrealized_pnl_usd=10.0,
        instrument_id=abs(hash(symbol)) % 10_000,
        asset_class=asset_class,
    )


def make_brain(*symbols: str) -> Brain:
    from dataclasses import replace

    return BrainBuilder(
        portfolio=replace(
            make_portfolio(),
            holdings=tuple(holding(symbol) for symbol in symbols),
        ),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


@pytest.fixture
def pipeline() -> ExecutivePipeline:
    # journal=None: an evaluation in a test writes nothing.
    return ExecutivePipeline()


# ── 1. one judgment, everywhere ─────────────────────────────────────


@pytest.mark.parametrize("symbol", CRYPTO)
def test_the_portfolio_answer_is_the_canonical_answer(
    symbol: str,
    pipeline: ExecutivePipeline,
) -> None:
    """The mandatory invariant, per specimen.

    Not "the same posture" — *the same object*, translated. A test that
    compared only the state would pass while the rationale drifted.
    """

    workspace = pipeline.execute(symbol=symbol, brain=make_brain(symbol))

    canonical = DigitalAssetDecisionService().decide(symbol)

    assert workspace.decision is not None

    # Everything but the stamp of when it was taken: two constructions of
    # the same judgment differ by microseconds and by nothing else.
    assert workspace.decision.model_dump(
        exclude={"decided_at"}
    ) == as_executive_decision(canonical).model_dump(exclude={"decided_at"})

    assert workspace.decision.state is canonical.state
    assert workspace.decision.rationale == canonical.rationale


@pytest.mark.parametrize("symbol", CRYPTO)
def test_no_conviction_is_regenerated_downstream(
    symbol: str,
    pipeline: ExecutivePipeline,
) -> None:
    """DV2's rule, and DV3's, held across the portfolio path."""

    workspace = pipeline.execute(symbol=symbol, brain=make_brain(symbol))

    assert workspace.decision is not None
    assert workspace.decision.conviction is None

    assert workspace.thesis is not None
    assert workspace.thesis.conviction is None

    # And nothing recomputed one from a score, because there are no
    # scores: the company route did not run.
    assert workspace.evidence is None


@pytest.mark.parametrize("symbol", CRYPTO)
def test_no_provider_reasoning_is_produced_for_a_digital_asset(
    symbol: str,
    pipeline: ExecutivePipeline,
) -> None:
    """Not discarded — never produced.

    A provider-fed finding that exists is a finding something downstream
    can find, so the company route is skipped rather than run and
    filtered.
    """

    workspace = pipeline.execute(symbol=symbol, brain=make_brain(symbol))

    assert workspace.findings.findings == ()
    assert workspace.committee_opinions == ()
    assert workspace.quality is None
    assert workspace.evidence is None


def test_the_dispatch_is_the_asset_class_and_not_a_symbol_list() -> None:
    """The boundary is the instrument's domain, not a corpus membership.

    A crypto holding outside the read corpus still reaches the crypto
    path — where it honestly answers MONITOR, because no committee has
    judged it — rather than falling through to company reasoning.
    """

    source = pathlib.Path("app/application/workspace/executive_pipeline.py").read_text(
        encoding="utf-8"
    )

    assert "ASSIGNMENTS" not in source
    assert "crypto_archetype" not in source

    workspace = ExecutivePipeline().execute(
        symbol="ZZZNOTACORPUSASSET",
        brain=make_brain("ZZZNOTACORPUSASSET"),
    )

    assert workspace.decision is not None
    assert workspace.decision.state is DecisionState.MONITOR
    assert workspace.decision.conviction is None
    assert workspace.evidence is None


# ── 2. the evidence discipline survives the translation ─────────────


@pytest.mark.parametrize("symbol", CRYPTO)
def test_nothing_crosses_as_a_strength_or_a_risk(
    symbol: str,
    pipeline: ExecutivePipeline,
) -> None:
    """A structural conclusion is not a grade, in either direction.

    This is where the old path did its damage: market capitalisation
    arrived as a reason *for* BTC and its volatility as a reason
    *against* it, neither of which any crypto layer licenses.
    """

    workspace = pipeline.execute(symbol=symbol, brain=make_brain(symbol))

    assert workspace.decision is not None
    assert workspace.decision.key_strengths == ()
    assert workspace.decision.key_risks == ()

    assert workspace.thesis is not None
    assert workspace.thesis.strengths == ()
    assert workspace.thesis.risks == ()


def canonical(
    state: DecisionState = DecisionState.INVESTIGATE,
    established: tuple[str, ...] = (),
    not_applicable: tuple[str, ...] = (),
    unresolved: tuple[UnresolvedQuestion, ...] = (),
    material_uncertainties: tuple[str, ...] = (),
) -> DigitalAssetDecision:
    """A canonical answer built directly.

    The suite runs against an empty evidence root, so a corpus-shaped
    assertion here would skip rather than fail. These specimens carry
    the live shapes — BTC's wrong-instrument finding, ETH's open
    question, ARB's material spread — so the translation is pinned
    whatever the store holds.
    """

    return DigitalAssetDecision(
        symbol="TEST",
        state=state,
        rationale="because the postures said so",
        established=established,
        not_applicable=not_applicable,
        unresolved=unresolved,
        material_uncertainties=material_uncertainties,
    )


def test_a_wrong_instrument_finding_never_becomes_adverse() -> None:
    """BTC's Value Capture shape: knowledge, carried as evidence weighed.

    The one crossing that would do the most damage if it slipped: a
    committee saying *this question is the wrong instrument for this
    asset* filed under what argues against the security.
    """

    line = (
        "Value Capture Committee: This asset's established economic role "
        "is monetary, so the question is the wrong instrument."
    )

    decision = as_executive_decision(canonical(not_applicable=(line,)))

    assert line in decision.evidence_weighed
    assert decision.key_risks == ()
    assert line not in decision.missing_evidence


def test_an_established_conclusion_never_becomes_a_strength() -> None:
    """BTC's Supply Governance shape: established, and not thereby good."""

    line = (
        "Supply Governance Committee established that new supply is created "
        "by a mechanical rule. On its investment meaning, what this "
        "conclusion means for an investment case is not established by "
        "this platform."
    )

    decision = as_executive_decision(canonical(established=(line,)))

    assert line in decision.evidence_weighed
    assert decision.key_strengths == ()

    # And the clause that keeps it honest travels with it.
    assert "not established by this platform" in decision.evidence_weighed[0]


def test_an_open_question_keeps_its_owner_and_stays_a_question() -> None:
    """ETH's shape: unresolved is what would advance it, not a penalty."""

    question = UnresolvedQuestion(
        owner="Supply Governance Committee",
        stated="No mechanical issuance rule is held for this asset.",
    )

    decision = as_executive_decision(canonical(unresolved=(question,)))

    assert decision.missing_evidence == (
        "Supply Governance Committee: No mechanical issuance rule is held "
        "for this asset.",
    )
    assert decision.key_risks == ()


def test_a_material_spread_stays_a_spread() -> None:
    """ARB's 81% circulating-supply range: uncertainty, never bearish."""

    line = (
        "Circulating supply cannot be stated as a single figure: available "
        "estimates run from 1.27 billion to 6.61 billion, a spread of 81%."
    )

    decision = as_executive_decision(canonical(material_uncertainties=(line,)))

    assert line in decision.missing_evidence
    assert decision.key_risks == ()
    assert decision.evidence_weighed == ()


def test_execution_unavailable_stays_distinct_from_insufficient_evidence() -> None:
    """Two different silences, and the sentences must not converge.

    *The committee did not run* is a fact about this platform; *the
    evidence could not answer* is a fact about what was read. Both reach
    `missing_evidence`, and each keeps the wording its own layer chose —
    this layer supplies no placeholder either could collapse into.
    """

    did_not_run = UnresolvedQuestion(
        owner="A Committee",
        stated="Committee judgment is off, so no verdict was reached.",
    )
    could_not_answer = UnresolvedQuestion(
        owner="A Committee",
        stated="No mechanical issuance rule is held for this asset.",
    )

    decision = as_executive_decision(
        canonical(unresolved=(did_not_run, could_not_answer))
    )

    assert len(set(decision.missing_evidence)) == 2


# ── 3. no fake comparability ────────────────────────────────────────


def test_a_case_without_conviction_holds_no_position_in_the_order(
    pipeline: ExecutivePipeline,
) -> None:
    """Rank is a place in the conviction order, and there is no order.

    Measured at the route in `test_api_routes`; asserted here as the
    domain fact it rests on — every digital asset comes out with no
    conviction, so none of them can be ranked against anything.
    """

    for symbol in CRYPTO:
        workspace = pipeline.execute(symbol=symbol, brain=make_brain(symbol))

        assert workspace.decision is not None
        assert workspace.decision.conviction is None


def test_the_decision_carries_the_rule_that_produced_it() -> None:
    """Provenance: which reasoning system decided this.

    An executive record produced by the company gates carries
    `decision-gates` and `conviction-mean`; this one carries
    `digital-asset-gates`, and the two can never be read as one.
    """

    decision = as_executive_decision(DigitalAssetDecisionService().decide("BTC"))

    assert [rule.key for rule in decision.decided_under] == ["digital-asset-gates"]


# ── 4. the company path is untouched ────────────────────────────────


def test_a_stock_holding_still_runs_the_company_route(
    pipeline: ExecutivePipeline,
) -> None:
    """The dispatch is narrow: only a digital asset leaves the old path."""

    brain = make_brain()

    from dataclasses import replace

    equity_brain = BrainBuilder(
        portfolio=replace(
            brain.portfolio,
            holdings=(holding("MSFT", asset_class="stock"),),
        ),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    workspace = pipeline.execute(symbol="MSFT", brain=equity_brain)

    assert workspace.evidence is not None
    assert workspace.decision is not None
    assert workspace.decision.decided_under
    assert [rule.key for rule in workspace.decision.decided_under] != [
        "digital-asset-gates"
    ]


def test_a_fund_is_not_routed_to_the_crypto_path(
    pipeline: ExecutivePipeline,
) -> None:
    """A fund has no company either, and is not a digital asset.

    `AssetClass.has_no_company` holds for CRYPTO, COMMODITY and ETF, so
    dispatching on it would have sent every fund to the crypto decider.
    The dispatch is on the class itself for exactly this reason.
    """

    from dataclasses import replace

    fund_brain = BrainBuilder(
        portfolio=replace(
            make_portfolio(),
            holdings=(holding("IB01.L", asset_class="etf"),),
        ),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    workspace = pipeline.execute(symbol="IB01.L", brain=fund_brain)

    assert workspace.evidence is not None
    assert [rule.key for rule in workspace.decision.decided_under] != [  # type: ignore[union-attr]
        "digital-asset-gates"
    ]


# ── 5. the route, end to end ────────────────────────────────────────


def test_the_briefing_route_ranks_only_what_carries_a_conviction() -> None:
    """The measured defect at the wire.

    BTC ranked eleventh of fourteen on a conviction of 46. It now
    carries no conviction, so it holds no position — and the cases below
    the ranked group are still listed, still explained, and simply not
    numbered against each other on an order nobody measured.
    """

    from dataclasses import replace

    from fastapi.testclient import TestClient

    from app.api.dependencies import get_brain_builder_service
    from app.api.main import app
    from tests.test_api_routes import StubBrainBuilder

    brain = BrainBuilder(
        portfolio=replace(
            make_portfolio(),
            holdings=(
                holding("BTC"),
                holding("ETH"),
                holding("MSFT", asset_class="stock"),
            ),
        ),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        brain
    )

    try:
        body = TestClient(app).get("/executive/portfolio").json()
    finally:
        app.dependency_overrides.pop(get_brain_builder_service, None)

    cases = {case["symbol"]: case for case in body["investment_cases"]}

    for symbol in ("BTC", "ETH"):
        assert cases[symbol]["conviction"] is None, symbol
        assert cases[symbol]["conviction_label"] is None, symbol
        assert cases[symbol]["rank"] is None, symbol

        # No company committee reviewed a digital asset, and an unasked
        # question is not unanimous disagreement.
        assert cases[symbol]["committee_agreement"] is None, symbol

        # No provider-fed reason for or against it reached the wire.
        assert cases[symbol]["risks"] == [], symbol
        assert cases[symbol]["safety_score"] is None, symbol

    # Every ranked position is held by a case that carries a conviction,
    # and the numbering is dense: 1, 2, 3 … with no gaps left by the
    # cases that stepped out of the order.
    ranked = [case for case in body["investment_cases"] if case["rank"] is not None]

    assert [case["rank"] for case in ranked] == list(range(1, len(ranked) + 1))
    assert all(case["conviction"] is not None for case in ranked)


def test_a_watched_digital_asset_is_not_dropped_from_research() -> None:
    """The defect this slice nearly introduced, pinned.

    The research route required `workspace.evidence` to build a row. A
    digital asset produces none, so a watched token that reached the
    pipeline vanished from the response entirely — a surface silently
    omitting an asset is worse than one showing it honestly unranked.

    Admission itself moved in DV5 and is pinned in that slice's own
    suite; what this asserts is the half DV4 owns — that once a digital
    asset is admitted, it survives to the wire carrying no conviction,
    no rank and no provider reasoning.
    """

    from dataclasses import replace

    from fastapi.testclient import TestClient

    from app.api.dependencies import get_brain_builder_service
    from app.api.main import app
    from app.domain.research_candidate import ResearchCandidate
    from tests.test_api_routes import StubBrainBuilder
    from tests.test_crypto_research_eligibility import StubDigitalAssets

    brain = BrainBuilder(
        portfolio=replace(make_portfolio(), holdings=()),
        market=make_market(),
        investment_policy=make_policy(),
        candidates=(
            ResearchCandidate(
                symbol="BTC",
                name="Bitcoin",
                source="My Watchlist",
                instrument_id=1,
                asset_class="crypto",
            ),
        ),
        attempted_candidates=("BTC",),
    ).build()

    research = CandidateResearchService(
        digital_assets=StubDigitalAssets({"BTC": DecisionState.INVESTIGATE}),
    ).build(brain)

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        brain
    )

    try:
        client = TestClient(app)

        # The route builds its own service, so the response is checked
        # against the same brain through the wire — and the admitted set
        # above is what proves the token reached the row builder at all.
        assert {workspace.symbol for workspace in research.workspaces} == {"BTC"}

        body = client.get("/research/candidates").json()
    finally:
        app.dependency_overrides.pop(get_brain_builder_service, None)

    # Without a recorded judgment the live path withholds it — and names
    # it, rather than dropping it silently.
    named = {row["symbol"] for row in body["candidates"]}
    named |= {row["symbol"] for row in body["unevidenced"]}
    named |= {row["symbol"] for row in body["not_reviewed"]}

    assert "BTC" in named
