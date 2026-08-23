"""Separate growth metrics — the owner's ruling of 2026-08-23, pinned.

Filing growth and provider growth are non-comparable measurements
(`GROWTH_METRIC_AUTHORITY_MEASUREMENT.md`), so each carries its
authority in its name wherever it appears: *"— FY filing"* against
*"Provider-reported … — period not stated"*. Nothing is compared,
reconciled, blended or averaged; no threshold, band, conviction, gate
or envelope moves; and the unqualified "Growth is …" is unproducible.
"""

from __future__ import annotations

import re

from app.analysts.growth_analyst import GrowthAnalyst
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.cio.artificial_cio import SCORE_FAMILIES
from app.domain.company_facts import CompanyFacts
from app.domain.company_research import CompanyResearch
from app.domain.fundamentals_presentation import (
    FundamentalStanding,
    fundamentals_for,
)
from app.domain.growth_opinion import GrowthVerdict
from app.domain.research_plan import AnalystKey
from tests.test_fundamentals_presentation import (
    GROSS_MARGIN_ABSENT,
    absent,
    established,
    row,
    snapshot,
    understanding,
)
from tests.test_fundamentals_presentation import (
    FinancialMeasure as Measure,
)


def facts(revenue: float | None, earnings: float | None) -> CompanyFacts:
    return CompanyFacts(
        instrument_id=1,
        symbol="DIS",
        name="The Walt Disney Company",
        asset_type="stock",
        exchange="NYSE",
        revenue_growth=revenue,
        earnings_growth=earnings,
    )


def growth_finding(revenue: float | None, earnings: float | None):
    """The one producible growth finding, through the real path."""

    opinion = GrowthAnalyst().analyze(facts(revenue, earnings))
    research = CompanyResearch(
        playbook=None,  # type: ignore[arg-type]
        opinions={AnalystKey.GROWTH: opinion},
    )

    findings = DecisionEvidenceBuilder._research_findings(research)

    return findings[0] if findings else None


# ── the analyst's own sentence ──────────────────────────────────────


def test_the_evidence_sentence_states_the_authority_and_its_limits() -> None:
    """DIS's provider figure, in the ruling's own substance."""

    opinion = GrowthAnalyst().analyze(facts(None, -0.483))

    assert opinion.evidence == (
        "Provider-reported earnings growth was -48.3%; the stored provider "
        "record states neither its reporting period nor its formula.",
    )


def test_thresholds_bands_and_verdicts_are_untouched() -> None:
    """The naming slice moves wording and nothing arithmetical."""

    opinion = GrowthAnalyst().analyze(facts(0.25, 0.35))

    assert opinion.score == 92
    assert opinion.verdict is GrowthVerdict.STRONG

    declining = GrowthAnalyst().analyze(facts(0.068, -0.483))

    assert declining.verdict is GrowthVerdict.DECLINING


def test_a_missing_provider_field_is_never_inferred_from_a_filing() -> None:
    """Control 4: the analyst sees the provider's absence, whole."""

    opinion = GrowthAnalyst().analyze(facts(None, None))

    assert opinion.verdict is GrowthVerdict.UNKNOWN
    assert opinion.confidence == 0.0
    assert opinion.evidence == ()


# ── the finding: a signal, never an unqualified conclusion ──────────


def test_the_verdict_is_worded_as_a_provider_reported_signal() -> None:
    finding = growth_finding(0.068, -0.483)

    assert finding is not None
    assert finding.statement.startswith(
        "The provider-reported growth signal is declining — "
    )
    assert "Provider-reported earnings growth was -48.3%" in finding.statement
    assert "states neither its reporting period nor its formula" in finding.statement


def test_no_producible_sentence_says_unqualified_growth_is() -> None:
    """Control 2, across every verdict the analyst can produce."""

    cases = (
        (0.35, 0.35),  # strong
        (0.12, 0.08),  # moderate
        (0.02, 0.02),  # weak
        (-0.15, -0.05),  # declining
        (0.25, None),  # partial
    )

    for revenue, earnings in cases:
        finding = growth_finding(revenue, earnings)

        assert finding is not None
        assert not re.match(
            r"^Growth is (strong|moderate|weak|declining)", finding.statement
        ), finding.statement
        assert finding.statement.startswith("The provider-reported growth signal is")


