from dataclasses import dataclass

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
from app.domain.decision_blocker import BlockerKind, DecisionBlocker
from app.domain.decision_rules import CONVICTION_MEAN, DECISION_GATES
from app.domain.finding import Dimension, Sense

#: The score families `conviction-mean@1` averages, in the order it
#: reads them, each named as the investor would recognise it.
#:
#: Named because a count is only checkable against an expectation: *the
#: mean of the 5 scores measured* is a claim that five families spoke,
#: and where four did it was false. The tuple is the expectation, its
#: length is the denominator, and a family absent from a decision is
#: named rather than quietly dropped out of the numerator.
SCORE_FAMILIES = (
    "business quality",
    "evidence",
    "valuation",
    "portfolio fit",
    "safety",
)


@dataclass(frozen=True, slots=True)
class ScoreParticipation:
    """Which score families spoke for one decision, and which did not.

    Derived from the decision's own evidence, never supplied beside it:
    the scores, how many families were expected, and the names of the
    ones that produced nothing. The conviction sentence is worded from
    this and from nothing else, so it cannot state a count the evidence
    does not support.
    """

    scores: tuple[int, ...]
    expected: int
    absent: tuple[str, ...]

    @property
    def participating(self) -> int:
        return len(self.scores)

    @property
    def complete(self) -> bool:
        return self.participating == self.expected


