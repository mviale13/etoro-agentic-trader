"""One authority for the hard limits, and no plan without a policy.

The owner's amendment to PR #247, in two corrections that share a
shape: **a figure an investor reads must have exactly one author.**

**Correction 1 — the second hard-limit authority.**
`strategic_allocation.py` held `HARD_MINIMUM_CASH_PCT = 15.0` and
`HARD_MAXIMUM_CRYPTO_PCT = 40.0` as module constants while the active
strategy file stated the same two limits, and the Capital Action
Envelope funded against *its* copy. Both agreed on the day it shipped.
One owner edit — `minimum_cash_pct: 20` — and the envelope would fund
to 20% while the CIO's guidance went on quoting 15%, with nothing in
the code able to see the disagreement. The limits now arrive as
`HardLimits` from the same validated `CapitalPolicy` reading the
envelope uses, the operating ranges are validated against *those*, and
a policy whose plan was checked against a different pair refuses by
name rather than picking a side.

**Correction 2 — a refused policy still rendered a plan.**
`CapitalPolicyService` could refuse an allocation totalling 105% while
`InvestmentPolicyMapper` independently mapped those same targets onto
the page. The cycle persisted and displayed a malformed plan and
dropped the refusal entirely. The displayed allocation now rests on the
validated `StrategicAllocation` or on nothing: no target, no range, no
standing, no total and no compliance judgment, with the exact refusal
carried in their place. The account is not erased with the plan — the
holdings and the measured shares are facts about the account, not about
the strategy.
"""

from __future__ import annotations

import ast
import json
import pathlib
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.commands.cycle import _portfolio_weights, _recorded_portfolio
from app.domain.capital_envelope import capacity_for
from app.domain.capital_policy import CapitalPolicy, CapitalPolicyReading
from app.domain.portfolio_position import PortfolioPosition
from app.domain.strategic_allocation import (
    AllocationBand,
    HardLimits,
    StrategicAllocation,
    guidance_for,
    portfolio_guidance_for,
)
from app.infrastructure.evidence.daily_cycle_store import _decode_portfolio
from tests.test_capital_action_envelope import (
    OWNER_ALLOCATION,
    OWNER_LIMITS,
    observed_portfolio,
    policy,
    reading_for,
    strategy_document,
)

MOMENT = datetime(2026, 8, 24, 15, 0, tzinfo=UTC)

#: The live account as the last completed cycle recorded it.
LIVE = {"stocks": 10.3, "etfs": 0.0, "crypto": 35.63, "cash": 54.07}


def moved_policy(**portfolio_policy) -> dict:
    """The tracked strategy with one or more limits edited by the owner."""

    document = strategy_document()
    document["portfolio_policy"].update(portfolio_policy)

    return document


def guidance_of(reading: CapitalPolicyReading, current: dict[str, float]) -> str:
    """Every worded sentence a reading produces, joined for searching."""

    assert reading.policy is not None

    whole = portfolio_guidance_for(reading.policy.allocation, current)

    return " ".join([whole.stated, *(item.stated for item in whole.allocations)])


# ── correction 1: one authority for the hard limits ─────────────────


def test_a_moved_cash_floor_moves_the_guidance_and_the_capacity(tmp_path) -> None:
    """Control 1: cash floor 20%, cash range minimum 20% — both read 20%.

    The whole point of the correction. The guidance quotes the limit
    the envelope funds above, because there is only one of them.
    """

    reading = reading_for(
        tmp_path,
        moved_policy(
            minimum_cash_pct=20,
            cash_range_pct={"minimum": 20, "maximum": 45},
        ),
    )

    assert reading.policy is not None

    # The guidance's figure.
    assert reading.policy.allocation.limits.minimum_cash_pct == 20.0
    assert "20% hard floor" in guidance_of(reading, LIVE)

    # The envelope's figure, and the same one.
    assert reading.policy.cash_floor_pct == 20.0

    room = capacity_for(
        policy=reading.policy,
        total_value=10_000.0,
        cash_pct=30.0,
        current_weight_pct=0.0,
        portfolio=observed_portfolio(),
        broker_answered=True,
    )

    # 30% cash above a 20% floor is 10% of funding room, not 15%.
    assert room.funding_room_pct == pytest.approx(10.0)


