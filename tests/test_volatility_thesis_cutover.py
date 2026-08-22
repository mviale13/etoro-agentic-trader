"""Slice 2: historical volatility no longer rejects an investment thesis.

The owner's ruling of 2026-08-21 removed exactly one transition from
the Artificial CIO's cascade — `risk_score > maximum_acceptable_risk →
REJECT` — on the finding that a security's own price record measures
how violently it has moved and says nothing about whether the case is
sound. AMD was REJECTed on 71.8% annualised volatility while its own
analysts read growth, profitability, balance sheet and cash flow as
strong or better.

Nothing about risk was weakened. What these cases pin is the pair: the
gate is gone, **and** every reading it rested on still travels, still
scores, and still bounds position size through #236's security-risk
ceiling. A cutover that quietly deleted the measurement would pass the
first half of this file and fail the second.
"""

from __future__ import annotations

import pytest

from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_policy import DecisionPolicy
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.capital_envelope import security_risk_ceiling_for
from app.domain.decision_blocker import BlockerKind
from app.domain.decision_rules import DECISION_GATES
from app.domain.finding import Finding
from app.domain.risk_signal import RiskSignal
from app.services.risk_signal_service import RiskSignalService
from tests.test_capital_action_envelope import policy as capital_policy

#: AMD as the live store reads it: severe volatility, moderate drawdown.
AMD_RISK = RiskSignal(
    level="SEVERE",
    volatility=0.718,
    max_drawdown=0.278,
    confidence=90,
    evidence=(Finding.adverse("Annualised volatility is 71.8% over the past year."),),
)


def evidence(**overrides: object) -> DecisionEvidence:
    """A case that clears every gate, so each test moves exactly one."""

    values: dict[str, object] = {
        "symbol": "AMD",
        "quality_score": 80,
        "evidence_score": 80,
        "valuation_score": 80,
        "risk_score": 20,
        "portfolio_fit_score": 80,
        "actionable_now": True,
        "strengths": ("Large-cap company.",),
    }

    values.update(overrides)

    return DecisionEvidence(**values)  # type: ignore[arg-type]


# ── the gate is gone ────────────────────────────────────────────────


@pytest.mark.parametrize("score", [71, 85, 100])
def test_no_risk_score_rejects_a_thesis(score: int) -> None:
    """Not at the boundary, not at AMD's, not at the ceiling."""

    decision = ArtificialCIO().decide(evidence(risk_score=score))

    assert decision.state is not DecisionState.REJECT


def test_a_severe_case_is_not_blocked_by_a_risk_ruling() -> None:
    decision = ArtificialCIO().decide(
        evidence(risk_score=85, risk_reading=AMD_RISK),
    )

    assert decision.blocker is not None
    assert decision.blocker.kind is not BlockerKind.RISK_GATE


def test_the_obsolete_sentence_is_unproducible() -> None:
    """No newly produced cycle may still display it.

    Asserted over the *whole cascade* rather than one case, because the
    ruling is about what this platform can say at all — a surviving
    branch that produced it under some other combination would satisfy
    a single-case test and violate the ruling.
    """

    cascade = (
        {},
        {"hard_reject": True},
        {"analyst_veto": True},
        {"security_evidenced": False},
        {"risk_score": 85, "risk_reading": AMD_RISK},
        {"risk_score": None},
        {"quality_score": 20},
        {"quality_score": None},
        {"evidence_score": 10},
        {"valuation_score": None},
        {"valuation_score": 40},
        {"portfolio_fit_score": 10},
        {"actionable_now": False},
    )

    for overrides in cascade:
        decision = ArtificialCIO().decide(evidence(**overrides))

        assert decision.blocker is not None

        stated = decision.blocker.stated

        assert "Blocked by the current risk policy" not in stated, overrides
        assert "71.8%" not in stated, overrides
        assert decision.rationale != "Risk exceeds the maximum permitted by policy."


def test_the_gate_removal_is_pinned_as_a_rule_change() -> None:
    """A cascade may not lose a gate without its rule version moving."""

    assert DECISION_GATES.version == 3


# ── and nothing about risk was weakened ─────────────────────────────


def test_every_preserved_reading_still_travels() -> None:
    """Volatility, drawdown, band, severity and findings — all intact."""

    assert AMD_RISK.volatility == 0.718
    assert AMD_RISK.max_drawdown == 0.278
    assert AMD_RISK.level == "SEVERE"
    assert AMD_RISK.severity == RiskSignal.SEVERITIES["SEVERE"]
    assert AMD_RISK.evidence

    # The bands themselves are untouched by the cutover.
    bands = RiskSignalService()

    assert bands.volatility_level(0.718) == "SEVERE"
    assert bands.drawdown_level(0.278) == "MODERATE"


