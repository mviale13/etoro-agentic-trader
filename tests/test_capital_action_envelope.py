"""The Capital Action Envelope v1: policy, capacity, ceilings, honesty.

Display-only, normalized, deterministic. Every case below pins one of
the owner's acceptance requirements: a policy that refuses rather than
defaults, capacity that never mistakes a broker outage for an empty
account, ceilings that only preserve or reduce, wording that never
turns a floor into a target — and byte-identical decisions beneath it
all, because the envelope consumes the pipeline's outputs and touches
none of its inputs.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.capital_envelope import (
    LIQUIDITY_UNMEASURED,
    CapitalActionEnvelope,
    EnvelopeKind,
    PortfolioObservation,
    PriceObservation,
    QualityAuthority,
    capacity_for,
    envelope_for,
    portfolio_observation_for,
    price_observation_for,
)
from app.domain.capital_policy import (
    CapitalPolicy,
    CapitalPolicyReading,
    ReducePolicy,
)
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from app.services.capital_policy_service import CapitalPolicyService

MOMENT = datetime(2026, 8, 19, 15, 0, tzinfo=UTC)


def policy(**overrides) -> CapitalPolicy:
    values = dict(
        starter_max_total_position_pct=1.0,
        standard_initial_position_pct=3.0,
        max_add_weight_change_pct=2.0,
        max_single_position_pct=20.0,
        max_crypto_pct=65.0,
        target_cash_pct=5.0,
        minimum_cash_pct=40.0,
        price_max_age_minutes=15.0,
        portfolio_max_age_minutes=15.0,
        maximum_acceptable_drawdown_pct=20.0,
        reduce_policy=ReducePolicy.RESTORE_TO_POLICY_CAP,
        source="investor_strategy.json",
        version="testversion1",
    )
    values.update(overrides)

    return CapitalPolicy(**values)


def strategy_document(**overrides) -> dict:
    document = {
        "status": "active",
        "objectives": {"maximum_acceptable_drawdown_pct": 20},
        "portfolio_policy": {
            "target_cash_pct": 5,
            "minimum_cash_pct": 40,
            "maximum_single_position_pct": 20,
            "maximum_crypto_pct": 65,
        },
        "capital_envelope": {
            "starter_max_total_position_pct": 1.0,
            "standard_initial_position_pct": 3.0,
            "max_add_weight_change_pct": 2.0,
            "price_max_age_minutes": 15,
            "portfolio_max_age_minutes": 15,
            "reduce_policy": "restore_to_policy_cap",
        },
        "decision_rules": {
            "require_human_approval": True,
            "automatic_trading_enabled": False,
        },
    }
    document.update(overrides)

    return document


def reading_for(tmp_path, document: dict) -> CapitalPolicyReading:
    path = tmp_path / "investor_strategy.json"
    path.write_text(json.dumps(document))

    return CapitalPolicyService(path).reading()


def observed_portfolio(*, minutes_old: float = 2.0) -> PortfolioObservation:
    """A broker snapshot aged through the real factory."""

    return portfolio_observation_for(
        last_sync=MOMENT - timedelta(minutes=minutes_old),
        policy=policy(),
        now=MOMENT,
    )


def quote_for(
    symbol: str = "KO",
    *,
    minutes_old: float = 2.0,
    price: float = 61.0,
    last_known: bool = False,
    dated: bool = True,
) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        name=symbol,
        price=price,
        change_percent=0.0,
        reading=(
            Provenance(
                source="Yahoo Finance",
                observed_at=MOMENT - timedelta(minutes=minutes_old),
                last_known=last_known,
            )
            if dated
            else None
        ),
    )


def observed_price(*, fresh: bool = True, symbol: str = "KO") -> PriceObservation:
    """The exact quote's own verdict, through the real factory."""

    return price_observation_for(
        symbol=symbol,
        quote=quote_for(symbol, minutes_old=2.0 if fresh else 40.0),
        policy=policy(),
        now=MOMENT,
    )


def capacity(
    *,
    cash: float = 58.0,
    weight: float | None = 0.0,
    fresh: bool = True,
    answered: bool = True,
    total: float | None = 10_000.0,
):
    return capacity_for(
        policy=policy(),
        total_value=total,
        cash_pct=cash,
        current_weight_pct=weight,
        portfolio=observed_portfolio(minutes_old=2.0 if fresh else 20.0),
        broker_answered=answered,
    )


def envelope(
    course: str = "open",
    *,
    cap=None,
    gaps: tuple[str, ...] = (),
    authority: QualityAuthority = QualityAuthority.GROUNDED,
    floor: bool = True,
    price_fresh: bool = True,
    drawdown: float | None = 2.0,
    equity: bool = True,
    the_policy: CapitalPolicy | None = None,
) -> CapitalActionEnvelope:
    return envelope_for(
        symbol="KO",
        course=course,
        policy=the_policy or policy(),
        capacity=cap if cap is not None else capacity(),
        named_gaps=gaps,
        quality_authority=authority,
        hard_floor_passes=floor,
        price=observed_price(fresh=price_fresh),
        portfolio_as_of=("eToro account response received at 2026-08-19 14:58 UTC"),
        drawdown_depth_pct=drawdown,
        is_equity=equity,
    )


