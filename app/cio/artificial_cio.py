from app.cio.decision_policy import DecisionPolicy
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import (
    DecisionEvidence,
    ExecutiveDecision,
)
from app.cio.investment_case import InvestmentCase
from app.cio.timeline import (
    InvestmentCaseEvent,
    InvestmentCaseEventType,
)


class ArtificialCIO:
    """Executive brain responsible for investment-case decisions."""

    def __init__(
        self,
        policy: DecisionPolicy | None = None,
    ) -> None:
        self._policy = policy or DecisionPolicy()

    def evaluate(
        self,
        investment_case: InvestmentCase,
        evidence: DecisionEvidence,
    ) -> InvestmentCase:
        if investment_case.symbol != evidence.symbol:
            raise ValueError(
                "Decision evidence symbol must match investment case symbol.",
            )

        decision = self.decide(evidence)
        previous_state = investment_case.state

        if previous_state is None:
            event_type = InvestmentCaseEventType.CASE_CREATED
        elif previous_state is decision.state:
            event_type = InvestmentCaseEventType.DECISION_REAFFIRMED
        else:
            event_type = InvestmentCaseEventType.DECISION_CHANGED

        event = InvestmentCaseEvent(
            event_type=event_type,
            previous_state=previous_state,
            new_state=decision.state,
            rationale=decision.rationale,
        )

        return investment_case.with_decision(
            decision,
            event,
        )

    def decide(
        self,
        evidence: DecisionEvidence,
    ) -> ExecutiveDecision:
        state, rationale = self._determine_state(evidence)

        return ExecutiveDecision(
            symbol=evidence.symbol,
            state=state,
            conviction=self._calculate_conviction(
                evidence,
                state,
            ),
            rationale=rationale,
            evidence_as_of=evidence.evidence_as_of,
            evidence_weighed=evidence.evidence_weighed,
            key_strengths=evidence.strengths,
            key_risks=evidence.risks,
            context_risks=evidence.context_risks,
            missing_evidence=evidence.missing_evidence,
            catalysts=evidence.catalysts,
            next_trigger=evidence.next_trigger,
        )

    def _determine_state(
        self,
        evidence: DecisionEvidence,
    ) -> tuple[DecisionState, str]:
        policy = self._policy

        if evidence.hard_reject:
            return (
                DecisionState.REJECT,
                "The investment case violates a hard policy gate.",
            )

        if evidence.analyst_veto:
            return (
                DecisionState.REJECT,
                "A specialist analyst identified a veto-level risk.",
            )

        # Nothing about the security itself was gathered — the symbol names
        # nothing the platform could describe. Said plainly, and kept apart
        # from "quality has not been measured", which promises a reading of
        # a security we do not have. What is true here is only that there is
        # no security-level analysis, not why; the platform does not claim
        # the symbol is unknown when a fetch may simply have failed.
        if not evidence.security_evidenced:
            return (
                DecisionState.INVESTIGATE,
                (
                    f"No security-level analysis is available for "
                    f"{evidence.symbol}, so there is nothing to base a "
                    "decision on."
                ),
            )

        # An unmeasured score is never a reason to reject: not knowing
        # something is not the same as knowing it is bad. It is, further
        # down, a reason not to progress.
        if (
            evidence.risk_score is not None
            and evidence.risk_score > policy.maximum_acceptable_risk
        ):
            return (
                DecisionState.REJECT,
                "Risk exceeds the maximum permitted by policy.",
            )

        if (
            evidence.quality_score is not None
            and evidence.quality_score < policy.minimum_watchlist_quality
        ):
            return (
                DecisionState.REJECT,
                ("Business quality is insufficient to justify continued monitoring."),
            )

        if evidence.evidence_score < policy.minimum_investigation_evidence:
            return (
                DecisionState.MONITOR,
                (
                    "The opportunity is relevant, but available "
                    "evidence is still limited."
                ),
            )

        if evidence.quality_score is None:
            return (
                DecisionState.INVESTIGATE,
                self._unassessable_quality(evidence),
            )

        if (
            evidence.quality_score < policy.minimum_prepare_quality
            or evidence.evidence_score < policy.minimum_prepare_evidence
        ):
            return (
                DecisionState.INVESTIGATE,
                (
                    "The opportunity merits deeper research before "
                    "a thesis can be prepared."
                ),
            )

        if evidence.quality_score < policy.minimum_recommendation_quality:
            return (
                DecisionState.PREPARE,
                (
                    "The investment case is credible, but quality "
                    "conviction is not yet sufficient."
                ),
            )

        if evidence.evidence_score < policy.minimum_recommendation_evidence:
            return (
                DecisionState.PREPARE,
                (
                    "The thesis is promising, but recommendation-level "
                    "evidence is incomplete."
                ),
            )

        if evidence.valuation_score is None:
            return (
                DecisionState.PREPARE,
                self._unassessable_valuation(evidence),
            )

        if evidence.risk_score is None:
            return (
                DecisionState.PREPARE,
                (
                    "The case is credible, but risk has not been measured, "
                    "and no recommendation is made without it."
                ),
            )

        if evidence.valuation_score < policy.minimum_recommendation_valuation:
            return (
                DecisionState.PREPARE,
                (
                    "The company is attractive, but valuation does not "
                    "currently support action."
                ),
            )

        if evidence.portfolio_fit_score is None:
            return (
                DecisionState.PREPARE,
                (
                    "The case is credible, but how it would fit the "
                    "portfolio has not been measured."
                ),
            )

        if evidence.portfolio_fit_score < policy.minimum_portfolio_fit:
            return (
                DecisionState.PREPARE,
                (
                    "The thesis is actionable in isolation, but "
                    "portfolio fit is insufficient."
                ),
            )

        if not evidence.actionable_now:
            return (
                DecisionState.PREPARE,
                (
                    "The investment case is ready, but its execution "
                    "trigger has not occurred."
                ),
            )

        return (
            DecisionState.RECOMMEND,
            (
                "The investment case satisfies quality, evidence, "
                "valuation, risk, and portfolio gates."
            ),
        )

    @staticmethod
    def _unassessable_quality(
        evidence: DecisionEvidence,
    ) -> str:
        """
        Why quality is missing: not yet read, or not a question that applies.

        "Business quality has not been measured" promises a measurement that
        is coming. For a cryptocurrency none is: there is no business to
        assess and no earnings to price it against, so the case would sit at
        INVESTIGATE forever while the wording implied otherwise. The limit
        is this platform's, and it is stated as this platform's.
        """

        asset_class = evidence.asset_class

        if asset_class is not None and asset_class.has_no_company:
            return (
                f"A {asset_class.noun} has no business quality or valuation to "
                "assess, and this platform judges an investment case on "
                "both. Its measured risk and portfolio fit are reported, "
                "but no recommendation rests on them alone."
            )

        return (
            "Business quality has not been measured, so the case cannot "
            "progress beyond research."
        )

    @staticmethod
    def _unassessable_valuation(
        evidence: DecisionEvidence,
    ) -> str:
        """
        Why valuation is missing: not yet read, or nothing to read it from.

        A token has no earnings, so there is no price/earnings ratio to be
        cheap or expensive on. Its scale, liquidity, issuance and age are
        assessable and now assessed; what it is worth is not, and saying
        the measurement is pending would promise one that cannot come.
        """

        asset_class = evidence.asset_class

        if asset_class is not None and asset_class.has_no_company:
            return (
                f"A {asset_class.noun} has no earnings to be valued "
                "against, so this platform cannot judge what it is worth. "
                "No recommendation is made without that."
            )

        return (
            "The case is credible, but valuation has not been measured, "
            "so no recommendation can rest on it."
        )

    @staticmethod
    def _calculate_conviction(
        evidence: DecisionEvidence,
        state: DecisionState,
    ) -> int:
        """
        Average the scores that exist.

        An unmeasured score is left out rather than counted as zero or
        filled in. The state reached already caps conviction, and a case
        resting on fewer measurements cannot reach the higher states.
        """

        measured = [
            score
            for score in (
                evidence.quality_score,
                evidence.evidence_score,
                evidence.valuation_score,
                evidence.portfolio_fit_score,
                None if evidence.risk_score is None else 100 - evidence.risk_score,
            )
            if score is not None
        ]

        conviction = round(sum(measured) / len(measured)) if measured else 0

        limits = {
            DecisionState.REJECT: 40,
            DecisionState.MONITOR: 55,
            DecisionState.INVESTIGATE: 70,
            DecisionState.PREPARE: 85,
            DecisionState.RECOMMEND: 100,
        }

        return min(conviction, limits[state])


ExecutiveDecisionEngine = ArtificialCIO
