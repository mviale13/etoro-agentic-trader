"""The valuation refusal speaks the investor's language, not the score's.

The owner's product feedback of 2026-08-24. The live specimen was MSFT:

    "Blocked by what it costs: valuation scores 55 against the 60 a
    recommendation needs."

The investor does not need the internal score to understand the
decision. The sentence now names what was measured, what it means for
the course, and what could reasonably change the conclusion — composed
deterministically from the typed reading `DecisionEvidence` carries
(`valuation_reading`, `risk_reading`'s precedent), with no model and no
prose parsing. The score survives on the payload and in the score basis
as audit detail; the gate reads it unchanged.
"""

from __future__ import annotations

from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.asset_class import AssetClass
from app.domain.decision_blocker import BlockerKind
from app.domain.valuation_comparison import ValuationObservation
from app.domain.value_signal import ValueSignal


def reading(band: str, pe: float) -> ValueSignal:
    return ValueSignal(
        valuation=band,
        confidence=85,
        evidence=(),
        observation=ValuationObservation(
            metric="forward_pe",
            label="Forward P/E",
            value=pe,
        ),
    )


def evidence(**overrides: object) -> DecisionEvidence:
    """MSFT as cycle `d98cf859932e` scored it, at the valuation gate."""

    values: dict[str, object] = {
        "symbol": "MSFT",
        "quality_score": 80,
        "evidence_score": 82,
        "valuation_score": 55,
        "risk_score": 45,
        "portfolio_fit_score": 68,
        "security_evidenced": True,
        "valuation_reading": reading("FAIR", 20.6),
    }
    values.update(overrides)

    return DecisionEvidence(**values)  # type: ignore[arg-type]


def blocker(**overrides: object):
    decision = ArtificialCIO().decide(evidence(**overrides))

    assert decision.blocker is not None

    return decision, decision.blocker


# ── the live specimen ───────────────────────────────────────────────


def test_the_msft_specimen_reads_as_cio_advice() -> None:
    """Acceptance 1 and 2: natural advice, no internal score needed."""

    decision, blocked = blocker()

    assert blocked.kind is BlockerKind.VALUATION_GATE
    assert blocked.stated == (
        "At 20.6× forward earnings, MSFT sits in this platform's middle "
        "valuation band: not overpriced, but not cheap enough to support "
        "a buy recommendation. This is a house rule applied to one "
        "measured multiple, not a market comparison or a judgment on "
        "the business. Wait for the forward P/E to move into the "
        "cheaper band before reconsidering a purchase."
    )

    # The decision itself is byte-identical to what the score sentence
    # produced: same state, same kind, same scores. (This fixture cites
    # no supporting finding, so conviction is withheld by
    # conviction-mean@2 — unchanged behaviour, pinned elsewhere.)
    assert decision.state is DecisionState.PREPARE
    assert decision.conviction is None


def test_the_score_is_audit_detail_not_explanation() -> None:
    """Never "score X against threshold Y" as the primary explanation."""

    _, blocked = blocker()

    for banned in ("score", "55", "60", "against the"):
        assert banned not in blocked.stated, banned

    # The number itself survives where auditors read, untouched.
    assert evidence().valuation_score == 55


# ── the four shapes, distinct and truthful ──────────────────────────


def test_the_expensive_band_names_the_bar_and_not_the_word() -> None:
    """Never call a company expensive: this platform holds one unaudited
    multiple and no benchmark, so the band is worded as its own bar."""

    _, blocked = blocker(
        valuation_score=25, valuation_reading=reading("EXPENSIVE", 29.3)
    )

    stated = blocked.stated

    assert stated == (
        "At 29.3× forward earnings, MSFT sits above the valuation range "
        "this platform accepts for a buy recommendation. This is a "
        "house rule applied to one measured multiple, not a market "
        "comparison or a judgment on the business. Wait for the forward "
        "P/E to move into a more attractive band before reconsidering a "
        "purchase."
    )
    assert "expensive" not in stated.lower()


def test_the_fair_band_is_mixed_not_condemned() -> None:
    _, blocked = blocker()

    stated = blocked.stated

    assert "middle valuation band" in stated
    assert "not overpriced, but not cheap enough" in stated


def test_the_four_shapes_are_distinct() -> None:
    """Expensive, mixed, incomplete and unavailable read differently."""

    expensive = blocker(
        valuation_score=25, valuation_reading=reading("EXPENSIVE", 29.3)
    )[1].stated
    fair = blocker()[1].stated
    incomplete = blocker(valuation_reading=None)[1].stated
    unavailable = blocker(valuation_score=None)[1].stated

    assert len({expensive, fair, incomplete, unavailable}) == 4


def test_a_missing_reading_claims_no_metric() -> None:
    """The score exists and the reading was not carried: nothing quotable,
    so nothing is quoted and no band is asserted."""

    _, blocked = blocker(valuation_reading=None)

    assert blocked.stated == (
        "The available evidence does not establish that the shares offer "
        "good value at today's price, so valuation cannot support a "
        "purchase."
    )