def test_safety_still_scores_into_conviction() -> None:
    """Removed as a gate, preserved as a score.

    The proof the measurement was not merely deleted: a violent case
    still carries less conviction than an otherwise identical calm one.
    """

    violent = ArtificialCIO().decide(evidence(risk_score=85, risk_reading=AMD_RISK))
    calm = ArtificialCIO().decide(evidence(risk_score=20))

    assert violent.conviction is not None and calm.conviction is not None
    assert violent.conviction < calm.conviction

    # And safety is still one of the five families that spoke.
    assert violent.conviction_participating == 5
    assert "safety" not in violent.conviction_absent_families


def test_an_unmeasured_risk_still_refuses_a_recommendation() -> None:
    """The gate the ruling preserves, distinguished from the one it removed.

    Not knowing is not the same as knowing it is bad — and it is still
    a reason not to progress.
    """

    decision = ArtificialCIO().decide(evidence(risk_score=None))

    assert decision.state is DecisionState.PREPARE
    assert decision.blocker is not None
    assert decision.blocker.kind is BlockerKind.RISK_GATE
    assert "unmeasured risk" in decision.blocker.stated


def test_the_dead_threshold_is_gone_from_executed_code() -> None:
    """The owner's structural control, enforced rather than asserted.

    `maximum_acceptable_risk` was deleted as dead — the envelope reads
    the risk band and the three explicit CapitalPolicy ceilings, so a
    retained field would read as a live rule while selecting nothing.
    Executed production code may not reference it; the phrase survives
    only in historical prose describing the removed @2 gate, which the
    AST never sees.
    """

    import ast
    import pathlib

    offenders: list[str] = []

    for path in pathlib.Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            named = (
                isinstance(node, ast.Name)
                and node.id == "maximum_acceptable_risk"
                or isinstance(node, ast.Attribute)
                and node.attr == "maximum_acceptable_risk"
                or isinstance(node, ast.Constant)
                and node.value == "maximum_acceptable_risk"
                or isinstance(node, (ast.AnnAssign, ast.arg))
                and getattr(getattr(node, "target", node), "id", None)
                == "maximum_acceptable_risk"
            )

            if named:
                offenders.append(f"{path}:{node.lineno}")

    assert not offenders, offenders

    # And the policy no longer carries it as a field at all.
    assert "maximum_acceptable_risk" not in DecisionPolicy.model_fields


# ── the envelope is where volatility now speaks ─────────────────────


def test_a_severe_security_is_bounded_in_size_rather_than_refused() -> None:
    """The whole shape of the ruling, in one case.

    AMD's thesis survives and AMD's *position* is capped at 1% of the
    portfolio. The measurement did not stop mattering; it stopped
    answering the wrong question.
    """

    decision = ArtificialCIO().decide(evidence(risk_score=85, risk_reading=AMD_RISK))

    assert decision.state is not DecisionState.REJECT

    bands = RiskSignalService()
    ceiling = security_risk_ceiling_for(
        policy=capital_policy(),
        volatility_band=bands.volatility_level(AMD_RISK.volatility),
        drawdown_band=bands.drawdown_level(AMD_RISK.max_drawdown),
    )

    assert ceiling.ceiling_pct == 1.0


def test_no_ceiling_grows_because_a_reading_is_missing() -> None:
    """Acceptance 12, at the boundary the cutover could have moved."""

    bands = RiskSignalService()

    measured = security_risk_ceiling_for(
        policy=capital_policy(),
        volatility_band=bands.volatility_level(AMD_RISK.volatility),
        drawdown_band=bands.drawdown_level(AMD_RISK.max_drawdown),
    )
    unmeasured = security_risk_ceiling_for(
        policy=capital_policy(), volatility_band=None, drawdown_band=None
    )

    assert unmeasured.ceiling_pct is not None
    assert measured.ceiling_pct is not None
    assert unmeasured.ceiling_pct <= measured.ceiling_pct


def test_no_automatic_order_path_exists() -> None:
    """Acceptance 13: the decision layer still only ever states a case."""

    decision = ArtificialCIO().decide(evidence(risk_score=85, risk_reading=AMD_RISK))

    for forbidden in ("buy", "sell", "order", "execute", "trade"):
        assert not hasattr(decision, forbidden)