def test_a_moved_crypto_maximum_moves_the_guidance_and_the_policy(tmp_path) -> None:
    """Control 2: crypto maximum 30% with a compatible range — both 30%."""

    reading = reading_for(
        tmp_path,
        moved_policy(
            maximum_crypto_pct=30,
            crypto_range_pct={"minimum": 15, "maximum": 30},
        ),
    )

    assert reading.policy is not None
    assert reading.policy.max_crypto_pct == 30.0
    assert reading.policy.allocation.limits.maximum_crypto_pct == 30.0

    breach = guidance_for(
        reading.policy.allocation.crypto,
        35.0,
        reading.policy.allocation.limits,
    )

    assert "30% hard maximum-crypto" in breach.stated
    assert "40%" not in breach.stated


def test_a_cash_range_below_the_active_floor_refuses(tmp_path) -> None:
    """Control 3: range minimum 15% beside a 20% hard floor.

    It refuses by name. It does not quietly raise the range to 20, nor
    quietly lower the floor to 15 — either choice would be this
    platform editing the investor's plan.
    """

    reading = reading_for(tmp_path, moved_policy(minimum_cash_pct=20))

    assert reading.policy is None
    assert "cash range's minimum (15%)" in reading.refused_because
    assert "20% hard minimum-cash limit" in reading.refused_because


def test_a_crypto_range_above_the_active_maximum_refuses(tmp_path) -> None:
    """Control 4: range maximum 40% beside a 30% hard maximum."""

    reading = reading_for(tmp_path, moved_policy(maximum_crypto_pct=30))

    assert reading.policy is None
    assert "crypto range's maximum (40%)" in reading.refused_because
    assert "30% hard maximum-crypto limit" in reading.refused_because


def test_the_allocation_module_holds_no_hard_limit_of_its_own() -> None:
    """Control 5, at the source: no 15 and no 40 anywhere in the module.

    A named constant would be reachable by a future reader; that is
    exactly what made the second authority survivable. The numbers are
    simply not here — they arrive with the policy or not at all.
    """

    module = pathlib.Path("app/domain/strategic_allocation.py")
    tree = ast.parse(module.read_text(encoding="utf-8"))

    literals = sorted(
        {
            float(node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, int | float)
        }
    )

    assert 15.0 not in literals, "a cash floor is stated here again"
    assert 40.0 not in literals, "a crypto maximum is stated here again"

    source = module.read_text(encoding="utf-8")

    assert "HARD_MINIMUM_CASH_PCT" not in source
    assert "HARD_MAXIMUM_CRYPTO_PCT" not in source


def test_a_hard_limit_cannot_be_omitted_or_defaulted() -> None:
    """Control 5, at the type: no production path can reach a default.

    `limits` has no default value, so there is no construction of a
    `StrategicAllocation` that silently invents one.
    """

    with pytest.raises(TypeError):
        StrategicAllocation(  # type: ignore[call-arg]
            stocks=OWNER_ALLOCATION.stocks,
            etfs=OWNER_ALLOCATION.etfs,
            crypto=OWNER_ALLOCATION.crypto,
            cash=OWNER_ALLOCATION.cash,
        )

    with pytest.raises(TypeError):
        HardLimits()  # type: ignore[call-arg]

    with pytest.raises(TypeError):
        guidance_for(OWNER_ALLOCATION.cash, 20.0)  # type: ignore[call-arg]


def test_a_policy_whose_plan_used_another_limit_refuses_by_name() -> None:
    """The two authorities cannot be reintroduced by a caller either.

    A `CapitalPolicy` funding above 40% cash while its allocation was
    validated against a 15% floor is the exact disagreement this
    amendment removes, and it cannot be constructed.
    """

    with pytest.raises(ValueError) as refused:
        policy(minimum_cash_pct=40.0, target_cash_pct=45.0)

    assert "validated against a different hard limit" in str(refused.value)
    assert "40%" in str(refused.value)
    assert "15%" in str(refused.value)


def test_the_live_policy_states_the_limits_the_owner_ruled() -> None:
    """The tracked strategy, unchanged by the amendment."""

    document = json.loads(pathlib.Path("data/investor_strategy.json").read_text())
    reading = reading_for(pathlib.Path("/tmp"), document)

    assert reading.policy is not None

    limits = reading.policy.hard_limits

    assert limits.minimum_cash_pct == 15.0
    assert limits.maximum_crypto_pct == 40.0
    assert reading.policy.allocation.limits == limits
    assert reading.policy.max_single_position_pct == 20.0

    # And the target is still not the floor.
    assert reading.policy.target_cash_pct == 25.0
    assert reading.policy.cash_floor_pct == 15.0


def test_crypto_at_the_live_share_still_causes_no_reduction() -> None:
    """Preserved: 35.6% is inside the range and forces nothing."""

    reading = guidance_for(OWNER_ALLOCATION.crypto, LIVE["crypto"], OWNER_LIMITS)

    assert "No reduction follows" in reading.stated
    assert "hard maximum-crypto" not in reading.stated