def test_an_unmeasured_valuation_speaks_the_owners_sentence() -> None:
    """The incomplete case, exactly as the feedback words it."""

    decision, blocked = blocker(valuation_score=None, valuation_reading=None)

    assert decision.state is DecisionState.PREPARE
    assert blocked.kind is BlockerKind.VALUATION_GATE
    assert blocked.stated == (
        "The available evidence does not establish whether the shares "
        "offer good value at today's price, so valuation cannot yet "
        "support a purchase."
    )

    # The rationale keeps its own long-pinned wording; only the
    # investor-facing blocker changed.
    assert "valuation has not been measured" in decision.rationale


def test_a_funds_platform_limit_wording_is_untouched() -> None:
    """A fund has no earnings to be valued against — that sentence is
    already exact and stays the blocker."""

    _, blocked = blocker(
        valuation_score=None,
        valuation_reading=None,
        asset_class=AssetClass.ETF,
    )

    assert "has no earnings to be valued" in blocked.stated
    assert "No recommendation is made without that." in blocked.stated


# ── what the sentence must never do ─────────────────────────────────


def test_no_shape_manufactures_a_figure_or_a_verdict() -> None:
    """No target price, expected return, computed margin of safety —
    and no implication that a poor valuation is a poor business."""

    shapes = [
        blocker(valuation_score=25, valuation_reading=reading("EXPENSIVE", 29.3)),
        blocker(),
        blocker(valuation_reading=None),
        blocker(valuation_score=None),
    ]

    for _decision, blocked in shapes:
        stated = blocked.stated

        for banned in ("target price", "expected return", "upside", "%"):
            assert banned not in stated, banned

        # A valuation ruling says nothing about the business — carried
        # structurally beside every one of these sentences.
        assert blocked.does_not_say == (
            "This is a valuation ruling. It does not say MSFT is a weak business."
        )


def test_the_change_of_course_is_possibility_not_promise() -> None:
    """Reconsidering is what is offered — never a promised outcome."""

    _, blocked = blocker()

    assert "before reconsidering a purchase" in blocked.stated
    assert "will " not in blocked.stated
    assert "guarantee" not in blocked.stated.lower()


def test_no_shape_claims_a_margin_of_safety() -> None:
    """The platform measured no intrinsic value, expected return or
    margin of safety — it holds one multiple and applies a house band —
    so none may be said to be missing. The owner's correction 1."""

    shapes = [
        blocker(valuation_score=25, valuation_reading=reading("EXPENSIVE", 29.3)),
        blocker(),
        blocker(valuation_score=55, valuation_reading=reading("CHEAP", 12.0)),
        blocker(valuation_reading=None),
        blocker(valuation_score=None),
    ]

    for _decision, blocked in shapes:
        assert "margin of safety" not in blocked.stated.lower()


def test_cash_flow_is_never_named_as_clearing_this_gate() -> None:
    """Cash flow is not an input to pe-bands, and generic earnings
    evidence does not necessarily move the forward P/E. The owner's
    correction 2."""

    shapes = [
        blocker(valuation_score=25, valuation_reading=reading("EXPENSIVE", 29.3)),
        blocker(),
        blocker(valuation_score=55, valuation_reading=reading("CHEAP", 12.0)),
        blocker(valuation_reading=None),
        blocker(valuation_score=None),
    ]

    for _decision, blocked in shapes:
        lowered = blocked.stated.lower()

        assert "cash flow" not in lowered
        assert "cash-flow" not in lowered
        assert "stronger earnings" not in lowered


def test_the_reconsideration_condition_is_the_gates_own_input() -> None:
    """What could change the ruling is the multiple moving bands — the
    one input pe-bands actually reads. The owner's correction 3."""

    for overrides in (
        {},
        {"valuation_score": 25, "valuation_reading": reading("EXPENSIVE", 29.3)},
    ):
        _, blocked = blocker(**overrides)

        assert "Wait for the forward P/E to move into" in blocked.stated
        assert "band before reconsidering a purchase" in blocked.stated


def test_no_target_price_or_guaranteed_outcome() -> None:
    """Crossing the band earns reconsideration, never a promised
    recommendation. The owner's correction 3, second half."""

    for overrides in (
        {},
        {"valuation_score": 25, "valuation_reading": reading("EXPENSIVE", 29.3)},
    ):
        _, blocked = blocker(**overrides)
        stated = blocked.stated

        for banned in ("target price", "will be recommended", "will produce", "$"):
            assert banned not in stated, banned

        assert "reconsidering" in stated


def test_the_builder_carries_the_reading_to_the_decision() -> None:
    """The carriage itself, through the real builder.

    The unit fixtures above set `valuation_reading` directly, so
    without this pin the production line that populates it could be
    deleted and every sentence would silently fall back to the
    nothing-quotable shape.
    """

    from tests.test_security_evidence import build_evidence, make_brain, make_company

    company = make_company("MSFT")
    evidence_built = build_evidence(make_brain(evidence={"MSFT": (company,)}), "MSFT")

    assert evidence_built.valuation_reading is company.signals.value


def test_an_unknown_band_names_the_fact_and_claims_no_band() -> None:
    """A CHEAP band under a custom policy bar, or a future vocabulary:
    the measured multiple is named, no band word is asserted."""

    _, blocked = blocker(valuation_score=55, valuation_reading=reading("CHEAP", 12.0))

    stated = blocked.stated

    assert "At 12.0× forward earnings" in stated
    assert "does not clear the bar this policy sets" in stated
    assert "cheap" not in stated.lower().replace("not cheap", "")