# ── 1–5: the policy contract ────────────────────────────────────────


def test_1_draft_strategy_refuses_the_final_envelope(tmp_path) -> None:
    reading = reading_for(tmp_path, strategy_document(status="draft"))

    assert reading.policy is None
    assert "draft" in reading.refused_because
    assert "cannot authorize" in reading.refused_because

    # Capacity stays computable beside the refusal — the raw facts are
    # not hostage to the policy's status.
    room = capacity()

    assert room.capacity_pct is not None


def test_2_a_missing_sizing_field_refuses_with_no_default(tmp_path) -> None:
    document = strategy_document()
    del document["capital_envelope"]["starter_max_total_position_pct"]

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "starter_max_total_position_pct" in reading.refused_because
    assert "refuses rather than defaults" in reading.refused_because


def test_3_an_invalid_policy_relationship_refuses(tmp_path) -> None:
    document = strategy_document()
    document["capital_envelope"]["starter_max_total_position_pct"] = 5.0  # > standard

    reading = reading_for(tmp_path, document)

    assert reading.policy is None
    assert "STARTER <= STANDARD_INITIAL" in reading.refused_because


def test_4_the_policy_hash_is_stable_and_moves_on_decision_bearing_change(
    tmp_path,
) -> None:
    first = reading_for(tmp_path, strategy_document())
    second = reading_for(tmp_path, strategy_document())

    assert first.policy is not None and second.policy is not None
    assert first.policy.version == second.policy.version

    changed_doc = strategy_document()
    changed_doc["capital_envelope"]["max_add_weight_change_pct"] = 1.5
    changed = reading_for(tmp_path, changed_doc)

    assert changed.policy is not None
    assert changed.policy.version != first.policy.version

    # A cosmetic edit moves nothing.
    cosmetic_doc = strategy_document()
    cosmetic_doc["notes"] = ["reworded"]
    cosmetic = reading_for(tmp_path, cosmetic_doc)

    assert cosmetic.policy is not None
    assert cosmetic.policy.version == first.policy.version


def test_5_the_envelope_reads_neither_legacy_policy_source() -> None:
    """No import of config/policy.yaml's loader or app/config.py."""

    import ast
    import pathlib

    for module in (
        "app/domain/capital_policy.py",
        "app/domain/capital_envelope.py",
        "app/services/capital_policy_service.py",
    ):
        tree = ast.parse(pathlib.Path(module).read_text())

        imports = [
            name.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for name in node.names
        ] + [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]

        for imported in imports:
            assert "app.config" not in imported, module
            assert "policy_service" not in imported, module

        # Executed strings only: the module's own prose may NAME the
        # inadmissible sources in order to refuse them — the recorded
        # lesson about literals against whole source files, applied.
        docstrings = {
            doc
            for node in ast.walk(tree)
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            )
            for doc in (ast.get_docstring(node, clean=False),)
            if doc is not None
        }
        executed = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value not in docstrings
        ]

        for text in executed:
            assert "policy.yaml" not in text, module


# ── 6–8: capacity honesty ───────────────────────────────────────────


def test_6_split_broker_rows_aggregate_by_instrument_identity() -> None:
    from types import SimpleNamespace

    from app.commands.cycle import _portfolio_weights

    brain = SimpleNamespace(
        portfolio=SimpleNamespace(
            total_value=10_000.0,
            allocation=SimpleNamespace(cash=50.0),
            holdings=(
                SimpleNamespace(
                    instrument_id=7,
                    symbol="KO",
                    market_value_usd=2_000.0,
                    is_resolved=True,
                ),
                SimpleNamespace(
                    instrument_id=7,
                    symbol="KO",
                    market_value_usd=50.0,
                    is_resolved=True,
                ),
            ),
        )
    )

    weights, cash, total = _portfolio_weights(brain)

    assert weights["KO"] == pytest.approx(20.5)
    assert cash == 50.0 and total == 10_000.0


def test_7_a_broker_that_did_not_answer_is_not_an_empty_account() -> None:
    refused = capacity(answered=False, total=None)

    assert refused.capacity_pct is None
    assert "unanswered account is not an empty one" in refused.refused_because

    unusable = capacity(total=0.0)

    assert unusable.capacity_pct is None
    assert "unavailable or non-positive" in unusable.refused_because


def test_8_the_cash_floor_is_the_stricter_of_the_two_cash_statements() -> None:
    assert policy().cash_floor_pct == 40.0

    # cash 58% − floor 40% = 18% funding room; concentration room 20%.
    room = capacity()

    assert room.funding_room_pct == pytest.approx(18.0)
    assert room.concentration_room_pct == pytest.approx(20.0)
    assert room.capacity_pct == pytest.approx(18.0)
    assert "cash floor" in room.binding


# ── 9–14: the ceilings ──────────────────────────────────────────────