class ArtificialCIO:
    """Executive brain responsible for investment-case decisions."""

    #: The state caps of `conviction-mean@1`. Named so the provenance
    #: guard can fingerprint them: a cap cannot move under an unchanged
    #: rule version without a test failing.
    CONVICTION_LIMITS = {
        DecisionState.REJECT: 40,
        DecisionState.MONITOR: 55,
        DecisionState.INVESTIGATE: 70,
        DecisionState.PREPARE: 85,
        DecisionState.RECOMMEND: 100,
    }

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
        state, rationale, blocker = self._determine_state(evidence)

        conviction = self._calculate_conviction(evidence, state)

        # One reading of the evidence, worded and carried. A sentence
        # that states a count and a decision that carries a different
        # one would be two answers to one question.
        participation = self._participation(evidence)

        return ExecutiveDecision(
            symbol=evidence.symbol,
            state=state,
            conviction=conviction,
            conviction_basis=self._conviction_basis(evidence, state, conviction),
            conviction_participating=participation.participating,
            conviction_expected=participation.expected,
            conviction_absent_families=participation.absent,
            rationale=rationale,
            # What stopped it, from the branch that stopped it. Nothing
            # re-reads the state to work this out: the cascade already
            # knows, and this is that knowledge kept rather than thrown
            # away and guessed at by a surface.
            blocker=blocker,
            evidence_as_of=evidence.evidence_as_of,
            evidence_weighed=evidence.evidence_weighed,
            key_strengths=evidence.strengths,
            key_risks=evidence.risks,
            # Carried through untouched. The CIO gates on scores; it
            # neither reads a committee's position nor edits one, and
            # preserving them here is what lets the synthesis show an
            # investor which committee dissented from what was decided.
            findings=evidence.findings,
            opinions=evidence.opinions,
            context_risks=evidence.context_risks,
            missing_evidence=evidence.missing_evidence,
            catalysts=evidence.catalysts,
            next_trigger=evidence.next_trigger,
            # The rules this decision was reached under. Stamped where
            # the deciding happens; the score rules already ride on the
            # evidence's own bases.
            decided_under=(DECISION_GATES, CONVICTION_MEAN),
        )

    def _determine_state(
        self,
        evidence: DecisionEvidence,
    ) -> tuple[DecisionState, str, DecisionBlocker]:
        """The gate that decides, and the same gate's account of itself.

        Every rationale below is unchanged, to the byte. What is added
        is the third member: the branch names the blocker it *is*,
        because it is the only place that knows. A surface reading a
        state string back into a cause would be guessing — REJECT is
        reached three different ways here, and two of them say nothing
        about the business.
        """

        policy = self._policy

        if evidence.hard_reject:
            return (
                DecisionState.REJECT,
                "The investment case violates a hard policy gate.",
                self._blocked(
                    evidence,
                    BlockerKind.POLICY_GATE,
                    "Refused outright by a hard policy gate.",
                ),
            )

        # **A company vote no longer rejects a thesis *here*.** The
        # owner's ruling of 2026-08-24 removed the transition that
        # lived at this line — `analyst_veto -> REJECT`, set from the
        # value/quality/momentum vote reaching SELL — because a
        # one-session provider price move decided it. AMD was REJECTed
        # on a -4.28% day while its own analysts read growth,
        # profitability, balance sheet and cash flow as strong or
        # better, and the blocker called that "a specialist analyst's
        # veto" when no analyst had spoken.
        #
        # This is the volatility ruling of 2026-08-21 applied to the
        # same question one layer up: market behaviour may inform risk,
        # timing and eventual sizing, and may not become a judgment
        # about business quality.
        #
        # **Stated exactly, because the weaker claim is the true one:**
        # The company vote's SELL and BUY directions no longer
        # directly reject or authorize a case. Its confidence remains
        # decision-bearing through `evidence_score`; that residual
        # changes one live blocker, can reach a state threshold, and is
        # **not** accepted as the final contract.
        #
        # So value, quality and momentum are still measured, banded,
        # shown and scored into conviction — and they no longer stop a
        # case *through the deleted direct branches*. They remain
        # capable of affecting the evidence gates below through Path C,
        # which this ruling did not touch.

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
                self._blocked(
                    evidence,
                    BlockerKind.MISSING_EVIDENCE,
                    (
                        f"Nothing about {evidence.symbol} itself has been "
                        "read, so there is nothing yet to judge."
                    ),
                ),
            )

        # **Historical volatility no longer rejects a thesis.** The owner's
        # ruling of 2026-08-21 removed the one transition that lived here —
        # `risk_score > maximum_acceptable_risk → REJECT`, against the
        # policy's former threshold of 70, a field since deleted as dead —
        # because a security's own price record is a statement about how
        # violently it has moved, not about whether the investment case is
        # sound.
        # AMD was REJECTed on 71.8% annualised volatility while its own
        # analysts read growth, profitability, balance sheet and cash flow
        # as strong or better.
        #
        # Nothing about risk was weakened. Volatility, drawdown, the band,
        # the severity and the findings are all still measured, still
        # displayed, and still scored as safety into conviction — and the
        # constraint volatility now carries is the Capital Action
        # Envelope's security-risk ceiling (#236), which bounds how much
        # of the portfolio a violent security may occupy rather than
        # whether it may be considered at all. A cap on size is the honest
        # form of that measurement; a veto on the thesis was not.
        #
        # What remains here is the *unmeasured* risk gate, further down:
        # no recommendation rests on a risk that was never read. Not
        # knowing something is not the same as knowing it is bad, and it
        # is still a reason not to progress.

        if (
            evidence.quality_score is not None
            and evidence.quality_score < policy.minimum_watchlist_quality
        ):
            return (
                DecisionState.REJECT,
                ("Business quality is insufficient to justify continued monitoring."),
                self._blocked(
                    evidence,
                    BlockerKind.QUALITY_GATE,
                    (
                        f"Blocked by the quality floor: business quality "
                        f"scores {evidence.quality_score} against a minimum "
                        f"of {policy.minimum_watchlist_quality}."
                    ),
                ),
            )

        if evidence.evidence_score < policy.minimum_investigation_evidence:
            return (
                DecisionState.MONITOR,
                (
                    "The opportunity is relevant, but available "
                    "evidence is still limited."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.MISSING_EVIDENCE,
                    (
                        f"Blocked by how little has been read: evidence "
                        f"scores {evidence.evidence_score} against the "
                        f"{policy.minimum_investigation_evidence} research "
                        "needs."
                    ),
                ),
            )

        if evidence.quality_score is None:
            return (
                DecisionState.INVESTIGATE,
                self._unassessable_quality(evidence),
                self._blocked(
                    evidence,
                    BlockerKind.QUALITY_GATE,
                    self._unassessable_quality(evidence),
                ),
            )

        if (
            evidence.quality_score < policy.minimum_prepare_quality
            or evidence.evidence_score < policy.minimum_prepare_evidence
        ):
            # A disjunction, and the blocker names the side that fired.
            # Both can be true at once; quality is named first because
            # it is the one that is a statement about the company, and
            # a reader shown only "not enough read" would be told the
            # smaller half of the truth.
            quality_short = evidence.quality_score < policy.minimum_prepare_quality

            return (
                DecisionState.INVESTIGATE,
                (
                    "The opportunity merits deeper research before "
                    "a thesis can be prepared."
                ),
                self._blocked(
                    evidence,
                    (
                        BlockerKind.QUALITY_GATE
                        if quality_short
                        else BlockerKind.MISSING_EVIDENCE
                    ),
                    (
                        (
                            f"Blocked short of a thesis: business quality "
                            f"scores {evidence.quality_score} against the "
                            f"{policy.minimum_prepare_quality} preparing one "
                            "needs."
                        )
                        if quality_short
                        else (
                            f"Blocked short of a thesis: evidence scores "
                            f"{evidence.evidence_score} against the "
                            f"{policy.minimum_prepare_evidence} preparing one "
                            "needs."
                        )
                    ),
                ),
            )

        if evidence.quality_score < policy.minimum_recommendation_quality:
            return (
                DecisionState.PREPARE,
                (
                    "The investment case is credible, but quality "
                    "conviction is not yet sufficient."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.QUALITY_GATE,
                    (
                        f"Blocked short of a recommendation: business quality "
                        f"scores {evidence.quality_score} against the "
                        f"{policy.minimum_recommendation_quality} one needs."
                    ),
                ),
            )

        if evidence.evidence_score < policy.minimum_recommendation_evidence:
            return (
                DecisionState.PREPARE,
                (
                    "The thesis is promising, but recommendation-level "
                    "evidence is incomplete."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.MISSING_EVIDENCE,
                    (
                        f"Blocked short of a recommendation: evidence scores "
                        f"{evidence.evidence_score} against the "
                        f"{policy.minimum_recommendation_evidence} one needs."
                    ),
                ),
            )

        if evidence.valuation_score is None:
            return (
                DecisionState.PREPARE,
                self._unassessable_valuation(evidence),
                self._blocked(
                    evidence,
                    BlockerKind.VALUATION_GATE,
                    # The fund and token wording is already exact — a
                    # platform limit, not a pending measurement — and
                    # stays. For a company, the investor's sentence: what
                    # the evidence cannot yet establish, not which score
                    # is missing.
                    self._unassessable_valuation(evidence)
                    if evidence.asset_class is not None
                    and evidence.asset_class.has_no_company
                    else (
                        "The available evidence does not establish whether "
                        "the shares offer good value at today's price, so "
                        "valuation cannot yet support a purchase."
                    ),
                ),
            )

        if evidence.risk_score is None:
            return (
                DecisionState.PREPARE,
                (
                    "The case is credible, but risk has not been measured, "
                    "and no recommendation is made without it."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.RISK_GATE,
                    (
                        "Blocked by an unmeasured risk: this security's own "
                        "price record was not read, and no recommendation "
                        "rests on an unmeasured risk."
                    ),
                ),
            )

        if evidence.valuation_score < policy.minimum_recommendation_valuation:
            return (
                DecisionState.PREPARE,
                (
                    "The company is attractive, but valuation does not "
                    "currently support action."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.VALUATION_GATE,
                    # The owner's product feedback of 2026-08-24: "scores
                    # 55 against the 60 a recommendation needs" is not
                    # investor language. The sentence now names what was
                    # measured and what it means for the course; the
                    # score itself stays on the payload and in the score
                    # basis as audit detail, and the gate above read it
                    # unchanged.
                    self._short_valuation(evidence),
                ),
            )

        if evidence.portfolio_fit_score is None:
            return (
                DecisionState.PREPARE,
                (
                    "The case is credible, but how it would fit the "
                    "portfolio has not been measured."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.PORTFOLIO_FIT_GATE,
                    (
                        "Blocked by an unmeasured fit: how this security "
                        "would sit in this account was not measured."
                    ),
                ),
            )

        if evidence.portfolio_fit_score < policy.minimum_portfolio_fit:
            return (
                DecisionState.PREPARE,
                (
                    "The thesis is actionable in isolation, but "
                    "portfolio fit is insufficient."
                ),
                self._blocked(
                    evidence,
                    BlockerKind.PORTFOLIO_FIT_GATE,
                    (
                        f"Blocked by how it would sit in this account: "
                        f"portfolio fit scores {evidence.portfolio_fit_score} "
                        f"against a minimum of {policy.minimum_portfolio_fit}."
                    ),
                ),
            )

        # **And a company vote no longer authorizes one here either.**
        # The final gate at this line read `actionable_now`, which was
        # the same vote reaching BUY — so a positive one-session move
        # was the last thing standing between PREPARE and RECOMMEND.
        # Measured over the live book, that flag was decided by the
        # day's price band for four securities. Removed with its
        # sibling, and **not replaced**: no technical-analysis trigger
        # is introduced here.
        #
        # A case that satisfies quality, evidence, valuation, risk and
        # portfolio fit is recommended on those alone — noting that the
        # evidence gate above still carries the vote's magnitude
        # through Path C, which is a residual and not a settled
        # contract.

        return (
            DecisionState.RECOMMEND,
            (
                "The investment case satisfies quality, evidence, "
                "valuation, risk, and portfolio gates."
            ),
            DecisionBlocker.none(),
        )

    @staticmethod
    def _blocked(
        evidence: DecisionEvidence,
        kind: BlockerKind,
        stated: str,
    ) -> DecisionBlocker:
        """One blocker, carrying what survives it.

        `despite` is the fundamental analysts' own favourable verdicts,
        selected by *kind of finding* and never by strength — the ledger
        states outright that its order is not a ranking, so picking "the
        strongest" would publish an ordering nobody measured. Where the
        gate is itself about the business the blocker drops them, since
        quoting an analyst against a quality ruling would argue with the
        decision rather than qualify it.
        """

        return DecisionBlocker.of(
            kind,
            stated,
            evidence.symbol,
            despite=tuple(
                finding.statement
                for finding in evidence.findings
                if finding.sense is Sense.FAVOURABLE
                and finding.dimension is Dimension.RESEARCH
            ),
        )

    @classmethod
    def _conviction_basis(
        cls,
        evidence: DecisionEvidence,
        state: DecisionState,
        conviction: int | None,
    ) -> str:
        """What the number is, so it cannot be read as enthusiasm.

        AMD's 40 is the REJECT cap of `conviction-mean@1` and not a mean
        that happened to land on 40. Printed alone the two are the same
        digits, and only one of them is a measurement of anything.

        **A count is stated against its expectation, never alone.** *The
        mean of the 5 scores measured* was five families' verdict where
        five spoke and a false claim where four did — the reader has no
        way to tell which, because the sentence never said how many were
        asked. Every count here is `n of m` from one reading of the
        evidence, and the families that produced nothing are named:
        their absence is a limit on what the number covers, and it is
        not a low score for them. The arithmetic is untouched by this
        wording — #232's ruling reserves that for its own slice.
        """

        cap = cls.CONVICTION_LIMITS[state]

        if conviction is None:
            return (
                "No conviction is stated: this case cites no supporting "
                "reason, and an average over the account's own numbers is "
                "not confidence in a security."
            )

        participation = cls._participation(evidence)

        capped = (
            f"capped at {cap} by the {state.value} state"
            if conviction == cap
            else f"where the {state.value} state caps it at {cap}"
        )

        coverage = (
            ""
            if participation.complete
            else (
                " No "
                f"{cls._and(participation.absent)} score participated, so it "
                "covers less than a complete reading — an absent score is "
                "missing, not poor."
            )
        )

        return (
            "A decision score, not enthusiasm: computed from "
            f"{participation.participating} of {participation.expected} score "
            f"families under conviction-mean@1, {capped}.{coverage}"
        )

    @staticmethod
    def _and(names: tuple[str, ...]) -> str:
        """Name every absent family, joined as a reader would say them.

        Written as a slice rather than a length comparison on purpose:
        this module is governed by the anonymous-threshold guard, and a
        bare number in a comparison here is indistinguishable from a
        threshold whether or not it is one.
        """

        if not names[1:]:
            return names[0]

        return f"{', '.join(names[:-1])} or {names[-1]}"

    @staticmethod
    def _unassessable_quality(
        evidence: DecisionEvidence,
    ) -> str:
        """
        Why quality is missing: not yet read, read and inconclusive, or moot.

        "Business quality has not been measured" promises a measurement that
        is coming. For a cryptocurrency none is: there is no business to
        assess and no earnings to price it against, so the case would sit at
        INVESTIGATE forever while the wording implied otherwise. The limit
        is this platform's, and it is stated as this platform's.

        And it is equally false the other way. A company whose statements
        reached quorum *was* measured — the reading simply could not
        conclude, because too few of the questions its financial model asks
        could be answered from established figures. Saying that reading
        never happened denies evidence the same page displays, and it sends
        the investor to acquire something already held. The assessment's own
        arithmetic is quoted rather than summarised, so the sentence cannot
        drift from the object the score came from.
        """

        asset_class = evidence.asset_class

        if asset_class is not None and asset_class.has_no_company:
            return (
                f"A {asset_class.noun} has no business quality or valuation to "
                "assess, and this platform judges an investment case on "
                "both. Its measured risk and portfolio fit are reported, "
                "but no recommendation rests on them alone."
            )

        grounded = evidence.grounded_quality

        if grounded is not None:
            return (
                f"Business quality was assessed from {grounded.source} and "
                "could not be concluded, so the case cannot progress beyond "
                f"research. {grounded.stated()}"
            )

        return (
            "Business quality has not been measured, so the case cannot "
            "progress beyond research."
        )

    @staticmethod
    def _short_valuation(evidence: DecisionEvidence) -> str:
        """Why the price does not support action, in the investor's terms.

        Composed deterministically from the typed valuation reading the
        evidence already carries — the band, the measured multiple and
        nothing else. Four rules, each load-bearing (the owner's ruling
        on #251):

        - **The score is not the explanation.** It stays on the payload
          and in the score basis as audit detail; the sentence a reader
          acts on names what was measured instead.
        - **"Expensive" is never claimed, and neither is a margin of
          safety.** This platform holds one unaudited multiple and no
          benchmark (VALUATION_AUTHORITY.md) — no intrinsic value,
          expected return or margin of safety was measured, so none may
          be said to be missing.
        - **A poor valuation is not a poor business.** The sentence says
          so itself, and the blocker's `does_not_say` says it again.
        - **The reconsideration condition is the gate's own input.**
          Only the forward P/E moving into a cheaper band can change
          this ruling, so that is what the reader is told to wait for —
          never "stronger earnings and cash-flow evidence", which does
          not feed this gate and does not necessarily move the
          multiple. No target price, and no promise that crossing the
          band produces a recommendation: reconsidering is what is
          offered.
        """

        reading = evidence.valuation_reading
        observation = reading.observation if reading is not None else None

        if reading is None or observation is None:
            # The score exists and the reading behind it was not
            # carried — a caller-built evidence, never the live
            # pipeline. Nothing quotable, so nothing is quoted.
            return (
                "The available evidence does not establish that the "
                "shares offer good value at today's price, so valuation "
                "cannot support a purchase."
            )

        # "20.6× forward earnings" for the one metric that decides
        # pe-bands@2; the observation's own label for anything else, so
        # a future metric is named rather than misdescribed.
        measured = (
            f"{observation.value:.1f}\u00d7 forward earnings"
            if observation.metric == "forward_pe"
            else f"a {observation.label} of {observation.value:.1f}{observation.unit}"
        )

        house_rule = (
            "This is a house rule applied to one measured multiple, not "
            "a market comparison or a judgment on the business."
        )

        if reading.valuation == "EXPENSIVE":
            return (
                f"At {measured}, {evidence.symbol} sits above the "
                "valuation range this platform accepts for a buy "
                f"recommendation. {house_rule} Wait for the forward P/E "
                "to move into a more attractive band before "
                "reconsidering a purchase."
            )

        if reading.valuation == "FAIR":
            return (
                f"At {measured}, {evidence.symbol} sits in this "
                "platform's middle valuation band: not overpriced, but "
                "not cheap enough to support a buy recommendation. "
                f"{house_rule} Wait for the forward P/E to move into "
                "the cheaper band before reconsidering a purchase."
            )

        # A band this composer has no honest sentence for — CHEAP
        # blocked by a custom policy bar, or a vocabulary this code
        # predates. The measured fact is named; no band is claimed, and
        # the reconsideration condition stays the gate's own input.
        return (
            f"At {measured}, the price does not clear the bar this "
            f"policy sets for a buy recommendation. {house_rule} Wait "
            "for the measured multiple to move into a band this policy "
            "accepts before reconsidering a purchase."
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
    ) -> int | None:
        """
        Average the scores that exist, all pointing the same way.

        An unmeasured score is left out rather than counted as zero or
        filled in. The state reached already caps conviction, and a case
        resting on fewer measurements cannot reach the higher states.

        Risk enters as safety, because an average is only meaningful over
        scores that agree on which direction is good. That inversion used
        to be written here, in the one place that happened to need it;
        it is now `DecisionEvidence.safety_score`, and every surface shows
        the same number this arithmetic uses.

        **A conviction requires something to be convinced by.** Where the
        case cites no supporting reason the number is withheld, not
        defaulted: an average over portfolio fit and an evidence-coverage
        discount is arithmetic about the account and the reading, and
        printing it beside an empty `because` presents it as confidence in
        a security nobody argued for. Four holdings each showed 64 that
        way — two of them from a two-term mean and two from a three-term
        one, agreeing by coincidence rather than by measurement.

        The arithmetic itself is untouched. Only its licence to speak is.
        """

        if not evidence.strengths:
            return None

        measured = ArtificialCIO._measured_scores(evidence)

        if not measured:
            return None

        conviction = round(sum(measured) / len(measured))

        return min(conviction, ArtificialCIO.CONVICTION_LIMITS[state])

    @staticmethod
    def _measured_scores(evidence: DecisionEvidence) -> tuple[int, ...]:
        """The scores that exist, all running the same way.

        Kept as the arithmetic's own door — `conviction-mean@1` averages
        exactly these — while `_participation` answers the separate
        question of what was expected and what did not arrive. The
        arithmetic is untouched by this slice; only what may be said
        about it is.
        """

        return ArtificialCIO._participation(evidence).scores

    @staticmethod
    def _participation(evidence: DecisionEvidence) -> ScoreParticipation:
        """Which families spoke, how many were expected, which are absent.

        One reading of the evidence produces all three, so a sentence
        can never state a count the same evidence would not produce.
        The pairing is positional against `SCORE_FAMILIES` and the test
        pins the order — a family renamed without its score moving
        would otherwise attribute an absence to the wrong one.
        """

        readings = (
            evidence.quality_score,
            evidence.evidence_score,
            evidence.valuation_score,
            evidence.portfolio_fit_score,
            evidence.safety_score,
        )

        return ScoreParticipation(
            scores=tuple(score for score in readings if score is not None),
            expected=len(SCORE_FAMILIES),
            absent=tuple(
                family
                for family, score in zip(SCORE_FAMILIES, readings, strict=True)
                if score is None
            ),
        )


ExecutiveDecisionEngine = ArtificialCIO