def test_other_analysts_keep_their_names() -> None:
    """The rename is growth's alone — no broader authority redesign."""

    assert DecisionEvidenceBuilder._FINDING_ASPECTS == {
        AnalystKey.GROWTH: "The provider-reported growth signal"
    }
    assert AnalystKey.PROFITABILITY.label == "Profitability"


# ── the Fundamentals section: both quantities, distinct names ───────


def test_dis_renders_both_quantities_with_distinct_names() -> None:
    """Control 1, DIS's shape: filing earnings wins and says FY filing;
    the provider figure lives in the analyst sentence, never this row."""

    facts_rows = fundamentals_for(
        understanding((established(Measure.EARNINGS_GROWTH, 1.3265),)),
        snapshot(),
    )

    earnings = row(facts_rows, "earnings_growth")

    assert earnings.standing is FundamentalStanding.FILING_EVIDENCE
    assert earnings.label == "Earnings growth — FY filing"
    assert earnings.value == 1.3265

    finding = growth_finding(0.068, -0.483)

    assert finding is not None
    assert "-48.3%" in finding.statement

    # And the two are never the same unqualified fact: neither carries
    # the other's bare label.
    assert "Provider-reported" not in earnings.label or "FY filing" in earnings.label
    assert "FY filing" not in finding.statement


def test_tsla_receives_the_symmetrical_treatment() -> None:
    """Filing revenue decline named FY filing; provider growth stays
    a qualified signal sentence."""

    facts_rows = fundamentals_for(
        understanding((established(Measure.REVENUE_GROWTH, -0.0293),)),
        snapshot(revenue_growth=0.255),
    )

    revenue = row(facts_rows, "revenue_growth")

    assert revenue.standing is FundamentalStanding.FILING_EVIDENCE
    assert revenue.label == "Revenue growth — FY filing"
    assert revenue.value == -0.0293

    finding = growth_finding(0.255, None)

    assert finding is not None
    assert "Provider-reported revenue growth was 25.5%" in finding.statement


def test_a_provider_fallback_growth_row_is_named_and_qualified() -> None:
    """Control 3: provider-only companies keep the observation, named."""

    facts_rows = fundamentals_for(None, snapshot())

    revenue = row(facts_rows, "revenue_growth")

    assert revenue.standing is FundamentalStanding.PROVIDER_FALLBACK
    assert revenue.label == "Provider-reported revenue growth — period not stated"
    assert (
        "The stored provider record states neither its reporting period "
        "nor its formula." in revenue.because
    )


def test_filing_first_precedence_is_retained() -> None:
    """Control 8: filing wins exactly as #240 built it, under new names."""

    facts_rows = fundamentals_for(
        understanding(
            (
                established(Measure.EARNINGS_GROWTH, 1.3265),
                absent(Measure.GROSS_MARGIN, GROSS_MARGIN_ABSENT),
            )
        ),
        snapshot(),
    )

    assert row(facts_rows, "earnings_growth").value == 1.3265
    assert (
        row(facts_rows, "gross_margin").standing
        is FundamentalStanding.PROVIDER_FALLBACK
    )

    # Non-growth rows keep their #240 names.
    assert row(facts_rows, "gross_margin").label == "Gross margin"


def test_filing_only_companies_remain_filing_only() -> None:
    """Control 5: no provider record offers nothing, under either name."""

    facts_rows = fundamentals_for(
        understanding((established(Measure.EARNINGS_GROWTH, 1.3265),)),
        None,
    )

    assert row(facts_rows, "earnings_growth").label == "Earnings growth — FY filing"
    assert row(facts_rows, "revenue_growth").standing is FundamentalStanding.UNAVAILABLE


# ── control 7: growth stays outside every canonical input ───────────


def test_growth_reaches_no_conviction_gate_or_envelope_input() -> None:
    """The measurement's structural facts, pinned where they can break."""

    assert "growth" not in SCORE_FAMILIES

    from app.services.quality_signal_service import QualityFactor

    assert {factor.value for factor in QualityFactor} == {
        "market_significance",
        "earnings",
        "dividend",
    }
