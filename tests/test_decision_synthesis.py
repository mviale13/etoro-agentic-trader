"""A conclusion an investor can argue with, and never one that invents.

The three properties this file holds, in the order they matter:

- nothing is invented — no trigger, no risk, no fact the canonical
  objects do not already carry;
- an empty part says it is empty, in words;
- a fact's origin travels with it, so an analyst's reading of market
  data never wears the authority of a figure read out of a filing.
"""

from datetime import UTC, datetime

from app.application.executive.decision_synthesis_builder import synthesise
from app.domain.agreement import agreement
from app.domain.business_understanding import (
    AlternativeConclusion,
    BusinessUnderstanding,
    Contingency,
)
from app.domain.company_archetype import Archetype, CompanyArchetype
from app.domain.decision_state import DecisionState
from app.domain.executive.decision_synthesis import FactOrigin
from app.domain.executive_decision import ExecutiveDecision
from app.domain.provenance import Provenance
from app.services.company_understanding_service import CompanyUnderstanding


def decision(
    state: DecisionState = DecisionState.RECOMMEND,
    strengths: tuple[str, ...] = ("Forward P/E below historical market average.",),
    risks: tuple[str, ...] = ("Annualised volatility is 36.7% over the past year.",),
    missing: tuple[str, ...] = (),
    next_trigger: str | None = None,
) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol="EXA",
        state=state,
        conviction=78,
        rationale="The investment case satisfies quality, evidence, "
        "valuation, risk, and portfolio gates.",
        evidence_as_of=Provenance(source="test", observed_at=datetime.now(UTC)),
        evidence_weighed=(),
        key_strengths=strengths,
        key_risks=risks,
        context_risks=("Limited diversification", "Cash concentration"),
        missing_evidence=missing,
        catalysts=(),
        next_trigger=next_trigger,
    )


def understanding(
    archetype: Archetype | None = Archetype.MANUFACTURER,
    narrowest_agreeing: int = 5,
    contingencies: tuple[Contingency, ...] = (),
) -> CompanyUnderstanding:
    business = BusinessUnderstanding(
        symbol="EXA",
        source="10-K 1",
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
        quorate=True,
        observation_count=5,
        quorum=5,
        engine="single-engine — manufacturing runs through 100% of revenue",
        sells=(),
        mechanisms=(),
        characteristics=CompanyArchetype(
            symbol="EXA",
            primary=archetype,
            secondary=None,
            candidates=(),
            coverage=(),
            measured=1.0,
            explained=1.0,
            missing=(),
            basis=(),
            undecided_because=None,
            source="10-K 1",
            reading=Provenance(source="test", observed_at=datetime.now(UTC)),
            quorate=True,
            narrowest=agreement(
                "narrowest",
                ["a"] * narrowest_agreeing + ["b"] * (5 - narrowest_agreeing),
            ),
        ),
        contingencies=contingencies,
        not_established=(),
        segments_because=None,
    )

    return CompanyUnderstanding(
        symbol="EXA",
        business=business,
        business_absent_because=None,
        financial=None,
        financial_absent_because="not read",
    )


# ── nothing is invented ─────────────────────────────────────────────


def test_no_trigger_is_invented_where_the_case_records_none() -> None:
    """The constraint that matters most: an invented trigger stops the search."""

    synthesis = synthesise(decision(next_trigger=None), understanding())

    assert synthesis.review_if == ()
    assert synthesis.review_if_absent is not None
    assert "No condition specific to this security" in synthesis.review_if_absent


def test_the_accounts_conditions_are_never_borrowed_to_fill_the_slot() -> None:
    """The defect this slice exists to remove.

    "Limited diversification" and "Cash concentration" are the account's,
    identical under every symbol, and shown on the same page as
    portfolio context. They must not answer *what would change this*.
    """

    synthesis = synthesise(decision(), understanding())

    conditions = [condition.condition for condition in synthesis.review_if]

    assert "Limited diversification" not in conditions
    assert "Cash concentration" not in conditions

    for fact in (*synthesis.because, *synthesis.despite):
        assert fact.statement not in ("Limited diversification", "Cash concentration")


def test_every_statement_comes_from_the_canonical_objects() -> None:
    """No fact appears that the decision or the understanding did not carry."""

    case = decision()
    known = understanding()

    synthesis = synthesise(case, known)

    for fact in synthesis.because:
        assert fact.statement in case.key_strengths

    for fact in synthesis.despite:
        assert (
            fact.statement in case.key_risks
            or fact.statement in case.missing_evidence
            or fact.origin is FactOrigin.ESTABLISHED
        )


# ── an empty part says so ───────────────────────────────────────────


def test_no_supporting_finding_is_reported_rather_than_left_blank() -> None:
    synthesis = synthesise(decision(strengths=()), understanding())

    assert synthesis.because == ()
    assert synthesis.because_absent is not None
    assert "not a judgment that the case is weak" in synthesis.because_absent