# ── correction 2: no plan is shown without a validated policy ───────


def brain(*, policy_loaded: bool = True):
    """The brain shape `_recorded_portfolio` reads, at the real contract."""

    return SimpleNamespace(
        portfolio=SimpleNamespace(
            total_value=10_000.0,
            holdings=(
                PortfolioPosition(
                    symbol="KO",
                    quantity=1.0,
                    invested_usd=1_030.0,
                    market_value_usd=1_030.0,
                    unrealized_pnl_usd=0.0,
                    asset_class=None,
                    instrument_id=1,
                ),
                PortfolioPosition(
                    symbol="BTC",
                    quantity=1.0,
                    invested_usd=3_563.0,
                    market_value_usd=3_563.0,
                    unrealized_pnl_usd=0.0,
                    asset_class=None,
                    instrument_id=2,
                ),
            ),
            allocation=SimpleNamespace(**LIVE),
            available_cash_usd=5_407.0,
            last_sync=None,
        ),
        # The independently mapped policy. Present on both paths, so a
        # refusal that still rendered a plan would show up here.
        investment_policy=(_mapped_policy() if policy_loaded else None),
    )


def _mapped_policy():
    from app.services.investment_policy_mapper import InvestmentPolicyMapper

    return InvestmentPolicyMapper().map(strategy_document())


def recorded(reading: CapitalPolicyReading, *, policy_loaded: bool = True):
    stub = brain(policy_loaded=policy_loaded)
    weights, cash_pct, total_value = _portfolio_weights(stub)

    return _recorded_portfolio(
        stub, weights, cash_pct, total_value, policy_reading=reading
    )


def contradictory(tmp_path) -> CapitalPolicyReading:
    """Targets totalling 105% — the owner's own example."""

    document = strategy_document()
    document["portfolio_policy"]["target_etfs_pct"] = 20

    return reading_for(tmp_path, document)


def test_targets_totalling_105_render_a_refusal_and_no_target_table(
    tmp_path,
) -> None:
    """Production control 1, at the record the page renders from."""

    reading = contradictory(tmp_path)

    assert reading.policy is None
    assert "105%" in reading.refused_because

    portfolio = recorded(reading)

    assert portfolio is not None

    # The refusal is persisted, exactly as the policy worded it.
    assert portfolio.allocation_policy_refused == reading.refused_because
    assert "105%" in portfolio.allocation_policy_refused

    # And no plan survives anywhere in the record: no target, no range,
    # no standing, no guidance. The mapper's 105% reaches nothing.
    for item in portfolio.allocations:
        assert item.target_pct is None
        assert item.difference_pct is None
        assert item.minimum_pct is None
        assert item.maximum_pct is None
        assert item.standing == ""
        assert item.stated == ""

    assert portfolio.allocation_guidance == ""
    assert portfolio.allocation_guidance_refused == ""


def test_a_missing_operating_range_refuses_and_guesses_no_range(tmp_path) -> None:
    """Production control 2."""

    document = strategy_document()
    del document["portfolio_policy"]["crypto_range_pct"]

    reading = reading_for(tmp_path, document)
    portfolio = recorded(reading)

    assert portfolio is not None
    assert "crypto_range_pct" in portfolio.allocation_policy_refused
    assert "refuses rather than defaults" in portfolio.allocation_policy_refused

    assert all(item.minimum_pct is None for item in portfolio.allocations)
    assert all(item.maximum_pct is None for item in portfolio.allocations)


def test_no_compliance_judgment_is_emitted_under_a_refused_policy(
    tmp_path,
) -> None:
    """Production control 3.

    `InvestmentPolicyMapper` is loaded and would happily answer. It is
    not asked: compliance is a judgment against a plan, and there is
    no validated plan to judge against.
    """

    portfolio = recorded(contradictory(tmp_path), policy_loaded=True)

    assert portfolio is not None
    assert portfolio.compliant is None


def test_a_refused_policy_does_not_erase_the_account(tmp_path) -> None:
    """The holdings and the measured shares are the account's own facts."""

    portfolio = recorded(contradictory(tmp_path))

    assert portfolio is not None

    assert [holding.symbol for holding in portfolio.holdings] == ["BTC", "KO"]
    assert portfolio.total_value == 10_000.0
    assert portfolio.cash_pct == 54.07

    measured = {item.asset: item.current_pct for item in portfolio.allocations}

    assert measured == LIVE


