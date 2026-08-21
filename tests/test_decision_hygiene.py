"""The three prerequisites the owner's ruling of 2026-08-21 could gate on.

`SECURITY_VOLATILITY_DECISION_ROLE.md` accepted conclusion B — a
security's own volatility belongs to action eligibility and magnitude
rather than to thesis rejection — and gated the change on four
corrections. Three need no new owner threshold and land here.

**A — a non-positive P/E must never band CHEAP.** LUNR's forward P/E of
−328 satisfied `pe < 18` and banded CHEAP at confidence 90. The
volatility veto was hiding it: LUNR is rejected on volatility today, so
the reading never reaches a ranking. Remove the veto without this and it
does.

**B — unequal score coverage must not produce a cross-company
conviction ranking that reads as comparable.** Quality is a provider
proxy or absent for 60 of 64 stored equities, and an unmeasured quality
is omitted from the conviction mean rather than penalised — so a
security judged on four families outranks one judged on five, on two
numbers that were never on one scale.

**C — non-company securities must not pass through company-quality
analysis.** Built in F1 and pinned here, because the boundary is held by
consumers rather than by a wall: a seventh consumer that forgets to ask
`has_no_company` reintroduces the defect silently.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.api.models.cycle import CycleReviewResponse
from app.application.workspace.ranking import (
    comparable,
    coverage_of,
    rank_by_conviction,
)
from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.daily_cycle import (
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleLog,
    CycleRecord,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
)
from app.domain.provenance import Provenance
from app.services.quality_signal_service import QualitySignalService
from app.services.value_signal_service import ValueSignalService

MOMENT = datetime(2026, 8, 21, 7, 0, tzinfo=UTC)


def facts(**overrides) -> CompanyFacts:
    values = dict(
        instrument_id=1,
        symbol="LUNR",
        name="Intuitive Machines",
        asset_type="stock",
        exchange="NMS",
        fundamentals_reading=Provenance(source="Yahoo Finance", observed_at=MOMENT),
    )
    values.update(overrides)

    return CompanyFacts(**values)  # type: ignore[arg-type]


# ── A. a multiple that measures nothing ─────────────────────────────


def test_a_negative_forward_pe_is_never_cheap() -> None:
    """The measured defect: −328 read as the strongest cheapness signal."""

    signal = ValueSignalService().build(facts(forward_pe=-328.0))

    assert signal.valuation == "UNKNOWN"
    assert signal.valuation != "CHEAP"
    assert signal.confidence < 90


def test_a_zero_forward_pe_is_not_cheap_either() -> None:
    """Zero earnings is not infinitely cheap; the boundary is the metric's."""

    assert ValueSignalService().build(facts(forward_pe=0.0)).valuation == "UNKNOWN"


@pytest.mark.parametrize(
    "pe, band",
    [
        (9.9, "CHEAP"),
        (17.9, "CHEAP"),
        (18.0, "FAIR"),
        (27.9, "FAIR"),
        (28.0, "EXPENSIVE"),
    ],
)
def test_the_bands_themselves_are_unmoved(pe: float, band: str) -> None:
    """Only the domain the rule claims changed. Profitable controls hold."""

    assert ValueSignalService().build(facts(forward_pe=pe)).valuation == band


def test_the_reported_figure_survives_as_evidence() -> None:
    """Preserved exactly, because it is evidence about the company.

    Withholding the *meaning* is the correction. Withholding the number
    would hide a fact the investor is entitled to — a company expected
    to lose money — behind a silence that reads as missing data.
    """

    signal = ValueSignalService().build(facts(forward_pe=-328.0))

    assert signal.observation is not None
    assert signal.observation.value == -328.0
    assert "-328.0" in signal.observation.stated
    assert any("-328.0" in finding.statement for finding in signal.evidence)


def test_no_other_valuation_method_stands_in() -> None:
    """The basis says what is not measurable, and offers no substitute."""

    signal = ValueSignalService().build(
        facts(forward_pe=-328.0, market_cap=1e9, eps=-1.06, dividend_yield=0.0),
    )

    assert signal.basis is not None
    assert "not measurable through" in signal.basis

    for substitute in ("price-to-book", "price-to-sales", "peer", "EV/"):
        assert substitute not in signal.basis


