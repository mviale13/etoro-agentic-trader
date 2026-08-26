"""The research plan is closed, quoted, and promises nothing.

Three properties carry the slice, and each was a measured defect before
it was a test: every decision-critical blocker gets exactly one
requirement, a requirement's sentences belong to the layer that
established them, and nothing here says what resolving one would
produce.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.api.models.crypto_research_plan import (
    BLOCKING_ABSTENTIONS,
    NextStepKind,
    ResearchPlan,
    research_plan,
)
from app.cio.digital_asset_decision import (
    DecisionState,
    DigitalAssetDecision,
    UnresolvedQuestion,
)
from app.domain.investor_assessment import (
    InvestorAssessment,
    InvestorStatement,
    LicensedMeaning,
    StatementShape,
)


class _Committee:
    def __init__(self, key: str, name: str) -> None:
        self.key = key
        self.name = name


class _Cell:
    """A committee cell shaped like the matrix's, with only what is read."""

    def __init__(
        self,
        key: str,
        state: str,
        because: str = "",
        abstained: str | None = None,
        question: str = "Does the question apply?",
    ) -> None:
        self.committee = _Committee(key, f"{key.replace('_', ' ').title()} Committee")
        self.state = state
        self.because = because
        self.unavailable_because = None
        self.stated = because
        self.abstained_because = abstained
        self.question = question


class _Matrix:
    def __init__(self, *cells: _Cell) -> None:
        self.assessments = list(cells)


class _Methodology:
    def __init__(self, disclosed: bool) -> None:
        self.disclosed = disclosed


class _Concept:
    def __init__(self, value: str) -> None:
        self.value = value


class _Fact:
    def __init__(self, concept: str, source: str, disclosed: bool) -> None:
        self.concept = _Concept(concept)
        self.source = source
        self.methodology = _Methodology(disclosed)


class _Supply:
    def __init__(self, *facts: _Fact) -> None:
        self.facts = list(facts)


def _decision(
    unresolved: tuple[UnresolvedQuestion, ...] = (),
    uncertainties: tuple[str, ...] = (),
    ceiling: str = "No digital asset can currently progress past INVESTIGATE.",
) -> DigitalAssetDecision:
    return DigitalAssetDecision(
        symbol="HYPE",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established.",
        unresolved=unresolved,
        material_uncertainties=uncertainties,
        ceiling=ceiling,
    )


def _assessment(
    statements: tuple[InvestorStatement, ...] = (),
    silent_about: tuple[str, ...] = (),
    silent_committees: tuple[str, ...] = (),
) -> InvestorAssessment:
    return InvestorAssessment(
        asset="HYPE",
        statements=statements,
        silent_about=silent_about,
        silent_committees=silent_committees,
    )


def _uncertain(subject: str) -> InvestorStatement:
    return InvestorStatement(
        subject=subject,
        shape=StatementShape.UNCERTAIN,
        stated=f"{subject} cannot be stated as a single figure.",
        uncertainty=f"Sources differ on {subject.lower()}.",
        why_it_matters=(
            LicensedMeaning(
                question="Supply and dilution",
                stated="A holder of a partly issued token is diluted by a schedule.",
                licensed_by="the market asset lens",
            ),
        ),
        refs=("CoinGecko",),
    )


def _plan(**kwargs: Any) -> ResearchPlan:
    return research_plan(
        kwargs.get("decision", _decision()),
        kwargs.get("assessment", _assessment()),
        kwargs.get("matrix", _Matrix()),
        kwargs.get("supply", _Supply()),
        kwargs.get("issuance", None),
    )


class TestTheBlockerSet:
    def test_a_wrong_instrument_is_never_a_blocker(self) -> None:
        """BTC's Value Capture abstains on this and BTC has no blockers.

        A question that is the wrong instrument for an asset is
        answered, not blocked, and listing it would invent a defect out
        of a correct refusal.
        """

        assert "not_economically_applicable" not in BLOCKING_ABSTENTIONS

        plan = _plan(
            matrix=_Matrix(
                _Cell(
                    "value_capture",
                    "abstained",
                    abstained="not_economically_applicable",
                )
            )
        )

        assert plan.requirements == ()
        assert plan.absent_because is not None

    @pytest.mark.parametrize("because", sorted(BLOCKING_ABSTENTIONS))
    def test_an_evidence_abstention_is_a_blocker(self, because: str) -> None:
        plan = _plan(
            matrix=_Matrix(
                _Cell("supply_governance", "abstained", "Nothing is held.", because)
            )
        )

        assert len(plan.requirements) == 1

    def test_a_silent_committee_is_not_counted_twice(self) -> None:
        """TAO is the case: its two silent subjects *are* its committees.

        `silent_committees` is documented as a subset of `silent_about`,
        so subtracting it is a typed dedup rather than a name match.
        """

        plan = _plan(
            matrix=_Matrix(
                _Cell(
                    "supply_governance",
                    "abstained",
                    "No role.",
                    "applicability_unestablished",
                )
            ),
            assessment=_assessment(
                silent_about=("Supply Governance",),
                silent_committees=("Supply Governance",),
            ),
        )

        assert len(plan.requirements) == 1
        assert plan.requirements[0].blocker == "supply_governance"

    def test_a_silent_non_committee_subject_is_its_own_blocker(self) -> None:
        """ETH and SOL are silent about maximum supply and no committee is."""

        plan = _plan(
            decision=_decision(
                unresolved=(
                    UnresolvedQuestion(
                        owner="Maximum supply",
                        stated="This platform holds nothing useful about it.",
                    ),
                )
            ),
            assessment=_assessment(silent_about=("Maximum supply",)),
        )

        assert len(plan.requirements) == 1
        assert plan.requirements[0].blocker == "Maximum supply"
        assert (
            plan.requirements[0].what_is_missing
            == "This platform holds nothing useful about it."
        )

    def test_one_requirement_per_blocker_and_never_two(self) -> None:
        plan = _plan(
            matrix=_Matrix(
                _Cell("supply_governance", "abstained", "x", "insufficient_evidence")
            ),
            assessment=_assessment(
                statements=(
                    _uncertain("Tokens in existence"),
                    _uncertain("Circulating supply"),
                ),
            ),
        )

        blockers = [item.blocker for item in plan.requirements]

        assert len(blockers) == 3
        assert len(set(blockers)) == 3


