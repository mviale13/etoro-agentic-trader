"""Per-security evidence and its effect on executive decisions."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from app.application.brain.perception.security_perception import (
    SecurityPerception,
)
from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.brain import Brain, BrainBuilder
from app.domain.company_facts import CompanyFacts
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_research import CompanyResearch
from app.domain.company_signals import CompanySignals
from app.domain.earnings_schedule import (
    EarningsSchedule,
    EarningsWindow,
    written,
)
from app.domain.finding import Finding
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.momentum_signal import MomentumSignal
from app.domain.portfolio_position import PortfolioPosition
from app.domain.provenance import Provenance
from app.domain.quality_signal import QualitySignal
from app.domain.risk_signal import RiskSignal
from app.domain.value_signal import ValueSignal
from app.domain.watchlist_item import WatchlistItem
from app.services.risk_signal_service import RiskSignalService
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)

#: The suite's "today" is the real one: a case is dated against the current
#: UTC date, and a pinned date would rot overnight.
TODAY = datetime.now(UTC).date()


def make_company(
    symbol: str,
    recommendation: str = "HOLD",
    confidence: int = 60,
    quality: str = "HIGH",
    valuation: str = "CHEAP",
    trend: str = "BULLISH",
    risk: RiskSignal | None = None,
    research: CompanyResearch | None = None,
    earnings: EarningsSchedule | None = None,
) -> CompanyRecommendation:
    return CompanyRecommendation(
        symbol=symbol,
        recommendation=recommendation,
        confidence=confidence,
        summary=f"{recommendation}: {symbol}",
        signals=CompanySignals(
            value=ValueSignal(
                valuation=valuation,
                confidence=confidence,
                evidence=(Finding.neutral(f"{symbol} looks {valuation.lower()}."),),
            ),
            quality=QualitySignal(
                quality=quality,
                confidence=confidence,
                evidence=(),
            ),
            momentum=MomentumSignal(
                trend=trend,
                strength="STRONG",
                confidence=confidence,
                evidence=(),
            ),
            risk=risk,
            research=research,
            earnings=earnings,
        ),
        evidence=(Finding.neutral(f"{symbol} evidence."),),
    )


def make_brain(
    evidence: dict[str, tuple[object, ...]] | None = None,
    holdings: tuple[PortfolioPosition, ...] = (),
) -> Brain:
    from dataclasses import replace

    portfolio = replace(make_portfolio(), holdings=holdings)

    return BrainBuilder(
        portfolio=portfolio,
        market=make_market(),
        investment_policy=make_policy(),
        evidence=evidence or {},
    ).build()


def make_holding(symbol: str, market_value_usd: float = 100.0) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=market_value_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=0.0,
        instrument_id=abs(hash(symbol)) % 10_000,
    )


def build_evidence(brain: Brain, symbol: str):
    reasoning = ReasoningService().reason(brain)
    opinions = CommitteeService().review(brain, reasoning, symbol)

    return DecisionEvidenceBuilder().build(
        symbol,
        brain,
        reasoning,
        opinions,
    )


def test_market_sensitivity_reaches_the_decision_as_per_security_evidence() -> None:
    """
    The reconsidered market gate: exposure is weighed, not gated.

    Now that beta is measured per security, a market reading bears on one
    holding more than another — a high-beta name and a defensive one are no
    longer the same case. It arrives on the security's `RiskSignal` and is
    weighed as evidence beside the decision, which is the honest form the
    market takes until a threshold can be calibrated against outcomes.
    """

    facts = CompanyFacts(
        instrument_id=1,
        symbol="GOOD",
        name="Good Co",
        asset_type="Stock",
        exchange="NASDAQ",
        realized_volatility=0.2,
        max_drawdown=0.1,
        market_sensitivity=MarketSensitivity(
            beta=1.8,
            correlation=0.7,
            observations=240,
            benchmark="SPY",
        ),
    )

    company = make_company("GOOD", risk=RiskSignalService().build(facts))
    brain = make_brain(evidence={"GOOD": (company,)})

    evidence = build_evidence(brain, "GOOD")

    assert any("1.80×" in statement for statement in evidence.evidence_weighed)


def test_fundamental_research_reaches_the_decision_as_weighed_evidence() -> None:
    """
    The starved analysts, fed and wired: their verdicts reach the case.

    Growth, profitability, the balance sheet and cash flow are read from the
    facts the platform already fetched, and each analyst's verdict is weighed
    as evidence — a strong one as a strength — rather than gated, exactly as
    the risk and sensitivity readings are.
    """

    import asyncio

    from app.services.company_research_service import CompanyResearchService

    facts = CompanyFacts(
        instrument_id=1,
        symbol="GOOD",
        name="Good Co",
        asset_type="stock",
        exchange="NASDAQ",
        gross_margin=0.62,
        operating_margin=0.30,
        net_margin=0.24,
        revenue_growth=0.18,
        free_cash_flow=50_000_000_000.0,
        operating_cash_flow=60_000_000_000.0,
        debt_to_equity=0.4,
        current_ratio=1.5,
    )

    research = asyncio.run(
        CompanyResearchService(knowledge_service=_NoKnowledge()).analyze(facts)
    )
    company = make_company("GOOD", research=research)
    brain = make_brain(evidence={"GOOD": (company,)})

    evidence = build_evidence(brain, "GOOD")

    assert any(
        statement.startswith("Profitability is")
        for statement in evidence.evidence_weighed
    )
    # An excellent-profitability read argues for the case, not merely noted.
    assert any(
        statement.startswith("Profitability is") for statement in evidence.strengths
    )


def test_security_evidence_distinguishes_two_holdings() -> None:
    brain = make_brain(
        evidence={
            "GOOD": (make_company("GOOD", quality="HIGH", valuation="CHEAP"),),
            "POOR": (make_company("POOR", quality="LOW", valuation="EXPENSIVE"),),
        }
    )

    good = build_evidence(brain, "GOOD")
    poor = build_evidence(brain, "POOR")

    assert good.quality_score > poor.quality_score
    assert good.valuation_score > poor.valuation_score


def test_a_sell_opinion_vetoes_the_case() -> None:
    brain = make_brain(
        evidence={"SELLME": (make_company("SELLME", recommendation="SELL"),)},
    )

    assert build_evidence(brain, "SELLME").analyst_veto is True


def test_a_hold_opinion_does_not_veto_the_case() -> None:
    brain = make_brain(
        evidence={"HOLDME": (make_company("HOLDME", recommendation="HOLD"),)},
    )

    assert build_evidence(brain, "HOLDME").analyst_veto is False


def test_low_quality_stays_above_the_rejection_floor() -> None:
    """The CIO must not reject what its own security committee holds."""

    from app.cio.decision_policy import DecisionPolicy

    brain = make_brain(
        evidence={"WEAK": (make_company("WEAK", quality="LOW"),)},
    )

    evidence = build_evidence(brain, "WEAK")

    assert evidence.quality_score >= DecisionPolicy().minimum_watchlist_quality


def test_missing_security_evidence_is_reported_not_invented() -> None:
    brain = make_brain()

    evidence = build_evidence(brain, "UNKNOWN")

    assert evidence.missing_evidence
    assert "UNKNOWN" in evidence.missing_evidence[0]


def test_unavailable_signals_are_reported_as_missing() -> None:
    brain = make_brain(
        evidence={
            "PARTIAL": (
                make_company("PARTIAL", quality="UNKNOWN", valuation="UNKNOWN"),
            )
        },
    )

    missing = build_evidence(brain, "PARTIAL").missing_evidence

    assert any("Valuation" in item for item in missing)
    assert any("Quality" in item for item in missing)


def test_portfolio_briefing_ranks_holdings_by_conviction() -> None:
    brain = make_brain(
        evidence={
            "STRONG": (make_company("STRONG", quality="HIGH", valuation="CHEAP"),),
            "WEAK": (
                make_company(
                    "WEAK",
                    recommendation="SELL",
                    quality="LOW",
                    valuation="EXPENSIVE",
                ),
            ),
        },
        holdings=(make_holding("WEAK"), make_holding("STRONG")),
    )

    briefing = PortfolioBriefingService().build(brain)

    assert briefing is not None

    symbols = [workspace.symbol for workspace in briefing.workspaces]

    # Ranked by conviction, not by the order the broker reported them.
    assert symbols == ["STRONG", "WEAK"]

    convictions = [
        workspace.decision.conviction
        for workspace in briefing.workspaces
        if workspace.decision
    ]
    assert convictions == sorted(convictions, reverse=True)


def test_what_was_weighed_is_not_a_list_of_strengths() -> None:
    """
    This collection was called `strengths`. It never held only strengths.

    A company the platform cannot score still produces evidence, and that
    evidence says so. Anything trusting the old name would have printed
    "Insufficient quality data." as a reason to invest — an absent
    measurement presented as a favourable finding.
    """

    from app.domain.company_facts import CompanyFacts
    from app.services.quality_signal_service import QualitySignalService

    unscoreable = QualitySignalService().build(
        CompanyFacts(
            instrument_id=1,
            symbol="OPAQUE",
            name="Opaque Holdings",
            asset_type="stock",
            exchange="4",
        )
    )

    company = CompanyRecommendation(
        symbol="OPAQUE",
        recommendation="HOLD",
        confidence=50,
        summary="HOLD: OPAQUE",
        signals=CompanySignals(
            value=ValueSignal(valuation="UNKNOWN", confidence=20, evidence=()),
            quality=unscoreable,
            momentum=MomentumSignal(
                trend="UNKNOWN",
                strength="WEAK",
                confidence=20,
                evidence=(),
            ),
        ),
        evidence=unscoreable.evidence,
    )

    evidence = build_evidence(make_brain(evidence={"OPAQUE": (company,)}), "OPAQUE")

    assert "Insufficient quality data." in evidence.evidence_weighed


def test_the_accounts_condition_is_not_evidence_about_a_security() -> None:
    """
    Every candidate's evidence used to open with the same lines.

    "Healthy liquidity" is true of the account whichever security is being
    judged, so repeating it under each one told the reader nothing and
    padded a thin case into a full-looking one.
    """

    brain = make_brain(evidence={"GOOD": (make_company("GOOD"),)})

    reasoning = ReasoningService().reason(brain)
    weighed = build_evidence(brain, "GOOD").evidence_weighed

    assert weighed == ("GOOD evidence.",)

    for strength in reasoning.portfolio.strengths:
        assert strength not in weighed


def test_evidence_handed_over_under_an_unknown_name_is_rejected() -> None:
    """
    Silently dropping it would report gathered evidence as absent.

    This is how the old name survived its own rename: `strengths=(...)`
    kept being passed, kept being accepted, and kept being discarded.
    """

    from pydantic import ValidationError

    from app.cio.executive_decision import DecisionEvidence

    with pytest.raises(ValidationError):
        DecisionEvidence(
            symbol="MSFT",
            evidence_score=80,
            portfolio_fit_score=70,
            conviction=99,  # type: ignore[call-arg]
        )


def test_the_investment_case_states_what_was_read_about_this_security() -> None:
    """
    Without this, every case reads the same.

    Strengths and risks describe the account and the market, so two
    securities produced identical prose. The findings about the security
    itself were built, carried as far as the decision, and then dropped.
    """

    brain = make_brain(
        evidence={
            "GOOD": (make_company("GOOD", quality="HIGH", valuation="CHEAP"),),
            "POOR": (make_company("POOR", quality="LOW", valuation="EXPENSIVE"),),
        },
        holdings=(make_holding("GOOD"), make_holding("POOR")),
    )

    briefing = PortfolioBriefingService().build(brain)

    assert briefing is not None

    cases = {case.symbol: case for case in briefing.brief.investment_cases}

    assert "GOOD evidence." in cases["GOOD"].evidence_weighed
    assert "POOR evidence." in cases["POOR"].evidence_weighed
    assert cases["GOOD"].evidence_weighed != cases["POOR"].evidence_weighed


def test_portfolio_briefing_is_none_without_holdings() -> None:
    assert PortfolioBriefingService().build(make_brain()) is None


def test_portfolio_brief_counts_every_holding() -> None:
    brain = make_brain(
        evidence={"A": (make_company("A"),), "B": (make_company("B"),)},
        holdings=(make_holding("A"), make_holding("B")),
    )

    briefing = PortfolioBriefingService().build(brain)

    assert briefing is not None
    assert "2 positions reviewed" in briefing.brief.headline
    assert len(briefing.brief.investment_cases) == 2


@pytest.mark.anyio
async def test_security_perception_skips_unresolved_holdings() -> None:
    """An unnamed instrument produces no evidence rather than a guess."""

    class ResolverStub:
        async def items(self) -> dict[int, WatchlistItem]:
            return {}

        async def items_for(self, instrument_ids) -> dict[int, WatchlistItem]:
            return {}

    from dataclasses import replace

    portfolio = replace(
        make_portfolio(),
        holdings=(
            PortfolioPosition(
                symbol="#1238",
                quantity=1.0,
                invested_usd=10.0,
                market_value_usd=10.0,
                unrealized_pnl_usd=0.0,
                instrument_id=1238,
            ),
        ),
    )

    perception = SecurityPerception(symbol_resolver=ResolverStub())  # type: ignore[arg-type]

    assert await perception.execute(portfolio) == {}


# ── The next earnings date as a per-security catalyst ────────────────


def schedule(
    starts_on: date | None = None,
    ends_on: date | None = None,
    unread: bool = False,
) -> EarningsSchedule:
    if starts_on is None:
        return EarningsSchedule(unread=unread)

    return EarningsSchedule(
        window=EarningsWindow(
            starts_on=starts_on,
            ends_on=ends_on,
            reading=Provenance(
                source="Yahoo Finance",
                observed_at=datetime.now(UTC),
            ),
        )
    )


def test_the_catalyst_is_this_securitys_own_dated_report() -> None:
    """
    Not the market's conditions, which are the same under every symbol.

    "Stable market conditions" was MSFT's catalyst, and everything else's,
    so the one line meant to say why this security now said nothing about
    this security at all.
    """

    report_day = TODAY + timedelta(days=6)

    brain = make_brain(
        {"MSFT": (make_company("MSFT", earnings=schedule(report_day)),)},
    )

    evidence = build_evidence(brain, "MSFT")

    assert evidence.catalysts == (
        f"Reports earnings in 6 days ({written(report_day, TODAY)}).",
    )
    assert "Stable market conditions" not in evidence.catalysts


def test_two_securities_no_longer_share_one_catalyst() -> None:
    """The whole defect, stated as a test: they differ, or they say nothing."""

    brain = make_brain(
        {
            "MSFT": (
                make_company("MSFT", earnings=schedule(TODAY + timedelta(days=6))),
            ),
            "AAPL": (
                make_company("AAPL", earnings=schedule(TODAY + timedelta(days=20))),
            ),
        },
    )

    msft = build_evidence(brain, "MSFT").catalysts
    aapl = build_evidence(brain, "AAPL").catalysts

    assert msft != aapl
    assert "6 days" in msft[0]
    assert "20 days" in aapl[0]


def test_a_company_with_no_published_date_offers_no_catalyst() -> None:
    """Absent, and said to be absent — never filled in with context."""

    brain = make_brain({"MSFT": (make_company("MSFT", earnings=schedule()),)})

    evidence = build_evidence(brain, "MSFT")

    assert evidence.catalysts == ()
    assert (
        "No upcoming earnings date is published for MSFT." in evidence.evidence_weighed
    )


def test_a_report_already_given_is_not_offered_as_a_reason_to_act() -> None:
    """A date that has passed is stated as past, and is not a catalyst."""

    reported_on = TODAY - timedelta(days=4)

    brain = make_brain(
        {"MSFT": (make_company("MSFT", earnings=schedule(reported_on)),)}
    )

    evidence = build_evidence(brain, "MSFT")

    assert evidence.catalysts == ()
    assert (
        f"Reported earnings on {written(reported_on, TODAY)}. "
        "No next date is published yet." in evidence.evidence_weighed
    )


def test_a_calendar_that_could_not_be_read_is_reported_as_missing() -> None:
    """A provider failure is a gap in the platform, not news about the company."""

    brain = make_brain(
        {"MSFT": (make_company("MSFT", earnings=schedule(unread=True)),)}
    )

    evidence = build_evidence(brain, "MSFT")

    assert evidence.catalysts == ()
    assert (
        "The earnings calendar for MSFT could not be read this cycle."
        in evidence.missing_evidence
    )
    assert not any("published" in line for line in evidence.evidence_weighed)


def test_a_scheduled_report_argues_neither_for_nor_against_the_security() -> None:
    """
    A catalyst is a date, and a date is not an opinion.

    Landing among the strengths would make "reports soon" a reason to buy,
    which is a view on a report nobody has read.
    """

    brain = make_brain(
        {"MSFT": (make_company("MSFT", earnings=schedule(TODAY - timedelta(days=2))),)},
    )

    evidence = build_evidence(brain, "MSFT")

    assert not any("earnings" in line for line in evidence.strengths)
    assert not any("earnings" in line for line in evidence.risks)


def test_a_security_with_no_evidence_at_all_has_no_catalyst() -> None:
    """Nothing gathered means nothing scheduled that anyone can state."""

    assert build_evidence(make_brain({}), "MSFT").catalysts == ()


# ── Why each score is the number it is ───────────────────────────────


def bases(brain: Brain, symbol: str):
    evidence = build_evidence(brain, symbol)

    assert evidence.score_bases is not None

    return evidence, evidence.score_bases


def test_a_quality_score_states_the_band_that_produced_it() -> None:
    """
    80 of 100 is not an observation about the business; it is HIGH, priced.

    A reader shown the number alone cannot tell a measurement from a house
    rule, so the whole scale travels with it and the findings the reading
    was taken from travel underneath.
    """

    company = make_company("MSFT", quality="HIGH")

    company = replace(
        company,
        signals=replace(
            company.signals,
            quality=QualitySignal(
                quality="HIGH",
                confidence=80,
                evidence=(
                    Finding.favourable("Large-cap company."),
                    Finding.favourable("Positive earnings."),
                ),
            ),
        ),
    )

    evidence, explained = bases(make_brain({"MSFT": (company,)}), "MSFT")

    assert evidence.quality_score == 80
    assert "Quality reads HIGH" in explained.quality.basis
    assert "HIGH at 80, MEDIUM at 62 and LOW at 40" in explained.quality.basis
    assert explained.quality.evidence == (
        "Large-cap company.",
        "Positive earnings.",
    )


def test_a_score_nobody_measured_says_why_rather_than_reading_zero() -> None:
    """The absence is worded where the score would have been."""

    company = make_company("MSFT", quality="UNKNOWN", valuation="UNKNOWN")

    evidence, explained = bases(make_brain({"MSFT": (company,)}), "MSFT")

    assert evidence.quality_score is None
    assert "no score was given" in explained.quality.basis

    assert evidence.valuation_score is None
    assert "no score was given" in explained.valuation.basis


def test_an_unevidenced_security_says_what_was_never_gathered() -> None:
    """
    Not "quality is unknown" — nothing about the security was collected.

    The basis also states what the score is never filled in from, because
    both of these once fell back to a number about the account.
    """

    _, explained = bases(make_brain({}), "MSFT")

    assert "No security-level analysis was gathered" in explained.quality.basis
    assert "the account's own health" in explained.quality.basis

    assert "price history was not read" in explained.safety.basis
    assert "The account's risk is never used" in explained.safety.basis


def test_safety_is_the_risk_reading_turned_once_and_said_to_be() -> None:
    """
    Every score here runs the same way, so risk is reported as safety.

    The bands shown are the bands scored on, turned by the same arithmetic
    that turns the number — a dashboard that restates a scale is one that
    will eventually show the wrong one. The inversion is stated outright,
    because a reader who remembers "Risk 45" must be able to see this is
    the same reading.
    """

    facts = CompanyFacts(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type="stock",
        exchange="NASDAQ",
        realized_volatility=0.32,
        max_drawdown=0.345,
    )

    company = make_company("MSFT", risk=RiskSignalService().build(facts))

    evidence, explained = bases(make_brain({"MSFT": (company,)}), "MSFT")

    assert evidence.risk_score == 45
    assert evidence.safety_score == 55

    assert "higher is safer" in explained.safety.basis

    for level, severity in RiskSignal.SEVERITIES.items():
        assert f"{level} at {100 - round(severity * 100)}" in explained.safety.basis

    assert "Annualised volatility is 32.0% over the past year." in (
        explained.safety.evidence
    )


def test_an_unmeasured_risk_is_never_reported_as_a_safe_security() -> None:
    """
    The one arithmetic this inversion must never do: 100 minus nothing.

    A security whose price history was too short to read is not safe. It
    is unmeasured, and on a dashboard where higher is better, filling that
    in would print the most dangerous number this platform could produce.
    """

    evidence, explained = bases(make_brain({"MSFT": (make_company("MSFT"),)}), "MSFT")

    assert evidence.risk_score is None
    assert evidence.safety_score is None
    assert "never" in explained.safety.basis


def test_the_evidence_score_names_both_terms_it_averaged() -> None:
    """It measures the reading, not the business, and says which readings."""

    company = make_company("MSFT", confidence=93)

    evidence, explained = bases(make_brain({"MSFT": (company,)}), "MSFT")

    assert "the security committee is" in explained.evidence.basis
    assert "93 of 100" in explained.evidence.basis

    assert any("Portfolio reasoning is" in line for line in explained.evidence.evidence)
    assert any("Market reasoning is" in line for line in explained.evidence.evidence)
    assert evidence.evidence_score > 0


def test_portfolio_fit_lists_every_term_including_the_unmeasured_ones() -> None:
    """
    An average of two terms presented as an average of three overstates it.

    So the term the policy could not answer is stated as unmeasured rather
    than dropped, and the basis says how many of how many were used.
    """

    brain = make_brain(
        {"MSFT": (make_company("MSFT"),)},
        holdings=(make_holding("MSFT", 1000.0),),
    )

    _, explained = bases(brain, "MSFT")

    assert "2 of 3 terms" in explained.portfolio_fit.basis
    assert "more room, not a better business" in explained.portfolio_fit.basis

    assert len(explained.portfolio_fit.evidence) == 3
    assert any(
        "Asset-class room is not measured" in line
        for line in explained.portfolio_fit.evidence
    )


class _NoKnowledge:
    """A unit test reads no filings and calls no model."""

    async def knowledge(self, symbol: str):
        from app.services.company_knowledge_service import (
            KnowledgeOutcome,
            KnowledgeState,
        )

        return KnowledgeOutcome(state=KnowledgeState.UNAVAILABLE)
