"""What blocks a case, named by the gate that stopped it.

The measured defect, from the cycle recorded on 2026-08-20: the
homepage listed MSFT (waiting), GRE.MC (research) and AMD and UUUU
(both rejected) in one ranked table headed *"Top opportunities the CIO
evaluated"*, with a *"What is missing"* column showing an em dash for
AMD. Nothing is missing for AMD. Its own price record is too violent
for this platform's risk policy — 71.8% annualised volatility, the
SEVERE band, risk 85 against a maximum of 70 — and on the same
evidence its growth analyst reads STRONG.

Three properties are tested here:

- the blocker is the **branch that fired**, so REJECT reached three
  different ways produces three different causes;
- a gate that is not about the business says so, and carries the
  analyst verdicts that survive it;
- a conviction never travels without an account of what it is.
"""

from __future__ import annotations

import pytest

from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.decision_blocker import BlockerKind, DecisionBlocker
from app.domain.finding import Dimension, Finding, FindingLedger
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.risk_signal import RiskSignal

#: AMD's own reading, as the live store held it on 2026-08-20.
AMD_RISK = RiskSignal(
    level="SEVERE",
    volatility=0.718,
    max_drawdown=0.2776,
    confidence=90,
    evidence=(
        Finding.adverse("Annualised volatility is 71.8% over the past year."),
        Finding.neutral("Deepest fall over the past year was 27.8%."),
    ),
    market_sensitivity=MarketSensitivity(
        beta=3.1584,
        correlation=0.5679,
        observations=250,
        benchmark="SPY",
    ),
)

#: The analysts' verdicts on the same company, in the same cycle.
AMD_RESEARCH = FindingLedger.of(
    (
        Finding.favourable(
            "Growth is strong — Revenue growth is 50.1%. Earnings growth is 159.5%.",
            Dimension.RESEARCH,
        ),
        Finding.favourable(
            "Profitability is strong — Gross margin is 55.7%.",
            Dimension.RESEARCH,
        ),
        # Not an analyst verdict, and never carried as a counterweight:
        # the ledger's order is not a ranking and its dimensions are
        # what select, so a momentum reading stays out of this.
        Finding.favourable("Short-term price momentum is positive."),
    )
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
        "findings": AMD_RESEARCH,
    }

    values.update(overrides)

    return DecisionEvidence(**values)  # type: ignore[arg-type]


def test_a_clean_case_states_that_nothing_blocks_it() -> None:
    decision = ArtificialCIO().decide(evidence())

    assert decision.state is DecisionState.RECOMMEND
    assert decision.blocker is not None
    assert decision.blocker.kind is BlockerKind.NONE
    assert decision.blocker.blocks is False
    assert decision.blocker.stated


def test_amds_risk_refusal_names_the_reading_beneath_the_score() -> None:
    """The sentence an investor is owed, with its figures.

    *Risk 85* is unreadable on its own: it is a band's severity turned
    into a number. What was measured is the volatility, and the band is
    this platform's policy over it — so both travel with the refusal.
    """

    decision = ArtificialCIO().decide(
        evidence(risk_score=85, risk_reading=AMD_RISK),
    )

    assert decision.state is DecisionState.REJECT

    blocker = decision.blocker

    assert blocker is not None
    assert blocker.kind is BlockerKind.RISK_GATE
    assert blocker.stated == (
        "Blocked by the current risk policy: annualised volatility was "
        "71.8%, placing AMD in this platform's severe-risk band and "
        "producing risk 85 against a maximum of 70."
    )


def test_a_risk_refusal_is_not_a_verdict_on_the_business() -> None:
    """Invariant 10 on a gate: the measurement travels, the meaning does not.

    A risk ruling establishes that the price record is violent. It
    establishes nothing about the company, and the analysts reading the
    same cycle's evidence said growth and profitability are strong.
    """

    decision = ArtificialCIO().decide(
        evidence(risk_score=85, risk_reading=AMD_RISK),
    )

    blocker = decision.blocker

    assert blocker is not None
    assert blocker.does_not_say == (
        "This is a risk ruling. It does not say AMD is a weak business."
    )
    assert blocker.despite == (
        "Growth is strong — Revenue growth is 50.1%. Earnings growth is 159.5%.",
        "Profitability is strong — Gross margin is 55.7%.",
    )


def test_the_refusal_claims_only_what_it_can_prove() -> None:
    """No reading, no volatility sentence — and no invented one."""

    decision = ArtificialCIO().decide(evidence(risk_score=85))

    blocker = decision.blocker

    assert blocker is not None
    assert blocker.stated == (
        "Blocked by the current risk policy: risk scores 85 against a maximum of 70."
    )
    assert "volatility" not in blocker.stated