def test_9_broad_unheld_open_is_capped_at_standard_never_capacity() -> None:
    result = envelope("open")

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 3.0, "never the 18% capacity or the 20% cap"
    assert result.evidence_ceiling == "standard_initial"
    assert "3%" in result.stated


def test_10_limited_unheld_open_is_capped_at_starter() -> None:
    result = envelope("open", gaps=("the earnings calendar could not be read",))

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 1.0
    assert result.starter_capped
    assert "1%" in result.stated
    assert "not the company's quality" in result.stated


def test_11_limited_held_at_a_fraction_adds_only_the_room_to_starter() -> None:
    result = envelope(
        "add",
        cap=capacity(weight=0.4),
        authority=QualityAuthority.PROVIDER,
    )

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == pytest.approx(0.6)


def test_12_limited_held_at_or_above_starter_has_zero_add_room() -> None:
    result = envelope(
        "add",
        cap=capacity(weight=1.0),
        gaps=("a gap",),
    )

    assert result.kind is EnvelopeKind.ZERO_CAPACITY
    assert result.final_pct is None
    assert "STARTER" in result.binding_constraint


def test_13_broad_add_is_capped_at_the_change_limit() -> None:
    result = envelope("add", cap=capacity(weight=4.0))

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == 2.0, "capacity is 16%; the change limit binds"
    assert result.evidence_ceiling == "max_add_change"


def test_14_near_the_concentration_cap_only_the_remaining_room_exists() -> None:
    result = envelope("add", cap=capacity(weight=19.2))

    assert result.kind is EnvelopeKind.UPWARD_BOUNDED
    assert result.final_pct == pytest.approx(0.8)
    assert "concentration" in result.binding_constraint


# ── 15–20: refusal floors ───────────────────────────────────────────


def test_15_a_hard_floor_failure_is_none(subtests=None) -> None:
    result = envelope("open", floor=False)

    assert result.kind is EnvelopeKind.REFUSED
    assert "hard safety prerequisite" in result.because
    assert "non-capital course remains unchanged" in result.stated


def test_16_a_stale_price_is_none() -> None:
    result = envelope("open", price_fresh=False)

    assert result.kind is EnvelopeKind.REFUSED
    assert "15-minute limit" in result.because


def test_17_a_stale_portfolio_is_none() -> None:
    result = envelope("open", cap=capacity(fresh=False))

    assert result.kind is EnvelopeKind.REFUSED
    assert "longer ago than the policy's 15-minute limit" in result.because


def test_18_missing_drawdown_refuses_open_and_add() -> None:
    for course in ("open", "add"):
        result = envelope(course, drawdown=None)

        assert result.kind is EnvelopeKind.REFUSED
        assert "cannot be evaluated" in result.because


def test_19_drawdown_at_the_budget_refuses_open_and_add() -> None:
    for course in ("open", "add"):
        result = envelope(course, drawdown=20.0)

        assert result.kind is EnvelopeKind.REFUSED
        assert "drawdown budget" in result.because


def test_20_reduce_remains_available_during_drawdown() -> None:
    result = envelope("reduce", cap=capacity(weight=24.0), drawdown=35.0)

    assert result.kind is EnvelopeKind.REDUCTION_FLOOR
    assert result.final_pct == pytest.approx(4.0)


# ── 21–23: reduce semantics and the crypto boundary ─────────────────


def test_21_an_overweight_holding_gets_an_at_least_floor() -> None:
    result = envelope("reduce", cap=capacity(weight=24.0))

    assert result.kind is EnvelopeKind.REDUCTION_FLOOR
    assert result.final_pct == pytest.approx(4.0)
    assert result.stated.startswith("At least 4%")
    assert "not a target or exit recommendation" in result.stated


def test_22_a_non_overweight_reduce_invents_no_magnitude() -> None:
    result = envelope("reduce", cap=capacity(weight=12.0))

    assert result.kind is EnvelopeKind.NO_POLICY_MAGNITUDE
    assert result.final_pct is None
    assert "no policy-derived reduction magnitude" in result.stated


def test_23_crypto_is_refused_by_this_contract() -> None:
    result = envelope("open", equity=False)

    assert result.kind is EnvelopeKind.REFUSED
    assert "crypto remains outside the equity capital envelope" in result.because


# ── 24–28: what cannot move the envelope ────────────────────────────


def test_24_conviction_is_not_an_input_and_cannot_alter_anything() -> None:
    """Structural: the function has no parameter conviction could enter by."""

    import inspect

    parameters = inspect.signature(envelope_for).parameters

    assert "conviction" not in parameters
    assert not any("confidence" in name for name in parameters)


def test_25_missing_evidence_only_preserves_or_reduces() -> None:
    broad = envelope("open")
    limited = envelope("open", gaps=("one named gap",))

    assert limited.final_pct is not None and broad.final_pct is not None
    assert limited.final_pct <= broad.final_pct

    more_limited = envelope(
        "open", gaps=("one named gap", "another"), authority=QualityAuthority.PROVIDER
    )

    assert more_limited.final_pct is not None
    assert more_limited.final_pct <= limited.final_pct