def test_no_opposing_finding_is_reported_without_claiming_there_is_no_risk() -> None:
    synthesis = synthesise(decision(risks=(), missing=()), understanding())

    assert synthesis.despite == ()
    assert synthesis.despite_absent is not None
    assert "only that none was read" in synthesis.despite_absent


def test_a_conclusion_with_nothing_to_argue_with_says_so() -> None:
    synthesis = synthesise(
        decision(strengths=(), risks=(), missing=(), next_trigger=None),
        understanding(),
    )

    assert not synthesis.is_challengeable


# ── origin travels with the fact ────────────────────────────────────


def test_an_analysts_reading_is_never_labelled_established() -> None:
    synthesis = synthesise(decision(), understanding())

    for fact in synthesis.because:
        assert fact.origin is FactOrigin.ASSESSED


def test_the_filings_facts_are_carried_and_marked_established() -> None:
    synthesis = synthesise(decision(), understanding())

    assert synthesis.established

    for fact in synthesis.established:
        assert fact.origin is FactOrigin.ESTABLISHED

    assert any("manufacturer" in fact.statement for fact in synthesis.established)


def test_a_narrow_established_claim_argues_against_the_case() -> None:
    """The one opposing fact this platform can call established."""

    synthesis = synthesise(
        decision(risks=(), missing=()),
        understanding(narrowest_agreeing=3),
    )

    assert synthesis.despite
    assert synthesis.despite[0].origin is FactOrigin.ESTABLISHED
    assert "3 of 5" in synthesis.despite[0].statement


def test_a_settled_understanding_raises_no_reservation() -> None:
    synthesis = synthesise(
        decision(risks=(), missing=()),
        understanding(narrowest_agreeing=5),
    )

    assert synthesis.despite == ()


# ── contingencies are the company's own review conditions ───────────


def test_a_contingency_that_could_conclude_differently_is_a_review_condition() -> None:
    contingency = Contingency(
        claim="how 'Cloud' earns",
        agreement=agreement("earning", ["a", "a", "a", "b", "b"]),
        as_it_stands="Manufacturer",
        consumed=True,
        alternatives=(
            AlternativeConclusion(
                answer="services",
                given=2,
                concludes="Diversified",
                primary=Archetype.DIVERSIFIED,
            ),
        ),
    )

    synthesis = synthesise(
        decision(),
        understanding(contingencies=(contingency,)),
    )

    assert synthesis.review_if
    assert synthesis.review_if[0].origin is FactOrigin.ESTABLISHED
    assert "how 'Cloud' earns" in synthesis.review_if[0].condition

    would = synthesis.review_if[0].would_change

    assert would is not None
    assert "Diversified" in would


def test_a_named_trigger_is_carried_through_unchanged() -> None:
    synthesis = synthesise(decision(next_trigger="Price falls below 120"), None)

    assert synthesis.review_if
    assert synthesis.review_if[0].condition == "Price falls below 120"
    assert synthesis.review_if[0].origin is FactOrigin.ASSESSED


def test_a_missing_measurement_is_a_condition_and_not_a_fact_against() -> None:
    """Not knowing something is what would settle the case, not an argument.

    It was briefly both, which printed the identical sentence under two
    opposite headings and read as two findings when it was one.
    """

    synthesis = synthesise(
        decision(risks=(), missing=("Quality data is unavailable for EXA.",)),
        understanding(),
    )

    opposing = {fact.statement for fact in synthesis.despite}
    conditions = {condition.condition for condition in synthesis.review_if}

    assert opposing & conditions == set()
    assert "Quality data is unavailable for EXA." in conditions
    assert opposing == set()


def test_an_unmeasured_case_is_never_told_nothing_would_change_it() -> None:
    """The failure the role split exists to prevent.

    A case held back only by what has not been measured has an obvious
    condition for review — measuring it. Reporting "no condition is
    recorded" there would be false, and would stop the investor looking.
    """

    synthesis = synthesise(
        decision(risks=(), missing=("Quality data is unavailable for EXA.",)),
        understanding(),
    )

    assert synthesis.review_if
    assert synthesis.review_if_absent is None
    assert synthesis.is_challengeable

    assert synthesis.despite_absent is not None
    assert "listed below as the condition" in synthesis.despite_absent


# ── the synthesis decides nothing ───────────────────────────────────


def test_the_synthesis_carries_the_decision_it_was_given() -> None:
    for state in (DecisionState.RECOMMEND, DecisionState.MONITOR):
        synthesis = synthesise(decision(state=state), understanding())

        assert synthesis.state is state
        assert synthesis.conviction == 78


def test_an_unread_company_still_yields_a_conclusion() -> None:
    """The dossier holds up when nothing has been read from a filing."""

    synthesis = synthesise(decision(), None)

    assert synthesis.because
    assert synthesis.despite
    assert synthesis.established == ()