def test_an_analyst_veto_claims_nothing_about_what_it_does_not_say() -> None:
    """The veto is a SELL vote, and a SELL vote may be about the business.

    It is composed from quality, value, momentum and risk together, so
    unlike the risk ceiling it cannot be declared silent about the
    company. The analysts who disagree are still quoted — that is a
    disagreement on the record — but no disclaimer is attached.
    """

    decision = ArtificialCIO().decide(evidence(analyst_veto=True))

    blocker = decision.blocker

    assert blocker is not None
    assert blocker.kind is BlockerKind.ANALYST_VETO
    assert blocker.does_not_say == ""
    assert blocker.despite


def test_a_quality_gate_carries_no_counterweight_and_no_disclaimer() -> None:
    """The one kind that *is* a statement about the business.

    Quoting an analyst against it would argue with the decision rather
    than qualify it, and *"this does not say the business is weak"*
    would simply be false.
    """

    decision = ArtificialCIO().decide(evidence(quality_score=20))

    blocker = decision.blocker

    assert blocker is not None
    assert blocker.kind is BlockerKind.QUALITY_GATE
    assert blocker.despite == ()
    assert blocker.does_not_say == ""


@pytest.mark.parametrize(
    ("overrides", "kind"),
    [
        ({"hard_reject": True}, BlockerKind.POLICY_GATE),
        ({"analyst_veto": True}, BlockerKind.ANALYST_VETO),
        ({"security_evidenced": False}, BlockerKind.MISSING_EVIDENCE),
        ({"risk_score": 85}, BlockerKind.RISK_GATE),
        ({"quality_score": 20}, BlockerKind.QUALITY_GATE),
        ({"evidence_score": 10}, BlockerKind.MISSING_EVIDENCE),
        ({"quality_score": None}, BlockerKind.QUALITY_GATE),
        ({"quality_score": 50}, BlockerKind.QUALITY_GATE),
        ({"evidence_score": 50}, BlockerKind.MISSING_EVIDENCE),
        ({"quality_score": 70}, BlockerKind.QUALITY_GATE),
        ({"evidence_score": 70}, BlockerKind.MISSING_EVIDENCE),
        ({"valuation_score": None}, BlockerKind.VALUATION_GATE),
        ({"risk_score": None}, BlockerKind.RISK_GATE),
        ({"valuation_score": 40}, BlockerKind.VALUATION_GATE),
        ({"portfolio_fit_score": None}, BlockerKind.PORTFOLIO_FIT_GATE),
        ({"portfolio_fit_score": 10}, BlockerKind.PORTFOLIO_FIT_GATE),
        ({"actionable_now": False}, BlockerKind.EXECUTION_TRIGGER),
    ],
)
def test_every_branch_names_its_own_gate(
    overrides: dict[str, object],
    kind: BlockerKind,
) -> None:
    """One case, one gate moved at a time, across the whole cascade.

    REJECT is reached three ways here — a policy gate, an analyst veto
    and the risk ceiling — and a surface reading the state back into a
    cause could not tell them apart.
    """

    decision = ArtificialCIO().decide(evidence(**overrides))

    assert decision.blocker is not None
    assert decision.blocker.kind is kind
    assert decision.blocker.stated
    assert decision.blocker.blocks


def test_the_cascade_produces_every_declared_kind_but_the_platform_limit() -> None:
    """No member without a branch — #119's rule, applied to this table.

    `PLATFORM_LIMIT` is the digital-asset path's, which does not run
    here. Everything else in the vocabulary is produced by the equity
    cascade above, and a member nothing can produce would make the
    taxonomy read as though it worked.
    """

    produced = {
        ArtificialCIO().decide(evidence(**overrides)).blocker.kind  # type: ignore[union-attr]
        for overrides in (
            {},
            {"hard_reject": True},
            {"analyst_veto": True},
            {"security_evidenced": False},
            {"risk_score": 85},
            {"quality_score": 20},
            {"evidence_score": 10},
            {"valuation_score": 40},
            {"portfolio_fit_score": 10},
            {"actionable_now": False},
        )
    }

    assert produced == set(BlockerKind) - {BlockerKind.PLATFORM_LIMIT}


# ── conviction, and what it is ──────────────────────────────────────