def test_26_provider_quality_authority_caps_at_starter() -> None:
    result = envelope("open", authority=QualityAuthority.PROVIDER)

    assert result.starter_capped
    assert result.final_pct == 1.0

    unavailable = envelope("open", authority=QualityAuthority.UNAVAILABLE)

    assert unavailable.starter_capped
    assert unavailable.final_pct == 1.0


def test_27_grounded_gap_free_evidence_may_use_standard() -> None:
    result = envelope("open", authority=QualityAuthority.GROUNDED, gaps=())

    assert not result.starter_capped
    assert result.evidence_ceiling == "standard_initial"


def test_28_liquidity_is_unmeasured_and_never_adequate() -> None:
    result = envelope("open")

    assert result.liquidity == LIQUIDITY_UNMEASURED
    assert "unmeasured" in result.liquidity
    assert "adequate" not in result.stated

    # And the disclosure never claims adequacy in its own words.
    assert "nothing here describes it as adequate" in result.liquidity


# ── 29–32: neutrality, persistence, boundaries ──────────────────────


def test_29_the_envelope_touches_no_decision_input() -> None:
    """The pipeline's modules import nothing from the envelope's.

    Decisions, actions, conviction and rationales are identical for
    identical inputs because the envelope consumes workspace outputs
    only — pinned here on the import graph, and by the full suite's
    untouched decision controls.
    """

    import ast
    import pathlib

    decision_modules = [
        "app/cio/artificial_cio.py",
        "app/application/executive/decision_evidence_builder.py",
        "app/application/executive/executive_action_builder.py",
        "app/application/workspace/executive_pipeline.py",
        "app/services/quality_signal_service.py",
        "app/services/company_committee_service.py",
    ]

    for module in decision_modules:
        source = pathlib.Path(module).read_text()

        assert "capital_envelope" not in source, module
        assert "capital_policy" not in source, module

    tree = ast.parse(pathlib.Path("app/domain/capital_envelope.py").read_text())
    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    for imported in imports:
        assert "cio" not in imported and "executive" not in imported


def test_30_no_order_trade_or_currency_path_exists() -> None:
    import pathlib

    for module in (
        "app/domain/capital_policy.py",
        "app/domain/capital_envelope.py",
        "app/services/capital_policy_service.py",
    ):
        source = pathlib.Path(module).read_text().casefold()

        for banned in ("place_order", "submit", "usd amount", "$", "quantity"):
            assert banned not in source, (module, banned)


def test_31_cycle_records_round_trip_and_old_records_still_decode(
    tmp_path,
) -> None:
    from app.domain.daily_cycle import (
        ComparisonBasis,
        ComparisonOutcome,
        CycleFinished,
        CycleStage,
        CycleStarted,
        CycleStatus,
        DecisionSummary,
        StageOutcome,
    )
    from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

    store = DailyCycleStore(tmp_path / "cycles")

    with_envelope = DecisionSummary(
        symbol="KO",
        state="RECOMMEND",
        rationale="r",
        action_kind="open",
        action_statement="Consider opening a position.",
        asks_for_something=True,
        envelope=envelope("open"),
    )
    without = DecisionSummary(
        symbol="PG", state="PREPARE", rationale="r", action_kind="wait"
    )

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        CycleFinished(
            cycle_id="c1",
            finished_at=MOMENT,
            status=CycleStatus.COMPLETE,
            stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
            comparison=ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
            decisions=(with_envelope, without),
        )
    )

    log = store.log()

    assert log.is_complete_stream, "the new fields live under the same schema"

    decoded = log.records[0].finished

    assert decoded is not None
    assert decoded.decisions[0] == with_envelope, "exact round-trip"
    assert decoded.decisions[1].envelope is None, (
        "a record without an envelope decodes exactly as before"
    )


def test_32_personal_news_and_sentiment_stay_outside_the_envelope() -> None:
    import pathlib

    for module in (
        "app/domain/capital_envelope.py",
        "app/services/capital_policy_service.py",
        "app/commands/cycle.py",
    ):
        source = pathlib.Path(module).read_text().casefold()

        assert "personal_news" not in source, module
        assert "sentiment" not in source, module


# ── 33: one policy location ─────────────────────────────────────────


def test_33_the_policy_source_is_tracked_configuration_not_evidence(
    monkeypatch, tmp_path
) -> None:
    """Redirecting MOVRVEST_EVIDENCE_ROOT must not redirect the policy.

    The strategy file is tracked configuration (the recorded exemption
    in test_evidence_root_invariant), so the capital policy reads the
    same physical document InvestorStrategyService addresses — and an
    isolated evidence root still resolves the owner's live policy.
    """

    import ast
    import pathlib

    from app.infrastructure.evidence_root import ROOT_ENV
    from app.services.investor_strategy_service import (
        STRATEGY_PATH,
        InvestorStrategyService,
    )

    monkeypatch.setenv(ROOT_ENV, str(tmp_path))

    assert CapitalPolicyService()._path == STRATEGY_PATH
    assert InvestorStrategyService()._path == STRATEGY_PATH
    assert CapitalPolicyService()._path == InvestorStrategyService()._path

    live = CapitalPolicyService().reading()

    assert live.policy is not None, (
        "the live tracked strategy is active and readable under a "
        "redirected evidence root"
    )
    assert live.policy.source == "investor_strategy.json"

    injected = tmp_path / "strategy.json"

    assert CapitalPolicyService(injected)._path == injected

    tree = ast.parse(pathlib.Path("app/services/capital_policy_service.py").read_text())
    modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    assert all("evidence_root" not in module for module in modules), (
        "the capital policy service must not hang from the evidence root"
    )


