"""The strategic allocation, its operating ranges, and what they permit.

The owner's policy of 2026-08-24, pinned. Three things are kept apart
here and were one thing before: a **strategic target** is a
destination, an **operating range** is tactical latitude, and a **hard
limit** is the only allocation boundary that blocks an action.

What the slice replaced: three non-cash targets hardcoded to zero (the
strategy page rendered 0/0/0/5 and totalled 5%), `target_cash_pct: 5`
beside `minimum_cash_pct: 40`, and a capital gate funding from
`max(target, minimum)` — which made whichever cash number happened to
be larger a floor under every deployment.
"""

from __future__ import annotations

import json

import pytest

from app.domain.strategic_allocation import (
    HARD_MAXIMUM_CRYPTO_PCT,
    HARD_MINIMUM_CASH_PCT,
    AllocationBand,
    AllocationStanding,
    StrategicAllocation,
    guidance_for,
    portfolio_guidance_for,
)
from tests.test_capital_action_envelope import (
    OWNER_ALLOCATION,
    capacity,
    envelope,
    policy,
    reading_for,
    strategy_document,
)

#: The live account as the last completed cycle recorded it.
LIVE = {"stocks": 10.3, "etfs": 0.0, "crypto": 35.63, "cash": 54.07}


def band(asset: str) -> AllocationBand:
    found = OWNER_ALLOCATION.band(asset)

    assert found is not None

    return found


# ── acceptance 1–2: the plan totals 100, or it refuses ──────────────


def test_the_strategic_targets_total_one_hundred() -> None:
    assert [b.target_pct for b in OWNER_ALLOCATION.bands] == [35.0, 15.0, 25.0, 25.0]
    assert sum(b.target_pct for b in OWNER_ALLOCATION.bands) == 100.0


def test_targets_that_do_not_total_one_hundred_refuse_by_name() -> None:
    with pytest.raises(ValueError) as refused:
        StrategicAllocation(
            stocks=band("stocks"),
            etfs=band("etfs"),
            crypto=band("crypto"),
            cash=AllocationBand(
                asset="cash", target_pct=20.0, minimum_pct=15.0, maximum_pct=45.0
            ),
        )

    assert "must total 100%" in str(refused.value)
    assert "95%" in str(refused.value)


def test_a_band_out_of_order_refuses_by_name() -> None:
    with pytest.raises(ValueError) as refused:
        AllocationBand(
            asset="stocks", target_pct=50.0, minimum_pct=25.0, maximum_pct=45.0
        )

    assert "minimum <= target <= maximum" in str(refused.value)


def test_a_band_may_not_contradict_a_hard_limit() -> None:
    with pytest.raises(ValueError) as cash:
        StrategicAllocation(
            stocks=band("stocks"),
            etfs=band("etfs"),
            crypto=band("crypto"),
            cash=AllocationBand(
                asset="cash", target_pct=25.0, minimum_pct=10.0, maximum_pct=45.0
            ),
        )

    assert "hard minimum-cash limit" in str(cash.value)

    with pytest.raises(ValueError) as crypto:
        StrategicAllocation(
            stocks=band("stocks"),
            etfs=band("etfs"),
            crypto=AllocationBand(
                asset="crypto", target_pct=25.0, minimum_pct=15.0, maximum_pct=65.0
            ),
            cash=band("cash"),
        )

    assert "hard maximum-crypto limit" in str(crypto.value)


@pytest.mark.parametrize(
    "field",
    ("target_stocks_pct", "target_etfs_pct", "target_crypto_pct"),
)
def test_a_missing_target_refuses_rather_than_defaulting(tmp_path, field) -> None:
    """Acceptance 2: no numeric defaults, and never a fallback to zeros."""

    document = strategy_document()
    del document["portfolio_policy"][field]

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert f"portfolio_policy.{field}" in reading.refused_because


def test_a_missing_operating_range_refuses(tmp_path) -> None:
    document = strategy_document()
    del document["portfolio_policy"]["crypto_range_pct"]

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "crypto_range_pct" in reading.refused_because
    assert "refuses rather than defaults" in reading.refused_because


def test_a_contradictory_plan_names_the_contradiction(tmp_path) -> None:
    document = strategy_document()
    document["portfolio_policy"]["target_etfs_pct"] = 20

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "must total 100%" in reading.refused_because
    assert "105%" in reading.refused_because


def test_the_live_policy_loads_and_totals_one_hundred(tmp_path) -> None:
    """The tracked strategy is the sole authority, and it validates."""

    document = json.loads(
        (__import__("pathlib").Path("data/investor_strategy.json")).read_text()
    )

    reading = reading_for(tmp_path, document)

    assert reading.policy is not None

    allocation = reading.policy.allocation

    assert sum(b.target_pct for b in allocation.bands) == 100.0
    assert allocation.cash.target_pct == 25.0
    assert allocation.crypto.maximum_pct == 40.0


# ── acceptance 3–5: the target and the floor are different things ───