def test_a_refused_policy_never_produces_a_total_of_zero(tmp_path) -> None:
    """Production control: no misleading "Total 0%".

    Every target is absent rather than zero, so nothing downstream can
    sum four zeros into a plan totalling 0%.
    """

    portfolio = recorded(contradictory(tmp_path))

    assert portfolio is not None

    targets = [item.target_pct for item in portfolio.allocations]

    assert targets == [None, None, None, None]
    assert 0.0 not in targets


def test_the_valid_policy_renders_the_owners_own_four_targets(tmp_path) -> None:
    """Production control 4 and the proof the brief asks for.

    The table's four targets are **exactly** those of the validated
    `StrategicAllocation` — the same object the envelope funds from and
    the guidance is worded from, not a second reading of the same file.
    """

    reading = reading_for(tmp_path, strategy_document())

    assert reading.policy is not None

    allocation = reading.policy.allocation
    portfolio = recorded(reading)

    assert portfolio is not None

    for item in portfolio.allocations:
        band = allocation.band(item.asset)

        assert band is not None
        assert item.target_pct == band.target_pct
        assert item.minimum_pct == band.minimum_pct
        assert item.maximum_pct == band.maximum_pct

    assert [item.asset for item in portfolio.allocations] == [
        "stocks",
        "etfs",
        "crypto",
        "cash",
    ]
    assert [item.target_pct for item in portfolio.allocations] == [
        35.0,
        15.0,
        25.0,
        25.0,
    ]
    assert sum(item.target_pct or 0.0 for item in portfolio.allocations) == 100.0

    assert portfolio.allocation_policy_refused == ""


def test_the_valid_policy_renders_as_it_was_rehearsed(tmp_path) -> None:
    """Production control 4: the live standings and wording are unmoved."""

    portfolio = recorded(reading_for(tmp_path, strategy_document()))

    assert portfolio is not None

    standings = {item.asset: item.standing for item in portfolio.allocations}

    assert standings == {
        "stocks": "below_range",
        "etfs": "below_range",
        "crypto": "within_range",
        "cash": "above_range",
    }

    stated = portfolio.allocation_guidance

    assert "Stocks and ETFs are below their operating ranges" in stated
    assert "within its permitted range" in stated
    assert "Cash is above its operating range" in stated
    assert "15% hard floor" in stated
    assert "allocation drift alone authorizes no trade" in stated.lower()

    # The measured shares and the differences are unchanged.
    assert {item.asset: item.current_pct for item in portfolio.allocations} == LIVE
    assert [item.difference_pct for item in portfolio.allocations] == [
        pytest.approx(-24.7),
        pytest.approx(-15.0),
        pytest.approx(10.63),
        pytest.approx(29.07),
    ]

    # And a compliance judgment is emitted, because there is a plan.
    assert portfolio.compliant is False


def test_a_historical_pre_range_record_decodes_unchanged() -> None:
    """Production control 5: nothing stored is rewritten or reinterpreted.

    A line written before the operating ranges — and before this
    amendment — carries a numeric `target_pct` and no
    `allocation_policy_refused`. It decodes to exactly that target, no
    range, no standing and no refusal: a record that predates a field
    is not a record that refused something.
    """

    stored = {
        "total_value": 10_000.0,
        "available_cash_usd": 5_407.0,
        "cash_pct": 54.07,
        "observed": "eToro account response received at 2026-08-20 20:59 UTC",
        "compliant": False,
        "holdings": [
            {"symbol": "BTC", "market_value_usd": 3_563.0, "weight_pct": 35.63}
        ],
        "allocations": [
            {
                "asset": "cash",
                "current_pct": 54.07,
                "target_pct": 5.0,
                "difference_pct": 49.07,
            }
        ],
    }

    portfolio = _decode_portfolio(stored)

    assert portfolio is not None
    assert portfolio.allocation_policy_refused == ""
    assert portfolio.compliant is False

    (allocation,) = portfolio.allocations

    assert allocation.target_pct == 5.0
    assert allocation.difference_pct == 49.07
    assert allocation.minimum_pct is None
    assert allocation.maximum_pct is None
    assert allocation.standing == ""


def test_a_refused_record_round_trips_through_the_store(tmp_path) -> None:
    """The refusal and the absent targets survive encode and decode."""

    from app.infrastructure.evidence.daily_cycle_store import _encode_portfolio

    portfolio = recorded(contradictory(tmp_path))

    assert portfolio is not None

    decoded = _decode_portfolio(_encode_portfolio(portfolio))

    assert decoded == portfolio
    assert decoded is not None
    assert "105%" in decoded.allocation_policy_refused
    assert all(item.target_pct is None for item in decoded.allocations)