# ── 34–37: the portfolio observation clock is the broker's ──────────


def test_34_a_recent_response_receipt_passes_and_is_named_as_receipt() -> None:
    observed = portfolio_observation_for(
        last_sync=MOMENT - timedelta(minutes=2),
        policy=policy(),
        now=MOMENT,
    )

    assert observed.fresh
    assert observed.as_of == (
        "eToro account response received at 2026-08-19 14:58 UTC "
        "(receipt time; eToro states no account observation time)"
    )
    assert observed.refused_because == ""

    # The ruled boundary: this clock may gate, and may never be
    # dressed up as something eToro said about the account.
    for forbidden in ("observed at", "as of", "asof", "snapshot time"):
        assert forbidden not in observed.as_of.casefold(), forbidden


def test_35_an_older_receipt_refuses_and_still_says_when_it_arrived() -> None:
    observed = portfolio_observation_for(
        last_sync=MOMENT - timedelta(minutes=20),
        policy=policy(),
        now=MOMENT,
    )

    assert not observed.fresh
    assert "longer ago than the policy's 15-minute limit" in observed.refused_because
    assert observed.as_of == (
        "eToro account response received at 2026-08-19 14:40 UTC "
        "(receipt time; eToro states no account observation time)"
    ), "a stale refusal still says when the broker last answered"


def test_36_absent_naive_and_future_receipt_times_refuse_distinctly() -> None:
    absent = portfolio_observation_for(last_sync=None, policy=policy(), now=MOMENT)
    naive = portfolio_observation_for(
        last_sync=datetime(2026, 8, 19, 14, 58),
        policy=policy(),
        now=MOMENT,
    )
    future = portfolio_observation_for(
        last_sync=MOMENT + timedelta(minutes=5),
        policy=policy(),
        now=MOMENT,
    )

    assert "no eToro account response has been recorded" in absent.refused_because
    assert "carries no timezone" in naive.refused_because
    assert "in the future" in future.refused_because

    for observed in (absent, naive, future):
        assert not observed.fresh
        assert observed.as_of == "", (
            "an unusable receipt time is never replaced by the evaluation clock"
        )

    reasons = {
        absent.refused_because,
        naive.refused_because,
        future.refused_because,
    }

    assert len(reasons) == 3


def test_37_a_fresh_brain_with_an_old_response_receipt_refuses_in_production(
    tmp_path,
) -> None:
    """The Brain is assembled now; the broker reading inside it is old.

    Stamping assembly time would pass this envelope. The gate must read
    `brain.portfolio.last_sync` and refuse.
    """

    from types import SimpleNamespace

    from app.commands.cycle import _envelope
    from app.domain.executive.executive_action import ActionKind

    brain = SimpleNamespace(
        portfolio=SimpleNamespace(last_sync=MOMENT - timedelta(minutes=20)),
        asset_class_for=lambda symbol: (
            __import__(
                "app.domain.asset_class", fromlist=["AssetClass"]
            ).AssetClass.STOCK
        ),
    )
    workspace = SimpleNamespace(
        decision=SimpleNamespace(symbol="KO", missing_evidence=()),
        action=SimpleNamespace(kind=ActionKind.OPEN),
        quality=None,
        evidence=None,
    )

    result = _envelope(
        workspace,
        policy_reading=reading_for(tmp_path, strategy_document()),
        brain=brain,
        weights={},
        cash_pct=58.0,
        total_value=10_000.0,
        drawdown_pct=2.0,
        quotes={"KO": quote_for("KO", minutes_old=2.0)},
        established_prices=frozenset({"KO"}),
        evaluated_at=MOMENT,
    )

    assert result is not None
    assert result.kind is EnvelopeKind.REFUSED
    assert "longer ago than the policy's 15-minute limit" in result.because
    assert result.portfolio_as_of.startswith("eToro account response received at"), (
        "portfolio_as_of describes the response receipt, not Brain assembly"
    )


# ── 38–43: the price belongs to the exact security ──────────────────


def test_38_no_quote_and_another_symbols_quote_both_refuse() -> None:
    missing = price_observation_for(
        symbol="ADBE", quote=None, policy=policy(), now=MOMENT
    )

    assert not missing.fresh
    assert "no market quote for ADBE" in missing.refused_because
    assert "another security's price cannot stand in for it" in (
        missing.refused_because
    )

    neighbour = price_observation_for(
        symbol="ADBE",
        quote=quote_for("AAPL", minutes_old=1.0),
        policy=policy(),
        now=MOMENT,
    )

    assert not neighbour.fresh
    assert "names AAPL, not ADBE" in neighbour.refused_because