def test_the_cash_target_and_the_cash_floor_are_distinct() -> None:
    """Acceptance 3, at the value that used to conflate them."""

    live = policy()

    assert live.target_cash_pct == 25.0
    assert live.minimum_cash_pct == HARD_MINIMUM_CASH_PCT
    assert live.cash_floor_pct == HARD_MINIMUM_CASH_PCT
    assert live.cash_floor_pct != live.target_cash_pct


def test_cash_between_the_target_and_the_floor_may_be_deployed() -> None:
    """Acceptance 4: 20% cash is below target and fully deployable."""

    room = capacity(cash=20.0)

    assert room.funding_room_pct == pytest.approx(5.0)
    assert room.capacity_pct == pytest.approx(5.0)

    bounded = envelope("open", cap=room)

    assert bounded.final_pct == pytest.approx(3.0)


def test_deployment_below_the_hard_floor_is_impossible() -> None:
    """Acceptance 5: at or under 15%, funding room is zero."""

    for cash in (15.0, 14.0, 0.0):
        room = capacity(cash=cash)

        assert room.funding_room_pct == 0.0
        assert room.capacity_pct == 0.0


# ── acceptance 6–7: drift authorizes nothing ────────────────────────


def test_crypto_above_target_but_inside_range_is_permitted() -> None:
    """Acceptance 6: 35.63% forces no reduction."""

    reading = guidance_for(band("crypto"), LIVE["crypto"])

    assert reading.standing is AllocationStanding.WITHIN_RANGE
    assert "Above the 25% strategic crypto target" in reading.stated
    assert "No reduction follows" in reading.stated
    assert "REDUCE" not in reading.stated


def test_crypto_above_the_hard_limit_uses_the_reduce_floor_wording() -> None:
    reading = guidance_for(band("crypto"), 45.0)

    assert reading.standing is AllocationStanding.ABOVE_RANGE
    assert f"{HARD_MAXIMUM_CRYPTO_PCT:g}% hard maximum-crypto" in reading.stated
    assert "REDUCE policy floor" in reading.stated
    assert "never a full exit" in reading.stated


def test_no_guidance_sentence_names_a_security_or_a_quantity() -> None:
    """Acceptance 7: allocation drift manufactures no security action."""

    guidance = portfolio_guidance_for(OWNER_ALLOCATION, LIVE)

    sentences = [item.stated for item in guidance.allocations] + [guidance.stated]

    for text in sentences:
        for forbidden in ("DIS", "BNP", "BTC", "shares", "$", "buy ", "sell "):
            assert forbidden not in text, text


# ── the four standings, and the cash and crypto special cases ───────


def test_the_live_account_stands_where_the_ruling_says() -> None:
    guidance = portfolio_guidance_for(OWNER_ALLOCATION, LIVE)

    standings = {item.asset: item.standing for item in guidance.allocations}

    assert standings == {
        "stocks": AllocationStanding.BELOW_RANGE,
        "etfs": AllocationStanding.BELOW_RANGE,
        "crypto": AllocationStanding.WITHIN_RANGE,
        "cash": AllocationStanding.ABOVE_RANGE,
    }


def test_the_portfolio_guidance_says_what_the_ruling_requires() -> None:
    guidance = portfolio_guidance_for(OWNER_ALLOCATION, LIVE)

    stated = guidance.stated

    assert "Stocks and ETFs are below their operating ranges" in stated
    assert "within its permitted range" in stated
    assert "Cash is above its operating range" in stated
    assert "15% hard floor" in stated
    assert "allocation drift alone authorizes no trade" in stated.lower()


def test_cash_below_target_is_permitted_not_non_compliant() -> None:
    reading = guidance_for(band("cash"), 20.0)

    assert reading.standing is AllocationStanding.WITHIN_RANGE
    assert "permitted, not non-compliant" in reading.stated
    assert "destination" in reading.stated


def test_cash_below_the_hard_floor_is_a_breach_with_no_capacity() -> None:
    reading = guidance_for(band("cash"), 12.0)

    assert reading.standing is AllocationStanding.BELOW_RANGE
    assert "hard minimum-cash limit" in reading.stated
    assert "no OPEN or ADD capacity" in reading.stated


def test_an_unmeasured_allocation_refuses_guidance() -> None:
    """Never a substituted zero, and never a difference of zero."""

    reading = guidance_for(band("stocks"), None)

    assert reading.standing is AllocationStanding.UNMEASURED
    assert reading.current_pct is None
    assert reading.difference_pct is None
    assert "could not be read" in reading.stated

    whole = portfolio_guidance_for(
        OWNER_ALLOCATION,
        {"stocks": None, "etfs": None, "crypto": None, "cash": None},
    )

    assert whole.stated == ""
    assert "No allocation could be read" in whole.refused_because


def test_a_standing_carries_its_range_and_its_difference() -> None:
    reading = guidance_for(band("stocks"), LIVE["stocks"])

    assert reading.current_pct == 10.3
    assert reading.target_pct == 35.0
    assert reading.stated_range == "25–45%"
    assert reading.difference_pct == pytest.approx(-24.7)
