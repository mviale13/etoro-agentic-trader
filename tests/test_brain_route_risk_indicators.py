"""What the dashboard is told about portfolio risk, and what it is not.

`overall` is an equal mean of exactly four indicators. That makes it a
composite of those four and **not the account's total risk** — and
because it averages, a component at the ceiling can sit inside a
composite that reads low. These pin the facts a surface needs to say so
honestly: the count of indicators, the band of each one, which of them
are elevated, and whose limit the drawdown is measured against.
"""

from app.api.routes.brain import _risk
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)
from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.domain.market_risk import ExposureVolatility, MarketRisk


def assessment(**overrides: object) -> RiskAssessment:
    values: dict[str, object] = {
        "overall_risk_score": 0.30,
        "market_risk_score": 0.20,
        "concentration_risk_score": 0.30,
        "liquidity_risk_score": 0.40,
        "drawdown_risk_score": 0.30,
        "confidence": 0.80,
    }
    values.update(overrides)

    return RiskAssessment(**values)  # type: ignore[arg-type]


def exposure(
    volatility: float = 0.18,
    covered_share: float = 0.457,
) -> MarketRisk:
    return MarketRisk(
        volatility=volatility,
        exposures=(
            ExposureVolatility(
                exposure="equities",
                share=0.096,
                volatility=0.171,
                benchmarks=("SPY", "QQQ", "IWM"),
            ),
            ExposureVolatility(
                exposure="crypto",
                share=0.361,
                volatility=0.453,
                benchmarks=("BTC", "ETH"),
            ),
            ExposureVolatility(
                exposure="cash",
                share=0.542,
                volatility=0.0,
                benchmarks=(),
            ),
        ),
        covered_share=covered_share,
        reading=None,
    )


# ── the composite is a composite of four ────────────────────────────


def test_the_indicator_count_is_served_rather_than_implied() -> None:
    served = _risk(assessment())

    assert served is not None
    assert served["component_count"] == 4
    assert served["measured_count"] == 4


def test_an_unmeasured_indicator_lowers_the_count_it_reports() -> None:
    """So a surface can say "3 of 4" instead of "fully measured"."""

    served = _risk(assessment(market_risk_score=None, overall_risk_score=None))

    assert served is not None
    assert served["measured_count"] == 3
    assert served["component_count"] == 4


def test_every_indicator_is_named_and_banded_by_the_platforms_own_rule() -> None:
    served = _risk(assessment())

    assert served is not None
    components = served["components"]
    assert isinstance(components, list)

    assert [item["key"] for item in components] == [
        "market",
        "drawdown",
        "concentration",
        "cash_buffer",
    ]

    # `assessment_level`: <0.2 very_low, <0.4 low, <0.6 moderate,
    # <0.8 high, else very_high. Resolved here so no surface invents a
    # second set of thresholds.
    assert [item["level"] for item in components] == [
        "low",
        "low",
        "low",
        "moderate",
    ]


# ── a low composite must not hide a severe component ─────────────────


def test_a_component_at_the_ceiling_is_flagged_inside_a_low_composite() -> None:
    """
    The defect this exists to prevent. An equal mean of four puts a
    maximal concentration risk inside a composite that bands LOW, and a
    page reading only the composite would report reassurance.
    """

    served = _risk(
        assessment(
            market_risk_score=0.05,
            drawdown_risk_score=0.05,
            liquidity_risk_score=0.05,
            concentration_risk_score=1.0,
            overall_risk_score=(0.05 + 0.05 + 0.05 + 1.0) / 4,
        )
    )

    assert served is not None

    # The composite really does read low — this is not a contrived case.
    assert served["level"] == "low"

    flagged = [
        item["key"]
        for item in served["components"]  # type: ignore[union-attr]
        if item["elevated"]
    ]

    assert flagged == ["concentration"]


def test_elevated_means_the_platforms_own_high_bands_and_nothing_else() -> None:
    at_boundary = _risk(
        assessment(concentration_risk_score=0.6, overall_risk_score=0.3)
    )
    below_boundary = _risk(
        assessment(concentration_risk_score=0.59, overall_risk_score=0.3)
    )

    assert at_boundary is not None and below_boundary is not None

    def flagged(served: dict[str, object]) -> list[str]:
        return [
            item["key"]
            for item in served["components"]  # type: ignore[union-attr]
            if item["elevated"]
        ]

    # 0.6 is where `assessment_level` starts saying HIGH.
    assert flagged(at_boundary) == ["concentration"]
    assert flagged(below_boundary) == []