def test_a_loss_making_company_is_not_a_fund() -> None:
    """UNKNOWN-and-applicable, so it lowers coverage rather than leaving it.

    `applicable=False` says the question does not arise — true of a fund
    or a token, which have no earnings for a price to be judged against.
    A loss-making company has earnings and they are negative. Collapsing
    the two would tell an investor those are the same kind of thing.
    """

    loss_maker = ValueSignalService().build(facts(forward_pe=-328.0))
    fund = ValueSignalService().build(facts(forward_pe=None), AssetClass.ETF)

    assert loss_maker.applicable is True
    assert fund.applicable is False


def test_the_refusal_names_the_rule_that_refused_it() -> None:
    """Identity, never endorsement — and version 2 is where it changed."""

    signal = ValueSignalService().build(facts(forward_pe=-328.0))

    assert signal.rule is not None
    assert signal.rule.identity == "pe-bands@2"


# ── B. two convictions, two denominators ────────────────────────────


def workspace(symbol: str, conviction: int | None, absent: tuple[str, ...] = ()):
    decision = (
        None
        if conviction is None and absent == ("none",)
        else SimpleNamespace(
            conviction=conviction,
            conviction_absent_families=absent,
        )
    )

    return SimpleNamespace(symbol=symbol, decision=decision)


def test_equal_coverage_still_ranks_by_conviction() -> None:
    """The change withholds a ranking; it does not abolish ranking."""

    ranked = rank_by_conviction(
        [workspace("AMD", 45), workspace("LUNR", 58), workspace("KO", 70)],
    )

    assert [item.symbol for item in ranked] == ["KO", "LUNR", "AMD"]
    assert comparable(ranked) is True


def test_unequal_coverage_is_not_ranked_by_conviction() -> None:
    """The measured inversion: LUNR 58 over AMD 45, on different families."""

    workspaces = [
        workspace("AMD", 45),
        workspace("LUNR", 58, absent=("business quality",)),
    ]

    assert comparable(workspaces) is False

    ranked = rank_by_conviction(workspaces)

    assert [item.symbol for item in ranked] == ["AMD", "LUNR"], (
        "by symbol — an order that is obviously not a judgment"
    )


def test_the_same_count_over_different_families_is_still_incomparable() -> None:
    """A count is not a coverage. Four of five twice is not one scale."""

    workspaces = [
        workspace("AAA", 60, absent=("business quality",)),
        workspace("BBB", 62, absent=("valuation",)),
    ]

    assert comparable(workspaces) is False


def test_a_case_with_no_conviction_contributes_no_coverage() -> None:
    """Nothing was computed, so there is no denominator to disagree with."""

    withheld = workspace("HYPE", None)

    assert coverage_of(withheld) is None
    assert comparable([workspace("AMD", 45), withheld]) is True


def test_a_complete_five_family_control_ranks() -> None:
    ranked = rank_by_conviction(
        [workspace("AAA", 40), workspace("BBB", 90), workspace("CCC", 65)],
    )

    assert [item.symbol for item in ranked] == ["BBB", "CCC", "AAA"]


# ── B, at the surface the investor reads ────────────────────────────


def summary(
    symbol: str, conviction: int | None, absent: tuple[str, ...] = (), *, said=True
):
    return DecisionSummary(
        symbol=symbol,
        state="INVESTIGATE",
        rationale="",
        conviction=conviction,
        conviction_participating=(
            (5 - len(absent)) if said and conviction is not None else None
        ),
        conviction_expected=5 if said and conviction is not None else None,
        conviction_absent_families=absent if said else (),
    )


def review(candidates: tuple[DecisionSummary, ...]) -> CycleReviewResponse:
    started = CycleStarted(cycle_id="c1", started_at=MOMENT)
    finished = CycleFinished(
        cycle_id="c1",
        finished_at=MOMENT,
        status=CycleStatus.COMPLETE,
        stages=(),
        comparison=ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
        decisions=(summary("KO", 50),),
        candidates=candidates,
    )

    return CycleReviewResponse.from_log(
        CycleLog(records=(CycleRecord(started=started, finished=finished),)),
    )