def test_the_mapper_is_not_consulted_for_the_displayed_plan(tmp_path) -> None:
    """The structural guarantee, not the behavioural one.

    With the allocation policy refused, `PolicyAnalyzer` is made to
    raise. The record still builds — which is only possible if no
    displayed figure comes through the independently mapped policy.
    """

    import app.commands.cycle as cycle_module

    class Poisoned:
        def analyze(self, *args, **kwargs):  # pragma: no cover - must not run
            raise AssertionError(
                "the mapped InvestmentPolicy was consulted under a refused "
                "allocation policy"
            )

    original = cycle_module.PolicyAnalyzer
    cycle_module.PolicyAnalyzer = Poisoned  # type: ignore[misc]

    try:
        portfolio = recorded(contradictory(tmp_path), policy_loaded=True)
    finally:
        cycle_module.PolicyAnalyzer = original  # type: ignore[misc]

    assert portfolio is not None
    assert portfolio.compliant is None
    assert "105%" in portfolio.allocation_policy_refused


def test_the_two_refusals_are_different_facts(tmp_path) -> None:
    """A policy that cannot be read is not an account that cannot be read.

    `allocation_guidance_refused` says no allocation could be measured;
    `allocation_policy_refused` says there is no plan to measure
    against. Collapsing them would make an unreadable strategy look
    like an unreadable account.
    """

    unreadable_account = SimpleNamespace(
        portfolio=SimpleNamespace(
            total_value=10_000.0,
            holdings=(),
            allocation=SimpleNamespace(stocks=None, etfs=None, crypto=None, cash=None),
            available_cash_usd=None,
            last_sync=None,
        ),
        investment_policy=_mapped_policy(),
    )

    weights, cash_pct, total_value = _portfolio_weights(unreadable_account)

    portfolio = _recorded_portfolio(
        unreadable_account,
        weights,
        cash_pct,
        total_value,
        policy_reading=reading_for(tmp_path, strategy_document()),
    )

    assert portfolio is not None
    assert portfolio.allocation_policy_refused == ""
    assert "No allocation could be read" in portfolio.allocation_guidance_refused
    assert portfolio.allocation_guidance == ""


def test_no_order_or_broker_write_is_reachable_from_this_layer() -> None:
    """Allocation drift authorizes nothing, at the import graph.

    A standing is a description of the account's shape. The module that
    produces one imports nothing at all beyond the standard library, so
    it cannot reach a broker, an order, a course or a conviction — the
    guarantee is structural rather than a promise in a docstring.
    """

    tree = ast.parse(
        pathlib.Path("app/domain/strategic_allocation.py").read_text(encoding="utf-8")
    )

    imported: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert sorted(imported) == ["__future__", "dataclasses", "enum", "math"]


def test_the_capital_policy_still_hashes_the_same_decision_bearing_set() -> None:
    """The amendment moved no decision-bearing value.

    `allocation` is not in `DECISION_BEARING_FIELDS` and neither is
    `hard_limits` — the limits are already hashed as
    `minimum_cash_pct` and `max_crypto_pct`, which is what makes them
    one authority rather than two.
    """

    from app.domain.capital_policy import DECISION_BEARING_FIELDS

    assert "allocation" not in DECISION_BEARING_FIELDS
    assert "hard_limits" not in DECISION_BEARING_FIELDS
    assert "minimum_cash_pct" in DECISION_BEARING_FIELDS
    assert "max_crypto_pct" in DECISION_BEARING_FIELDS

    live: CapitalPolicy = policy()

    assert live.version == policy(allocation=OWNER_ALLOCATION).version


def test_a_band_may_be_built_against_any_stated_limit() -> None:
    """The domain has no opinion about which numbers the owner picks.

    A 5% floor and a 90% crypto ceiling are a policy this platform
    would not recommend and *would* faithfully report. What it may not
    do is quietly substitute its own.
    """

    permissive = HardLimits(minimum_cash_pct=5.0, maximum_crypto_pct=90.0)

    allocation = StrategicAllocation(
        stocks=AllocationBand(
            asset="stocks", target_pct=10.0, minimum_pct=0.0, maximum_pct=20.0
        ),
        etfs=AllocationBand(
            asset="etfs", target_pct=5.0, minimum_pct=0.0, maximum_pct=10.0
        ),
        crypto=AllocationBand(
            asset="crypto", target_pct=75.0, minimum_pct=50.0, maximum_pct=90.0
        ),
        cash=AllocationBand(
            asset="cash", target_pct=10.0, minimum_pct=5.0, maximum_pct=20.0
        ),
        limits=permissive,
    )

    breach = guidance_for(allocation.cash, 4.0, permissive)

    assert "Below the 5% hard minimum-cash limit" in breach.stated
    assert "15%" not in breach.stated