def test_39_a_quote_without_provenance_refuses() -> None:
    observed = price_observation_for(
        symbol="ADBE",
        quote=quote_for("ADBE", dated=False),
        policy=policy(),
        now=MOMENT,
    )

    assert not observed.fresh
    assert "carries no provenance" in observed.refused_because


def test_40_a_last_known_reading_refuses_however_recent() -> None:
    observed = price_observation_for(
        symbol="KO",
        quote=quote_for("KO", minutes_old=1.0, last_known=True),
        policy=policy(),
        now=MOMENT,
    )

    assert not observed.fresh
    assert "did not answer" in observed.refused_because
    assert "recency cannot repair" in observed.refused_because


def test_41_non_finite_and_non_positive_prices_refuse() -> None:
    for bad in (float("nan"), float("inf"), 0.0, -5.0):
        observed = price_observation_for(
            symbol="KO",
            quote=quote_for("KO", price=bad),
            policy=policy(),
            now=MOMENT,
        )

        assert not observed.fresh, bad
        assert "not a positive finite figure" in observed.refused_because, bad


def test_42_staleness_and_clock_faults_refuse_and_freshness_quotes_provenance() -> None:
    stale = price_observation_for(
        symbol="KO",
        quote=quote_for("KO", minutes_old=40.0),
        policy=policy(),
        now=MOMENT,
    )

    assert not stale.fresh
    assert "older than the policy's 15-minute limit" in stale.refused_because

    naive_quote = MarketQuote(
        symbol="KO",
        name="KO",
        price=61.0,
        change_percent=0.0,
        reading=Provenance(
            source="Yahoo Finance",
            observed_at=datetime(2026, 8, 19, 14, 58),
        ),
    )
    naive = price_observation_for(
        symbol="KO", quote=naive_quote, policy=policy(), now=MOMENT
    )

    assert "carries no timezone" in naive.refused_because

    future = price_observation_for(
        symbol="KO",
        quote=quote_for("KO", minutes_old=-5.0),
        policy=policy(),
        now=MOMENT,
    )

    assert "in the future" in future.refused_because

    fresh_quote = quote_for("KO", minutes_old=2.0)
    fresh = price_observation_for(
        symbol="KO", quote=fresh_quote, policy=policy(), now=MOMENT
    )

    assert fresh.fresh
    assert fresh_quote.reading is not None
    assert fresh.as_of == fresh_quote.reading.stated(MOMENT), (
        "price_as_of is the exact quote's own provenance wording"
    )
    assert fresh.as_of == "Yahoo Finance, 2 minutes ago"


def test_43_a_fresh_neighbour_cannot_authorize_this_symbol_in_production_shape(
    tmp_path,
) -> None:
    """AAPL has a fresh reading; ADBE exists without provenance.

    An ADBE OPEN must refuse on ADBE's own quote — the discriminating
    control against any market-wide freshness shortcut.
    """

    from types import SimpleNamespace

    from app.commands.cycle import _envelope
    from app.domain.asset_class import AssetClass
    from app.domain.executive.executive_action import ActionKind

    brain = SimpleNamespace(
        portfolio=SimpleNamespace(last_sync=MOMENT - timedelta(minutes=2)),
        asset_class_for=lambda symbol: AssetClass.STOCK,
    )
    quotes = {
        "AAPL": quote_for("AAPL", minutes_old=2.0),
        "ADBE": quote_for("ADBE", dated=False),
    }
    policy_reading = reading_for(tmp_path, strategy_document())

    def open_workspace(symbol: str):
        return SimpleNamespace(
            decision=SimpleNamespace(symbol=symbol, missing_evidence=()),
            action=SimpleNamespace(kind=ActionKind.OPEN),
            quality=None,
            evidence=None,
        )

    def run_one(symbol: str):
        return _envelope(
            open_workspace(symbol),
            policy_reading=policy_reading,
            brain=brain,
            weights={},
            cash_pct=58.0,
            total_value=10_000.0,
            drawdown_pct=2.0,
            quotes=quotes,
            established_prices=frozenset(),
            evaluated_at=MOMENT,
        )

    adbe = run_one("ADBE")

    assert adbe is not None
    assert adbe.kind is EnvelopeKind.REFUSED
    assert "the ADBE quote carries no provenance" in adbe.because

    aapl = run_one("AAPL")

    assert aapl is not None
    assert aapl.kind is EnvelopeKind.UPWARD_BOUNDED, (
        "the same cycle authorizes the symbol whose own quote is fresh"
    )
    assert aapl.price_as_of == "Yahoo Finance, 2 minutes ago"


# ── 44–45: an unknown held weight is not zero ────────────────────────