def test_an_unmeasured_component_is_never_flagged_as_elevated() -> None:
    served = _risk(assessment(concentration_risk_score=None, overall_risk_score=None))

    assert served is not None

    concentration = next(
        item
        for item in served["components"]  # type: ignore[union-attr]
        if item["key"] == "concentration"
    )

    assert concentration["score"] is None
    assert concentration["level"] is None
    assert concentration["elevated"] is False


# ── whose limit the drawdown is measured against ─────────────────────


def test_the_investors_own_limit_is_named_as_theirs() -> None:
    served = _risk(assessment(drawdown_limit_pct=15.0))

    assert served is not None
    assert served["drawdown_limit_pct"] == 15.0
    assert served["drawdown_limit_source"] == "investor"


def test_the_platform_default_is_never_attributed_to_the_investor() -> None:
    """
    The claim a risk page must not get wrong. Saying "the limit the
    investor set" over a figure this platform chose invites an argument
    with a limit nobody stated.
    """

    served = _risk(assessment(drawdown_limit_pct=None))

    assert served is not None
    assert served["drawdown_limit_pct"] == 20.0
    assert served["drawdown_limit_source"] == "platform_default"


def test_a_zero_limit_is_the_default_too_because_it_scores_nothing() -> None:
    # `PortfolioDrawdownService.risk_score` falls back to the default for
    # a non-positive tolerance, so the page must say the same.
    served = _risk(assessment(drawdown_limit_pct=0.0))

    assert served is not None
    assert served["drawdown_limit_source"] == "platform_default"


def test_the_limit_travels_with_the_score_it_was_measured_against() -> None:
    """
    The serializer reads the limit off the assessment, not off a policy
    it fetches itself.

    That distinction is not cosmetic: `BrainSnapshot` carries no policy
    at all, so a serializer reaching for one found nothing and reported
    the platform default for every account — including accounts whose
    investor had set a limit. The analyst that computed the score is the
    only place that knows which limit the score is a ratio against.
    """

    import inspect

    from app.application.brain.reasoning.risk_analyst import RiskAnalyst

    source = inspect.getsource(
        __import__("app.api.routes.brain", fromlist=["_risk"])._risk
    )

    assert "risk.drawdown_limit_pct" in source
    assert "investment_policy" not in source

    # And the analyst does carry it.
    assert "drawdown_limit_pct" in inspect.getsource(RiskAnalyst.assess)


# ── what each indicator is a score of ────────────────────────────────


def test_the_cash_threshold_is_quoted_from_the_analyst_not_restated() -> None:
    served = _risk(assessment())

    assert served is not None
    assert served["cash_buffer_threshold_pct"] == (
        RiskAnalyst.CASH_BUFFER_THRESHOLD_PCT
    )


def test_the_market_figure_says_what_it_measured_and_how_much_it_covers() -> None:
    served = _risk(assessment(market_exposure=exposure()))

    assert served is not None
    assert served["market_volatility_pct"] == 18.0
    assert served["market_covered_pct"] == 45.7
    assert served["market_benchmarks"] == ["BTC", "ETH", "IWM", "QQQ", "SPY"]


def test_partial_market_coverage_is_reported_as_the_share_it_describes() -> None:
    """
    A blended volatility over 45.7% of an account is not a statement
    about the account, and the share is the only thing that says so.
    """

    served = _risk(
        assessment(market_exposure=exposure(volatility=0.03, covered_share=0.12))
    )

    assert served is not None
    assert served["market_volatility_pct"] == 3.0
    assert served["market_covered_pct"] == 12.0


def test_no_exposure_leaves_the_market_figures_absent_never_zero() -> None:
    served = _risk(assessment(market_exposure=None))

    assert served is not None
    assert served["market_volatility_pct"] is None
    assert served["market_covered_pct"] is None
    assert served["market_benchmarks"] == []


# ── the contract that already existed is untouched ───────────────────


def test_the_flat_keys_the_contract_carried_are_unchanged() -> None:
    served = _risk(assessment())

    assert served is not None

    for key in (
        "overall",
        "level",
        "market",
        "concentration",
        "liquidity",
        "drawdown",
        "factors",
        "mitigants",
        "evidence",
        "unmeasured",
    ):
        assert key in served

    assert served["liquidity"] == 0.40
    assert served["overall"] == 0.30


def test_an_absent_assessment_is_still_served_as_null() -> None:
    assert _risk(None) is None