def test_a_capped_conviction_says_it_was_capped() -> None:
    """AMD's 40 is `conviction-mean@1`'s REJECT cap, not a mean of 40."""

    decision = ArtificialCIO().decide(
        evidence(
            quality_score=62,
            evidence_score=60,
            valuation_score=25,
            risk_score=85,
            portfolio_fit_score=60,
            risk_reading=AMD_RISK,
        ),
    )

    assert decision.conviction == 40
    assert decision.conviction_basis == (
        "A decision score, not enthusiasm: computed from 5 of 5 score "
        "families under conviction-mean@1, capped at 40 by the REJECT state."
    )

    # And the count is carried, not only worded: the sentence states 5
    # of 5 because the decision itself does.
    assert decision.conviction_participating == 5
    assert decision.conviction_expected == 5
    assert decision.conviction_absent_families == ()


def test_an_uncapped_conviction_names_the_cap_it_did_not_reach() -> None:
    decision = ArtificialCIO().decide(evidence())

    assert decision.conviction is not None
    assert decision.conviction < 100
    assert "where the RECOMMEND state caps it at 100" in decision.conviction_basis


def test_a_withheld_conviction_says_why_there_is_no_number() -> None:
    decision = ArtificialCIO().decide(evidence(strengths=()))

    assert decision.conviction is None
    assert "cites no supporting reason" in decision.conviction_basis


# ── the record ──────────────────────────────────────────────────────


def test_a_blocker_round_trips_through_the_cycle_store(tmp_path: object) -> None:
    from app.domain.daily_cycle import DecisionSummary
    from app.infrastructure.evidence.daily_cycle_store import (
        _decode_decision,
        _encode_decision,
    )

    summary = DecisionSummary(
        symbol="AMD",
        state="REJECT",
        rationale="Risk exceeds the maximum permitted by policy.",
        conviction=40,
        conviction_basis="capped at 40 by the REJECT state",
        blocker=DecisionBlocker.of(
            BlockerKind.RISK_GATE,
            "Blocked by the current risk policy.",
            "AMD",
            despite=("Growth is strong.",),
        ),
    )

    restored = _decode_decision(_encode_decision(summary))

    assert restored == summary


def test_a_record_written_before_blockers_decodes_as_naming_none() -> None:
    """A stored state is not a stored cause, and is never read as one."""

    from app.infrastructure.evidence.daily_cycle_store import _decode_decision

    restored = _decode_decision(
        {
            "symbol": "AMD",
            "state": "REJECT",
            "rationale": "Risk exceeds the maximum permitted by policy.",
            "conviction": 40,
        }
    )

    assert restored.blocker is None
    assert restored.conviction_basis == ""


def test_an_unknown_blocker_kind_is_not_read_as_nothing_blocking() -> None:
    from app.infrastructure.evidence.daily_cycle_store import _decode_blocker

    assert _decode_blocker({"kind": "a_gate_from_a_later_version"}) is None


def test_a_digital_asset_is_blocked_by_this_platform_and_says_so() -> None:
    """The crypto path's ceiling, carried as what it is.

    A token is not blocked by an unread measurement or by a gate it
    failed: this platform judges an investment case on business quality
    and valuation, and a digital asset has neither to assess. The
    sentence is the ceiling's own, and `despite` stays empty for the
    same reason `key_strengths` does — a structural conclusion is not a
    strength.
    """

    from app.cio.digital_asset_decision import (
        DigitalAssetDecision,
        as_executive_decision,
    )

    decision = as_executive_decision(
        DigitalAssetDecision(
            symbol="HYPE",
            state=DecisionState.INVESTIGATE,
            rationale="Structural evidence is established.",
        )
    )

    assert decision.blocker is not None
    assert decision.blocker.kind is BlockerKind.PLATFORM_LIMIT
    assert "limit of this platform" in decision.blocker.stated
    assert decision.blocker.despite == ()
    assert decision.conviction is None
    assert "cited as support" in decision.conviction_basis


def test_the_cycle_response_carries_the_cause_and_the_basis() -> None:
    """The wire, because a field that stops at the API is not a surface."""

    from app.api.models.cycle import CourseResponse
    from app.domain.daily_cycle import DecisionSummary

    response = CourseResponse.of(
        DecisionSummary(
            symbol="AMD",
            state="REJECT",
            rationale="Risk exceeds the maximum permitted by policy.",
            conviction=40,
            conviction_basis="capped at 40 by the REJECT state",
            blocker=DecisionBlocker.of(
                BlockerKind.RISK_GATE,
                "Blocked by the current risk policy.",
                "AMD",
                despite=("Growth is strong.",),
            ),
        )
    )

    assert response.conviction_basis == "capped at 40 by the REJECT state"
    assert response.blocker is not None
    assert response.blocker.kind == "risk_gate"
    assert response.blocker.stated == "Blocked by the current risk policy."
    assert response.blocker.despite == ["Growth is strong."]
    assert response.blocker.does_not_say.startswith("This is a risk ruling.")