def test_44_add_and_reduce_with_an_unresolved_weight_refuse_in_words() -> None:
    unresolved = capacity(weight=None)

    assert unresolved.capacity_pct is None
    assert "could not be resolved from the broker's own rows" in (
        unresolved.refused_because
    )

    add = envelope("add", cap=unresolved)

    assert add.kind is EnvelopeKind.REFUSED
    assert add.evidence_ceiling == "", (
        "an unresolved ADD receives no standard or starter allowance"
    )
    assert add.final_pct is None
    assert "could not be resolved" in add.because

    reduce = envelope("reduce", cap=unresolved)

    assert reduce.kind is EnvelopeKind.REFUSED, (
        "an unresolved REDUCE must not become NO_POLICY_MAGNITUDE"
    )
    assert reduce.kind is not EnvelopeKind.NO_POLICY_MAGNITUDE
    assert "could not be resolved" in reduce.because


def test_45_open_uses_zero_only_because_the_course_says_unheld(tmp_path) -> None:
    """Course-aware weights through the production wiring.

    A broker row that cannot be resolved to a symbol contributes no
    weight; an ADD on that security refuses, while an OPEN on a
    security the course itself states is unheld proceeds from zero.
    """

    from types import SimpleNamespace

    from app.commands.cycle import _envelope, _portfolio_weights
    from app.domain.asset_class import AssetClass
    from app.domain.executive.executive_action import ActionKind

    brain = SimpleNamespace(
        portfolio=SimpleNamespace(
            total_value=10_000.0,
            last_sync=MOMENT - timedelta(minutes=2),
            allocation=SimpleNamespace(cash=58.0),
            holdings=(
                SimpleNamespace(
                    instrument_id=7,
                    market_value_usd=800.0,
                    is_resolved=False,
                    symbol="",
                ),
                SimpleNamespace(
                    instrument_id=8,
                    market_value_usd=500.0,
                    is_resolved=True,
                    symbol="KO",
                ),
            ),
        ),
        asset_class_for=lambda symbol: AssetClass.STOCK,
    )

    weights, cash_pct, total_value = _portfolio_weights(brain)

    assert "PEP" not in weights, "the unresolved row yields no symbol weight"
    assert weights["KO"] == 5.0

    policy_reading = reading_for(tmp_path, strategy_document())
    quotes = {
        "PEP": quote_for("PEP", minutes_old=2.0),
        "ADBE": quote_for("ADBE", minutes_old=2.0),
    }

    def workspace(symbol: str, kind: ActionKind):
        return SimpleNamespace(
            decision=SimpleNamespace(symbol=symbol, missing_evidence=()),
            action=SimpleNamespace(kind=kind),
            quality=None,
            evidence=None,
        )

    def run_one(symbol: str, kind: ActionKind):
        return _envelope(
            workspace(symbol, kind),
            policy_reading=policy_reading,
            brain=brain,
            weights=weights,
            cash_pct=cash_pct,
            total_value=total_value,
            drawdown_pct=2.0,
            quotes=quotes,
            established_prices=frozenset(),
            evaluated_at=MOMENT,
        )

    add = run_one("PEP", ActionKind.ADD)

    assert add is not None
    assert add.kind is EnvelopeKind.REFUSED
    assert "could not be resolved from the broker's own rows" in add.because

    opened = run_one("ADBE", ActionKind.OPEN)

    assert opened is not None
    assert opened.kind is EnvelopeKind.UPWARD_BOUNDED, (
        "OPEN proceeds from zero because the course states unheld"
    )


# ── 46–48: persisted-object invariants ──────────────────────────────


def test_46_every_valid_envelope_kind_round_trips_through_the_store(
    tmp_path,
) -> None:
    from app.domain.daily_cycle import (
        ComparisonBasis,
        ComparisonOutcome,
        CycleFinished,
        CycleStage,
        CycleStarted,
        CycleStatus,
        DecisionSummary,
        StageOutcome,
    )
    from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

    specimens = {
        EnvelopeKind.UPWARD_BOUNDED: envelope("open"),
        EnvelopeKind.ZERO_CAPACITY: envelope("open", cap=capacity(weight=20.0)),
        EnvelopeKind.REDUCTION_FLOOR: envelope("reduce", cap=capacity(weight=24.5)),
        EnvelopeKind.NO_POLICY_MAGNITUDE: envelope("reduce", cap=capacity(weight=10.0)),
        EnvelopeKind.REFUSED: envelope("open", floor=False),
    }

    for kind, specimen in specimens.items():
        assert specimen.kind is kind, "each specimen is its intended shape"

    store = DailyCycleStore(tmp_path / "cycles")
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        CycleFinished(
            cycle_id="c1",
            finished_at=MOMENT,
            status=CycleStatus.COMPLETE,
            stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
            comparison=ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
            decisions=tuple(
                DecisionSummary(
                    symbol=f"S{index}",
                    state="RECOMMEND",
                    rationale="r",
                    action_kind=specimen.course,
                    envelope=specimen,
                )
                for index, specimen in enumerate(specimens.values())
            ),
        )
    )

    log = store.log()

    assert log.unreadable_records == 0

    decoded = log.records[0].finished

    assert decoded is not None

    for stored, specimen in zip(decoded.decisions, specimens.values(), strict=True):
        assert stored.envelope == specimen, "exact round-trip, every kind"


