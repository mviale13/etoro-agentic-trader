"""The company vote's direct decision gates, removed.

The owner's ruling of 2026-08-24, stated exactly:

    The company vote's SELL and BUY directions no longer directly
    reject or authorize a case. Its confidence remains decision-bearing
    through `evidence_score`; that residual changes one live blocker,
    can reach a state threshold, and is **not** accepted as the final
    contract.

**This is not "the vote is now descriptive".** Its *direction* is; its
*magnitude* is not, and the difference is the whole residual. What the
ruling removed is the two direct mappings — a SELL that rejected and a
BUY that authorized.

What this replaces, measured on the live book:

- **`analyst_veto`** was `company.recommendation == "SELL"`, and it was
  the *first live branch* of the cascade — ahead of every score. AMD
  reached it on a −4.28% session while its own analysts read growth,
  profitability, balance sheet and cash flow as strong or better, and
  the blocker called that "a specialist analyst's veto" when no analyst
  had spoken. The veto was decided by the day's price band alone.
- **`actionable_now`** was `company.recommendation == "BUY"`, the final
  gate before RECOMMEND. Measured over the live book, that flag was
  decided by the day's price band for four securities.

Both are gone, and **nothing replaces the execution trigger** — this
slice introduces no technical-analysis trigger. A case that satisfies
quality, evidence, valuation, risk and portfolio fit is recommended on
those alone.

**Path C survives and is not accepted as final.** `evidence_score`
still averages the vote's confidence, which is magnitude-derived — so
a larger one-session move still raises it. The residual is measured
and pinned at the end of this file rather than described away.

This is the volatility ruling of 2026-08-21 applied one layer up:
market behaviour may inform risk, timing and eventual sizing without
becoming a judgment about business quality — a boundary this slice
moves toward and does not yet reach.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import textwrap

import pytest
from pydantic import ValidationError

from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.decision_blocker import BlockerKind
from app.domain.decision_rules import DECISION_GATES, DECISION_RULES
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.provider_identity import (
    CrossProviderIdentity,
    IdentityStanding,
    ProviderIdentityClaim,
)
from app.domain.provider_translation import TranslationWarrant
from app.services.company_committee_service import CompanyCommitteeService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService

#: AMD as the funded cycle of 2026-08-24 read it: a forward P/E of 29.3
#: (EXPENSIVE), quality MEDIUM at 2 of 3 factors, and the session that
#: produced the veto.
AMD = dict(
    symbol="AMD",
    name="Advanced Micro Devices Inc",
    instrument_id=1832,
    asset_type=5,
    exchange="4",
    current_price=453.0,
    forward_pe=29.261784,
    eps=3.93,
    dividend_yield=0.0,
    revenue_growth=0.501,
    earnings_growth=1.595,
    gross_margin=0.55724,
    operating_margin=0.1725,
    net_margin=0.15577,
    debt_to_equity=0.06361,
    current_ratio=2.609,
    operating_cash_flow=10_080_000_000.0,
    free_cash_flow=8_841_499_648.0,
    roe=0.10196,
    market_cap=739_751_297_024.0,
    realized_volatility=0.7186,
    max_drawdown=0.2776,
    sector="Technology",
    industry="Semiconductors",
    currency="USD",
)


def _identifiers(source: str) -> set[str]:
    """Every name and attribute a body actually references."""

    tree = ast.parse(textwrap.dedent(source))

    return {
        node.id if isinstance(node, ast.Name) else node.attr
        for node in ast.walk(tree)
        if isinstance(node, (ast.Name, ast.Attribute))
    }


def _string_literals(source: str) -> list[str]:
    return [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def facts(change_pct: float, **overrides) -> CompanyFacts:
    values = dict(AMD, daily_change_pct=change_pct)
    # The size factor reads the magnitude, never the bare figure: a
    # number whose denomination is unestablished may not be placed
    # against an absolute threshold (#142).
    values["market_cap_magnitude"] = MarketCapMagnitude(
        amount=AMD["market_cap"],
        warrant=TranslationWarrant.VALIDATED,
        currency="USD",
        currency_is_assumed=False,
        # The size factor is a conjunction over four crossings, and
        # identity is one of them: a perfectly denominated figure about
        # an unsettled subject is still not comparable (#134). This is
        # the live join for AMD, standing and all.
        identity=CrossProviderIdentity(
            symbol="AMD",
            claims=(
                ProviderIdentityClaim(provider="eToro", symbol="AMD"),
                ProviderIdentityClaim(provider="Yahoo Finance", symbol="AMD"),
            ),
            standing=IdentityStanding.ASSUMED,
            because="the join rests on symbol equality alone",
        ),
    )
    values.update(overrides)

    return CompanyFacts(**values)  # type: ignore[arg-type]


def signals(change_pct: float, **overrides) -> CompanySignals:
    company = facts(change_pct, **overrides)

    return CompanySignals(
        value=ValueSignalService().build(company, AssetClass.STOCK),
        momentum=MomentumSignalService().build(company),
        quality=QualitySignalService().build(company, AssetClass.STOCK),
        risk=RiskSignalService().build(company),
        research=None,
        earnings=None,
        reading=None,
    )


def evidence(**overrides) -> DecisionEvidence:
    """A fully measured case that clears every remaining gate."""

    values: dict[str, object] = {
        "symbol": "TEST",
        "quality_score": 85,
        "evidence_score": 85,
        "valuation_score": 80,
        "risk_score": 25,
        "portfolio_fit_score": 80,
        "security_evidenced": True,
    }
    values.update(overrides)

    return DecisionEvidence(**values)  # type: ignore[arg-type]


# ── acceptance 1: the −0.50% cliff no longer moves AMD ──────────────


@pytest.mark.parametrize("change", [-0.49, -0.50, -0.51, -2.0, -4.28, 0.0, +0.49, +2.5])
def test_amd_does_not_move_on_the_daily_change(change: float) -> None:
    """Acceptance 1, swept across the boundary that used to decide it.

    Value EXPENSIVE and quality MEDIUM are AMD's own, unchanged. Only
    the session moves. Before this ruling −0.49% left AMD at PREPARE
    and −0.50% rejected it; the whole decision turned on one hundredth
    of a percentage point of provider-reported price.

    AMD's *state* is now stable across the sweep. That is a fact about
    AMD, whose quality band holds it at PREPARE either way — not a
    general claim that momentum can no longer move a state. Path C can
    still reach an evidence threshold; see the residual test below.
    """

    reading = signals(change)
    vote = CompanyCommitteeService().evaluate("AMD", reading)

    # The vote still swings across the boundary — it is still measured,
    # still banded, and still says what it says. Its *direction* now
    # reaches no gate; its magnitude still reaches `evidence_score`.
    assert reading.value.valuation == "EXPENSIVE"
    assert reading.quality.quality == "MEDIUM"

    decision = ArtificialCIO().decide(
        evidence(
            symbol="AMD",
            quality_score=62,
            evidence_score=83,
            valuation_score=25,
            risk_score=85,
            portfolio_fit_score=69,
        )
    )

    # ...and no direction of it reaches this decision. AMD is held by
    # its quality band at both ends of the boundary that used to
    # decide between PREPARE and REJECT.
    assert decision.state is DecisionState.PREPARE
    assert decision.blocker is not None
    assert decision.blocker.kind is BlockerKind.QUALITY_GATE

    # The vote's own direction is unconstrained by the decision above.
    assert vote.recommendation in {"BUY", "HOLD", "SELL"}


def test_the_sell_vote_still_happens_and_reaches_no_direct_gate() -> None:
    """The committee still says SELL on the day it said SELL.

    "Reaches no direct gate" rather than "reaches nothing": the vote's
    confidence still reaches `evidence_score`. Only the direction is
    disconnected here.
    """

    vote = CompanyCommitteeService().evaluate("AMD", signals(-4.28))

    assert vote.recommendation == "SELL"
    assert vote.summary == (
        "SELL: value is expensive, quality is medium, and momentum is bearish."
    )

    # And the evidence a decision reads carries no field it could
    # arrive through — the schema refuses one outright.
    with pytest.raises(ValidationError):
        evidence(analyst_veto=True)


# ── acceptance 2: a good day cannot promote a case ──────────────────


def test_a_positive_session_cannot_promote_a_case_to_recommend() -> None:
    """Acceptance 2, at the gate that used to be the last one.

    Two identical cases that satisfy every genuine gate. Before this
    ruling the one whose committee reached BUY was RECOMMENDed and the
    one whose committee reached HOLD was held at PREPARE with
    "Blocked on timing alone" — a difference that a single positive
    session could create.
    """

    decision = ArtificialCIO().decide(evidence())

    assert decision.state is DecisionState.RECOMMEND
    assert decision.blocker is not None
    assert not decision.blocker.blocks

    # There is no input left that could withhold it on timing.
    with pytest.raises(ValidationError):
        evidence(actionable_now=False)


def test_the_execution_trigger_is_not_replaced() -> None:
    """No technical-analysis trigger is introduced by this slice.

    The gate is removed rather than re-sourced: a case that satisfies
    quality, evidence, valuation, risk and portfolio fit is recommended
    on those alone.
    """

    # Identifiers, not prose: the cascade explains the removal in a
    # comment, and a naive substring search would fail on its own
    # explanation. What must be absent is any *reference*.
    read = _identifiers(inspect.getsource(ArtificialCIO._determine_state))

    for banned in (
        "momentum",
        "daily_change",
        "trend",
        "actionable_now",
        "analyst_veto",
    ):
        assert banned not in read, banned

    source = pathlib.Path("app/cio/artificial_cio.py").read_text(encoding="utf-8")

    assert "execution trigger has not occurred" not in source


# ── acceptance 3–4: the observation survives, the claim does not ────


def test_the_momentum_observation_is_still_made_and_sourced() -> None:
    """Acceptance 3: the reading is untouched, including its provenance."""

    reading = MomentumSignalService().build(facts(-4.28))

    assert reading.trend == "BEARISH"
    assert reading.strength == "STRONG"
    assert reading.confidence == 85
    assert reading.rule.key == "momentum-bands"

    statements = [item.statement for item in reading.evidence]

    assert "AMD declined -4.28% in its most recent reading." in statements
    assert "Short-term price momentum is strongly negative." in statements


def test_no_price_move_can_be_worded_as_a_specialist_judgment() -> None:
    """Acceptance 4, at the vocabulary rather than at a sentence.

    The wording is unproducible because the *member* is gone: nothing
    in the blocker vocabulary can name an analyst, and nothing in the
    cascade can reach one.
    """

    assert not hasattr(BlockerKind, "ANALYST_VETO")
    assert not hasattr(BlockerKind, "EXECUTION_TRIGGER")

    blockers = pathlib.Path("app/domain/decision_blocker.py").read_text(
        encoding="utf-8"
    )

    for banned in ("specialist analyst", "analyst's veto", "veto-level risk"):
        assert banned not in blockers, banned

    # And no string literal anywhere in the cascade can say it. The
    # comments explaining the removal are not literals, which is the
    # distinction: a comment cannot reach an investor.
    for literal in _string_literals(
        pathlib.Path("app/cio/artificial_cio.py").read_text(encoding="utf-8")
    ):
        for banned in ("specialist analyst", "veto-level risk", "execution trigger"):
            assert banned not in literal, f"{banned}: {literal[:60]}"


# ── the vocabulary is gone, not merely unread ───────────────────────


def test_no_dead_vocabulary_survives_anywhere() -> None:
    """The four named symbols, and the fields that fed them."""

    assert "actionable-buy" not in DECISION_RULES
    assert "veto-sell" not in DECISION_RULES

    assert "analyst_veto" not in DecisionEvidence.model_fields
    assert "actionable_now" not in DecisionEvidence.model_fields

    for path in (
        "app/cio/artificial_cio.py",
        "app/cio/executive_decision.py",
        "app/cio/evidence_adapter.py",
        "app/domain/decision_blocker.py",
        "app/domain/decision_rules.py",
        "app/application/executive/decision_evidence_builder.py",
    ):
        source = pathlib.Path(path).read_text(encoding="utf-8")

        for banned in (
            "ACTIONABLE_BUY",
            "VETO_SELL",
            "ANALYST_VETO",
            "EXECUTION_TRIGGER",
        ):
            assert banned not in source, f"{path}: {banned}"


def test_the_gate_contract_is_re_versioned() -> None:
    """A cascade may not lose two gates without its rule version moving."""

    assert DECISION_GATES.version == 4
    assert "company-vote gates removed" in DECISION_GATES.because


# ── what must keep working ──────────────────────────────────────────


@pytest.mark.parametrize(
    ("overrides", "state", "kind"),
    [
        ({"hard_reject": True}, DecisionState.REJECT, BlockerKind.POLICY_GATE),
        (
            {"security_evidenced": False},
            DecisionState.INVESTIGATE,
            BlockerKind.MISSING_EVIDENCE,
        ),
        ({"quality_score": 20}, DecisionState.REJECT, BlockerKind.QUALITY_GATE),
        ({"quality_score": 70}, DecisionState.PREPARE, BlockerKind.QUALITY_GATE),
        ({"evidence_score": 70}, DecisionState.PREPARE, BlockerKind.MISSING_EVIDENCE),
        ({"valuation_score": 40}, DecisionState.PREPARE, BlockerKind.VALUATION_GATE),
        ({"risk_score": None}, DecisionState.PREPARE, BlockerKind.RISK_GATE),
        (
            {"portfolio_fit_score": 10},
            DecisionState.PREPARE,
            BlockerKind.PORTFOLIO_FIT_GATE,
        ),
    ],
)
def test_every_genuine_gate_remains_operative(
    overrides: dict[str, object],
    state: DecisionState,
    kind: BlockerKind,
) -> None:
    """Quality, evidence, valuation, risk, portfolio fit and policy."""

    decision = ArtificialCIO().decide(evidence(**overrides))

    assert decision.state is state
    assert decision.blocker is not None
    assert decision.blocker.kind is kind


def test_the_signals_are_all_still_measured_and_banded() -> None:
    """Value, quality, momentum and risk, with their provenance."""

    reading = signals(-4.28)

    assert reading.value.valuation == "EXPENSIVE"
    assert reading.value.rule.key == "pe-bands"
    assert reading.quality.quality == "MEDIUM"
    assert reading.momentum.trend == "BEARISH"
    assert reading.momentum.rule.key == "momentum-bands"
    assert reading.risk is not None and reading.risk.level == "SEVERE"

    vote = CompanyCommitteeService().evaluate("AMD", reading)

    assert vote.direction == "SELL"
    assert vote.authority is not None and vote.authority.may_act
    assert vote.rules


def test_the_digital_asset_contract_is_untouched() -> None:
    """The shared boolean is gone; the separate contract never used it.

    A digital asset is decided by `DigitalAssetDecision` before the
    equity cascade is reached at all, and that path never read either
    flag — so removing them cannot move a token.
    """

    crypto = pathlib.Path("app/cio/digital_asset_decision.py").read_text(
        encoding="utf-8"
    )

    for banned in ("analyst_veto", "actionable_now", 'recommendation == "BUY"'):
        assert banned not in crypto, banned

    assert "digital-asset-gates" in DECISION_RULES


def test_no_order_capable_path_is_introduced() -> None:
    """Nothing here can reach a broker write."""

    for path in (
        "app/cio/artificial_cio.py",
        "app/application/executive/decision_evidence_builder.py",
    ):
        source = pathlib.Path(path).read_text(encoding="utf-8")

        for banned in ("place_trade", "prepare_trade", "requests.post", "httpx"):
            assert banned not in source, f"{path}: {banned}"


# ── the residual, stated rather than implied ────────────────────────


def test_the_vote_confidence_still_reaches_the_evidence_score() -> None:
    """**Not removed.** Recorded here so it cannot be believed removed.

    `evidence_score` is the mean of an account-level cognitive
    confidence and the company vote's own confidence, and that vote's
    confidence rises with the *magnitude* of the vote — so a large
    one-session move still raises the evidence score. AMD's went 71 to
    83 on the day it was vetoed.

    It is left in place deliberately. `cognitive_confidence` is built
    from portfolio, market and risk confidence alone, so dropping the
    company term would leave `evidence_score` identical for every
    security and make three evidence gates security-blind. Replacing it
    needs a policy ruling on what evidence coverage means, which this
    slice does not have.

    Measured consequence on the live book: **no security's state moves
    on momentum through this path**, because every one of them is
    blocked at an earlier gate. One security's *blocker* does — MSFT's
    moves between `missing_evidence` and `risk_gate`.
    """

    from app.application.executive.decision_evidence_builder import (
        DecisionEvidenceBuilder as B,
    )

    source = inspect.getsource(B._evidence_score)

    assert "company.confidence" in source, (
        "the residual path is gone — update COMPANY_VOTE_DECISION_AUTHORITY.md"
    )

    weak = CompanyCommitteeService().evaluate("AMD", signals(0.0))
    strong = CompanyCommitteeService().evaluate("AMD", signals(-4.28))

    assert strong.confidence > weak.confidence
