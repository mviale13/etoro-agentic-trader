"""#234's security-risk envelope: band-to-total-position ceilings.

The owner ruling of 2026-08-21, pinned case by case: three explicit
policy values with no numeric defaults, volatility and the security's
own drawdown evaluated independently, the existing minimum composition
selecting the smaller ceiling, a maximum *total* position that gives an
at-ceiling holding zero additional room without ever requesting a
reduction — and every sentence under the policy's name, never as a fact
about the security. The absolute volatility veto is untouched in this
slice; decisions are byte-identical beneath all of it.
"""

from __future__ import annotations

import pytest

from app.domain.capital_envelope import (
    EnvelopeKind,
    security_risk_ceiling_for,
)
from app.domain.capital_policy import policy_version
from app.infrastructure.evidence.daily_cycle_store import (
    _decode_envelope,
    _encode_envelope,
)
from app.services.risk_signal_service import RiskSignalService
from tests.test_capital_action_envelope import (
    capacity,
    envelope,
    policy,
    reading_for,
    strategy_document,
)

# ── the policy contract: no defaults, hashed, ordered ───────────────


@pytest.mark.parametrize(
    "field",
    (
        "security_risk_high_max_total_pct",
        "security_risk_severe_max_total_pct",
        "security_risk_unmeasured_max_total_pct",
    ),
)
def test_a_missing_security_risk_field_refuses_by_name(tmp_path, field) -> None:
    """No numeric defaults: absence refuses the whole policy."""

    document = strategy_document()
    del document["capital_envelope"][field]

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert f"capital_envelope.{field}" in reading.refused_because


def test_severe_looser_than_high_is_contradictory(tmp_path) -> None:
    document = strategy_document()
    document["capital_envelope"]["security_risk_severe_max_total_pct"] = 3.0

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "SECURITY_RISK_SEVERE <= SECURITY_RISK_HIGH" in reading.refused_because


def test_unmeasured_looser_than_high_is_contradictory(tmp_path) -> None:
    """Missing evidence must never buy a larger envelope than measured."""

    document = strategy_document()
    document["capital_envelope"]["security_risk_unmeasured_max_total_pct"] = 3.0

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "SECURITY_RISK_UNMEASURED <= SECURITY_RISK_HIGH" in reading.refused_because


def test_the_three_values_are_in_the_canonical_policy_hash(tmp_path) -> None:
    """A security-risk edit is a policy change, visibly."""

    base = reading_for(tmp_path, strategy_document()).policy

    changed_document = strategy_document()
    changed_document["capital_envelope"]["security_risk_high_max_total_pct"] = 3.0
    changed = reading_for(tmp_path, changed_document).policy

    assert base is not None and changed is not None
    assert base.version != changed.version

    # And directly at the hash: only the named field moved.
    values = {"security_risk_high_max_total_pct": 2.0}
    assert policy_version(values) != policy_version(
        {"security_risk_high_max_total_pct": 3.0}
    )


# ── the ceiling factory: bands priced, never banded here ────────────


def test_low_and_moderate_add_no_ceiling() -> None:
    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band="MODERATE", drawdown_band="LOW"
    )

    assert ceiling.ceiling_pct is None
    assert ceiling.volatility_ceiling_pct is None
    assert ceiling.drawdown_ceiling_pct is None
    assert ceiling.missing == ()
    assert ceiling.because.startswith("Under your security-risk policy")


def test_high_volatility_caps_at_two_percent() -> None:
    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band="HIGH", drawdown_band="LOW"
    )

    assert ceiling.ceiling_pct == 2.0
    assert ceiling.volatility_ceiling_pct == 2.0


def test_severe_volatility_caps_at_one_percent() -> None:
    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band="SEVERE", drawdown_band="LOW"
    )

    assert ceiling.ceiling_pct == 1.0


def test_high_drawdown_caps_at_two_percent_independently() -> None:
    """NFLX's case: the drawdown ceiling needs no volatility support."""

    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band="MODERATE", drawdown_band="HIGH"
    )

    assert ceiling.ceiling_pct == 2.0
    assert ceiling.volatility_ceiling_pct is None
    assert ceiling.drawdown_ceiling_pct == 2.0


def test_the_two_measurements_are_never_substituted() -> None:
    """AMD's case: each measurement prices its own band; min selects."""

    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band="SEVERE", drawdown_band="MODERATE"
    )

    assert ceiling.volatility_ceiling_pct == 1.0
    assert ceiling.drawdown_ceiling_pct is None
    assert ceiling.ceiling_pct == 1.0


def test_an_unmeasured_reading_caps_at_one_percent_and_is_named() -> None:
    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band=None, drawdown_band="MODERATE"
    )

    assert ceiling.ceiling_pct == 1.0
    assert ceiling.missing == ("the security's annualised volatility is unmeasured",)
    assert "annualised volatility is unmeasured" in ceiling.because


def test_both_readings_missing_names_both() -> None:
    ceiling = security_risk_ceiling_for(
        policy=policy(), volatility_band=None, drawdown_band=None
    )

    assert ceiling.ceiling_pct == 1.0
    assert len(ceiling.missing) == 2


def test_a_band_outside_the_vocabulary_is_refused_loudly() -> None:
    with pytest.raises(ValueError):
        security_risk_ceiling_for(
            policy=policy(), volatility_band="EXTREME", drawdown_band="LOW"
        )

    # No SEVERE drawdown band exists in this slice, and none is
    # invented by silently pricing one.
    with pytest.raises(ValueError):
        security_risk_ceiling_for(
            policy=policy(), volatility_band="LOW", drawdown_band="SEVERE"
        )