def test_the_cycle_projection_ranks_only_a_comparable_group() -> None:
    body = review((summary("AAA", 41), summary("BBB", 88), summary("DDD", 63)))

    assert body.candidates_ranked is True
    assert [c.symbol for c in body.candidates] == ["BBB", "DDD", "AAA"]


def test_the_cycle_projection_withholds_a_mixed_coverage_ranking() -> None:
    body = review(
        (
            summary("AAA", 41),
            summary("BBB", 88, absent=("business quality",)),
            summary("DDD", 63),
        )
    )

    assert body.candidates_ranked is False
    assert [c.symbol for c in body.candidates] == ["AAA", "BBB", "DDD"]

    # Every candidate is still carried, and every conviction still
    # travels with its own basis. Withholding the order is not dropping
    # the evaluation.
    assert len(body.candidates) == 3
    assert [c.conviction for c in body.candidates] == [41, 88, 63]


def test_a_record_that_does_not_state_coverage_is_never_assumed_uniform() -> None:
    """Silence is not agreement — a pre-ruling record loses the ranking."""

    body = review((summary("AAA", 41, said=False), summary("BBB", 88, said=False)))

    assert body.candidates_ranked is False
    assert [c.symbol for c in body.candidates] == ["AAA", "BBB"]


# ── C. the company boundary, pinned ─────────────────────────────────


def test_a_fund_receives_no_company_quality_verdict() -> None:
    """IB01.L's measured defect: LOW (40) from a structural dividend of zero.

    An accumulating US Treasury ETF cannot distribute by design, and
    `dividend_yield: 0.0` was the only readable company field.
    """

    fund = facts(
        symbol="IB01.L",
        name="iShares $ Treasury Bond 0-1yr UCITS ETF",
        asset_type="etf",
        dividend_yield=0.0,
        expense_ratio=0.0007,
    )

    signal = QualitySignalService().build(fund, AssetClass.ETF)

    assert signal.quality != "LOW"
    assert signal.quality == "UNKNOWN"


def test_a_fund_is_asked_no_earnings_question_either() -> None:
    fund = ValueSignalService().build(
        facts(symbol="IB01.L", asset_type="etf", forward_pe=None),
        AssetClass.ETF,
    )

    assert fund.applicable is False
    assert fund.basis is not None and "no earnings" in fund.basis


@pytest.mark.parametrize(
    "asset_class, bypasses",
    [
        (AssetClass.ETF, True),
        (AssetClass.CRYPTO, True),
        (AssetClass.COMMODITY, True),
        (AssetClass.STOCK, False),
        (AssetClass.UNKNOWN, False),
    ],
)
def test_the_boundary_is_membership_and_says_so(asset_class, bypasses) -> None:
    """The whole vocabulary, pinned.

    UNKNOWN deliberately keeps the company questions: an instrument this
    platform could not classify is not one it established has no
    business behind it, and asserting otherwise is the substitution the
    rest of the decision path stopped making.
    """

    assert asset_class.has_no_company is bypasses


def test_no_company_proxy_can_score_a_fund() -> None:
    """Every company field readable at once, and still no verdict.

    The guard is the whole factor set rather than the dividend that
    caused the defect: a future provider field must not be able to score
    a fund by arriving.
    """

    loaded = facts(
        symbol="IB01.L",
        asset_type="etf",
        dividend_yield=0.0,
        market_cap=5_000_000_000.0,
        eps=0.0,
        net_margin=0.0,
        roe=0.0,
        free_cash_flow=0.0,
    )

    signal = QualitySignalService().build(loaded, AssetClass.ETF)

    assert signal.quality == "UNKNOWN"
    assert signal.applicable is False, "the question does not arise for a fund"
    assert signal.earned == 0 and signal.available == 0, (
        "no company factor was even offered, so none could be earned"
    )
    assert signal.contributions == ()