class TestTheNextStep:
    def test_an_unconvened_committee_is_the_one_thing_movrvest_can_do(self) -> None:
        plan = _plan(matrix=_Matrix(_Cell("value_capture", "unavailable", "Off.")))

        requirement = plan.requirements[0]

        assert requirement.next_step_kind is NextStepKind.CONVENE_COMMITTEE
        assert requirement.retryable is True
        assert "existing MOVRvest workflow" in requirement.next_step_stated

    def test_an_evidence_gap_says_so_rather_than_manufacturing_activity(self) -> None:
        plan = _plan(
            matrix=_Matrix(
                _Cell("supply_governance", "abstained", "x", "insufficient_evidence")
            )
        )

        requirement = plan.requirements[0]

        assert requirement.next_step_kind is NextStepKind.NOT_CURRENTLY_RESOLVABLE
        assert requirement.retryable is False
        assert "No MOVRvest workflow can obtain this" in requirement.next_step_stated

    def test_the_undisclosed_count_comes_from_typed_flags(self) -> None:
        """3 of 4 for HYPE's circulating estimate, counted not parsed."""

        plan = _plan(
            assessment=_assessment(statements=(_uncertain("Circulating supply"),)),
            supply=_Supply(
                _Fact("circulating_estimate", "Hyperliquid info API", True),
                _Fact("circulating_estimate", "TokenInsight", False),
                _Fact("circulating_estimate", "CoinGecko", False),
                _Fact("circulating_estimate", "Yahoo Finance", False),
            ),
        )

        requirement = plan.requirements[0]

        assert "3 of 4" in requirement.resolution_needed
        assert "3 of 4" in requirement.next_step_stated

    def test_it_never_says_why_an_issuance_rule_is_absent(self) -> None:
        """`None` conflates *no rule exists* with *no reader was built*.

        TAO's own developments record a halving, so a mechanical rule
        plainly exists while `rule("TAO")` returns `None`. Nothing here
        may pick a side.
        """

        plan = _plan(
            matrix=_Matrix(
                _Cell(
                    "supply_governance",
                    "abstained",
                    "No mechanical issuance rule is held.",
                    "insufficient_evidence",
                )
            ),
            issuance=None,
        )

        prose = " ".join(
            item.next_step_stated + item.resolution_needed for item in plan.requirements
        ).lower()

        for claim in (
            "allocation-release",
            "no rule exists",
            "has no issuance rule",
            "does not have",
        ):
            assert claim not in prose


class TestItPromisesNothing:
    def test_no_requirement_promises_an_outcome(self) -> None:
        plan = _plan(
            matrix=_Matrix(
                _Cell("supply_governance", "abstained", "x", "insufficient_evidence"),
                _Cell("value_capture", "unavailable", "Off."),
            ),
            assessment=_assessment(statements=(_uncertain("Circulating supply"),)),
        )

        prose = " ".join(
            f"{item.next_step_stated} {item.resolution_needed} {item.why_it_matters}"
            for item in plan.requirements
        ).lower()

        for promise in (
            "will recommend",
            "will monitor",
            "will research",
            "will alert",
            "we will",
            "buy",
            "conviction",
            "capital envelope",
        ):
            assert promise not in prose, promise

    def test_reconsideration_is_licensed_and_never_a_recommendation(self) -> None:
        stated = _plan().reconsideration.lower()

        assert "can reconsider" in stated
        assert "will recommend" not in stated
        assert "does not produce a recommendation" in stated

    def test_there_is_no_score_no_count_and_no_completeness(self) -> None:
        fields = _plan().as_dict()

        assert set(fields) == {
            "symbol",
            "asks_for_capital",
            "requirements",
            "absent_because",
            "reconsideration",
        }

        for forbidden in ("progress", "percent", "complete", "score", "rank"):
            assert forbidden not in " ".join(fields).lower()

    def test_asks_for_capital_reads_the_decision_and_decides_nothing(self) -> None:
        assert _plan(decision=_decision(ceiling="A limit.")).asks_for_capital is False
        assert _plan(decision=_decision(ceiling="")).asks_for_capital is True

    def test_an_empty_plan_states_its_absence(self) -> None:
        plan = _plan()

        assert plan.requirements == ()
        assert plan.absent_because is not None