def test_47_contradictory_envelope_shapes_are_refused_at_construction() -> None:
    def build(**overrides):
        values = dict(
            symbol="KO",
            course="open",
            kind=EnvelopeKind.REFUSED,
            policy_source="investor_strategy.json",
            policy_version="testversion1",
            because="a stated reason",
        )
        values.update(overrides)

        return CapitalActionEnvelope(**values)

    upward = dict(
        kind=EnvelopeKind.UPWARD_BOUNDED,
        because="",
        final_pct=1.0,
        capacity_ceiling_pct=5.0,
        evidence_ceiling="standard_initial",
        binding_constraint="the evidence ceiling",
    )

    # The valid shapes construct.
    build(**upward)
    build(
        kind=EnvelopeKind.ZERO_CAPACITY,
        because="",
        binding_constraint="the cash floor (funding room)",
    )
    build(kind=EnvelopeKind.REDUCTION_FLOOR, course="reduce", because="", final_pct=2.0)
    build(kind=EnvelopeKind.NO_POLICY_MAGNITUDE, course="reduce", because="")
    build(kind=EnvelopeKind.REFUSED)

    contradictions: list[dict] = [
        {**upward, "course": "reduce"},
        {**upward, "final_pct": None},
        {**upward, "final_pct": 0.0},
        {**upward, "capacity_ceiling_pct": None},
        {**upward, "evidence_ceiling": ""},
        {**upward, "binding_constraint": ""},
        {**upward, "final_pct": float("nan")},
        {**upward, "final_pct": -1.0},
        {**upward, "capacity_ceiling_pct": float("inf") * -1},
        {**upward, "starter_capped": True},
        dict(
            kind=EnvelopeKind.ZERO_CAPACITY,
            because="",
            final_pct=1.0,
            binding_constraint="the cash floor (funding room)",
        ),
        dict(
            kind=EnvelopeKind.ZERO_CAPACITY,
            course="reduce",
            because="",
            binding_constraint="the cash floor (funding room)",
        ),
        dict(kind=EnvelopeKind.ZERO_CAPACITY, because="", binding_constraint=""),
        dict(kind=EnvelopeKind.REDUCTION_FLOOR, because="", final_pct=2.0),
        dict(
            kind=EnvelopeKind.REDUCTION_FLOOR,
            course="reduce",
            because="",
            final_pct=None,
        ),
        dict(
            kind=EnvelopeKind.NO_POLICY_MAGNITUDE,
            course="reduce",
            because="",
            final_pct=1.0,
        ),
        dict(kind=EnvelopeKind.NO_POLICY_MAGNITUDE, course="add", because=""),
        dict(because=""),
        dict(because="   "),
        dict(final_pct=1.0),
    ]

    for overrides in contradictions:
        with pytest.raises(ValueError):
            build(**overrides)


def test_48_a_contradictory_stored_envelope_makes_the_record_unreadable(
    tmp_path,
) -> None:
    from app.domain.daily_cycle import (
        ComparisonBasis,
        ComparisonOutcome,
        CycleFinished,
        CycleStage,
        CycleStarted,
        CycleStatus,
        DecisionSummary,
        StageOutcome,
    )
    from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

    store = DailyCycleStore(tmp_path / "cycles")
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        CycleFinished(
            cycle_id="c1",
            finished_at=MOMENT,
            status=CycleStatus.COMPLETE,
            stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
            comparison=ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
            decisions=(
                DecisionSummary(
                    symbol="KO",
                    state="RECOMMEND",
                    rationale="r",
                    action_kind="open",
                    envelope=envelope("open"),
                ),
            ),
        )
    )

    clean = store.log()

    assert clean.unreadable_records == 0
    assert len(clean.records) == 1

    # Corrupt the stored envelope into a contradictory shape: an upward
    # bound that carries no final figure.
    path = next((tmp_path / "cycles").glob("*.jsonl"))
    lines = path.read_text().splitlines()
    mutated = []

    for line in lines:
        row = json.loads(line)

        if row.get("kind") == "finished":
            row["decisions"][0]["envelope"]["final_pct"] = None

        mutated.append(json.dumps(row))

    path.write_text("\n".join(mutated) + "\n")

    corrupted = store.log()

    assert corrupted.unreadable_records == 1, (
        "a contradictory envelope refuses the whole record through the "
        "existing unreadable count"
    )

    # And removing the field entirely is the old contract: a
    # pre-envelope record stays valid, envelope None.
    mutated = []

    for line in path.read_text().splitlines():
        row = json.loads(line)

        if row.get("kind") == "finished":
            del row["decisions"][0]["envelope"]

        mutated.append(json.dumps(row))

    path.write_text("\n".join(mutated) + "\n")

    old_contract = store.log()

    assert old_contract.unreadable_records == 0

    finished = old_contract.records[0].finished

    assert finished is not None
    assert finished.decisions[0].envelope is None