def test_the_bands_are_the_risk_signals_own() -> None:
    """AMD's 71.8% is SEVERE and NFLX-deep drawdowns are HIGH — from
    `risk-bands@1`'s own thresholds, not a second banding here."""

    bands = RiskSignalService()

    assert bands.volatility_level(0.718) == "SEVERE"
    assert bands.volatility_level(0.50) == "HIGH"
    assert bands.volatility_level(0.30) == "MODERATE"
    assert bands.volatility_level(None) is None
    assert bands.drawdown_level(0.45) == "HIGH"
    assert bands.drawdown_level(0.30) == "MODERATE"
    assert bands.drawdown_level(None) is None


# ── the envelope composition: the ruling's acceptance cases ─────────


def test_amd_severe_volatility_binds_at_one_percent() -> None:
    """SEVERE volatility, MODERATE drawdown: the 1% ceiling binds."""

    result = envelope("open", volatility_band="SEVERE", drawdown_band="MODERATE")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 1.0
    assert result.security_risk_ceiling_pct == 1.0
    assert result.security_risk_capped is True
    assert "under your security-risk policy" in result.stated.lower()
    assert "not the company's quality" in result.stated


def test_nflx_high_drawdown_caps_at_two_even_with_moderate_volatility() -> None:
    result = envelope("open", volatility_band="MODERATE", drawdown_band="HIGH")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 2.0
    assert result.security_risk_ceiling_pct == 2.0
    assert result.security_risk_capped is True


def test_a_missing_reading_constrains_to_one_percent_not_a_vanished_course() -> None:
    result = envelope("open", volatility_band=None, drawdown_band="MODERATE")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 1.0
    assert "annualised volatility is unmeasured" in result.security_risk_because


def test_an_at_ceiling_holding_gets_zero_add_room_and_no_reduce() -> None:
    """1.2% held under a 1% SEVERE ceiling: zero room, course intact."""

    result = envelope(
        "add",
        cap=capacity(weight=1.2),
        volatility_band="SEVERE",
        drawdown_band="MODERATE",
    )

    assert result.course == "add"
    assert result.kind is EnvelopeKind.ZERO_CAPACITY
    assert result.kind is not EnvelopeKind.REDUCTION_FLOOR
    assert "under your security-risk policy" in result.binding_constraint
    assert result.security_risk_capped is True


def test_low_and_moderate_controls_are_unchanged() -> None:
    """The calm corpus is byte-identical to the pre-ruling envelope."""

    calm = envelope("open", volatility_band="LOW", drawdown_band="LOW")
    moderate = envelope("open", volatility_band="MODERATE", drawdown_band="MODERATE")

    for result in (calm, moderate):
        assert result.kind is EnvelopeKind.UPWARD_BOUNDED
        assert result.final_pct == 3.0
        assert result.security_risk_ceiling_pct is None
        assert result.security_risk_capped is False
        assert result.binding_constraint == calm.binding_constraint
        assert result.stated == calm.stated


def test_an_equal_ceiling_changes_no_figure_and_no_wording() -> None:
    """STARTER at 1% and a SEVERE 1% ceiling tie: the existing naming
    stands, because a term that reduces nothing renames nothing."""

    result = envelope(
        "open",
        gaps=("one named gap",),
        volatility_band="SEVERE",
        drawdown_band="MODERATE",
    )

    assert result.final_pct == 1.0
    assert result.starter_capped is True
    assert result.security_risk_capped is False
    assert "Named uncertainty" in result.stated


def test_the_portfolio_drawdown_gate_stays_a_separate_account_gate() -> None:
    """The account-level budget refuses first, in its own words."""

    result = envelope("open", drawdown=25.0, volatility_band="SEVERE")

    assert result.kind is EnvelopeKind.REFUSED
    assert "drawdown budget" in result.because


def test_reduce_semantics_are_unchanged_by_the_ceiling() -> None:
    """The ceiling applies to OPEN and ADD; a reduction consults nothing here."""

    result = envelope(
        "reduce",
        cap=capacity(weight=25.0),
        volatility_band="SEVERE",
        drawdown_band="HIGH",
    )

    assert result.kind is EnvelopeKind.REDUCTION_FLOOR
    assert result.final_pct == 5.0
    assert result.security_risk_ceiling_pct is None
    assert result.security_risk_capped is False


def test_missing_risk_evidence_never_buys_a_larger_envelope() -> None:
    """Monotonicity, the ruling's own sentence: 1% <= 2% <= unconstrained."""

    unmeasured = envelope("open", volatility_band=None, drawdown_band=None)
    high = envelope("open", volatility_band="HIGH", drawdown_band="LOW")
    calm = envelope("open", volatility_band="LOW", drawdown_band="LOW")

    assert unmeasured.final_pct is not None and high.final_pct is not None
    assert calm.final_pct is not None
    assert unmeasured.final_pct <= high.final_pct <= calm.final_pct


# ── the store: optional under the same schema ───────────────────────


def test_the_security_risk_fields_round_trip_through_the_store() -> None:
    result = envelope("open", volatility_band="SEVERE", drawdown_band="MODERATE")

    decoded = _decode_envelope(_encode_envelope(result))

    assert decoded == result


def test_a_pre_ruling_record_decodes_as_carrying_no_ceiling() -> None:
    """Absent keys are the old contract, never a ceiling of zero."""

    raw = _encode_envelope(envelope("open"))

    assert raw is not None

    for key in (
        "security_risk_ceiling_pct",
        "security_risk_because",
        "security_risk_capped",
    ):
        del raw[key]

    decoded = _decode_envelope(raw)

    assert decoded is not None
    assert decoded.security_risk_ceiling_pct is None
    assert decoded.security_risk_because == ""
    assert decoded.security_risk_capped is False
