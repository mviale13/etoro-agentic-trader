"""Build Executive DecisionEvidence from the cognitive layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.executive.portfolio_fit import (
    PortfolioFit,
    PortfolioFitMeasure,
)
from app.brain import Brain
from app.domain.asset_class import AssetClass
from app.domain.business_quality import BAND_SCORES, BusinessQuality
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_research import CompanyResearch
from app.domain.decision_rules import (
    COGNITIVE_CONFIDENCE,
    EVIDENCE_SCORE,
    PE_BANDS,
    PORTFOLIO_FIT,
    PROVIDER_QUALITY,
    QUALITY_GROUNDED,
    RISK_BANDS,
    RISK_SEVERITY,
)
from app.domain.decision_rules import (
    VALUATION_SCORES as VALUATION_SCORES_RULE,
)
from app.domain.executive_decision import DecisionEvidence
from app.domain.financial_understanding import FinancialEvidenceStanding
from app.domain.finding import (
    Dimension,
    Finding,
    FindingLedger,
    Sense,
    statements,
    statements_where,
)
from app.domain.opinion import Opinion
from app.domain.research_plan import AnalystKey
from app.domain.risk_signal import RiskSignal
from app.domain.score_basis import (
    Contribution,
    ScoreBases,
    ScoreBasis,
    ScoreDerivation,
    ScoreKind,
)
from app.services.quality_signal_service import QualitySignalService


@dataclass(slots=True)
class DecisionEvidenceBuilder:
    """
    Translate cognitive outputs into Executive DecisionEvidence.

    The symbol belongs to the investment case being evaluated,
    not to the portfolio snapshot.

    Portfolio reasoning describes the account as a whole and is therefore
    identical for every holding. Per-security evidence, when the Brain holds
    any, is what distinguishes one investment case from another. Where it is
    missing the evidence says so, rather than letting portfolio-level scores
    stand in for security-level judgement.
    """

    # Signal bands are aligned to DecisionPolicy's own gates so a qualitative
    # signal lands in the band it describes:
    #   below 35 -> rejected, 60 -> may prepare, 75 -> may recommend.
    #
    # LOW quality sits above the rejection floor deliberately: the security
    # committee rates such holdings HOLD, and the Artificial CIO must not
    # reject an investment case its own committee is content to hold.
    #
    # **And no *direction* of that committee rejects or authorizes one
    # either.** The company value/quality/momentum vote once mapped SELL
    # to an analyst veto and BUY to the execution trigger; the owner's
    # ruling of 2026-08-24 removed both, because a one-session provider
    # price move decided them.
    #
    # **The vote is not therefore descriptive.** Its *direction* is;
    # its *magnitude* is not. `_evidence_score` below still averages
    # the company vote's confidence into `evidence_score`, and that
    # confidence is `50 + |score| * 50` — it rises with how far the
    # vote is from neutral, in either direction. AMD's evidence score
    # went 71 to 83 on the day its price fell 4.28%.
    #
    # Said exactly: the company vote's SELL and BUY directions no
    # longer directly reject or authorize a case. Its confidence
    # remains decision-bearing through `evidence_score`; that residual
    # changes one live blocker, can reach a state threshold, and is
    # **not** accepted as the final contract. See
    # `docs/architecture/COMPANY_VOTE_DECISION_AUTHORITY.md`.

    portfolio_fit: PortfolioFit = field(default_factory=PortfolioFit)

    #: Quality of the security itself, by signal.
    QUALITY_SCORES = {
        "HIGH": 80,
        "MEDIUM": 62,
        "LOW": 40,
    }

    #: The `evidence-score@1` discount for a case standing on the
    #: account rather than on the security. Named so the provenance
    #: guard can fingerprint it.
    UNEVIDENCED_DISCOUNT = 0.6

    #: Attractiveness of the price paid, by signal.
    VALUATION_SCORES = {
        "CHEAP": 80,
        "FAIR": 55,
        "EXPENSIVE": 25,
    }

    def ledger(
        self,
        symbol: str,
        brain: Brain,
        today: date | None = None,
    ) -> FindingLedger:
        """Every finding read about this security, each one addressable.

        Built before the committees run, because a committee states its
        position by *reference* into this ledger and cannot compose one
        against a list that does not exist yet. The evidence builder
        owns it because the evidence builder is where the findings were
        already being gathered — this only stops them being flattened
        into strings on the way out.
        """

        company = brain.security_evidence(symbol)

        return FindingLedger.of(
            self._company_findings(
                company,
                today if today is not None else datetime.now(UTC).date(),
            )
        )

    def build(
        self,
        symbol: str,
        brain: Brain,
        reasoning: ReasoningSnapshot,
        committee_opinions: tuple[CommitteeOpinion, ...],
        findings: FindingLedger | None = None,
        today: date | None = None,
        quality_assessment: BusinessQuality | None = None,
        financial_standing: FinancialEvidenceStanding = (
            FinancialEvidenceStanding.NEVER_READ
        ),
        financial_absent_because: str | None = None,
    ) -> DecisionEvidence:
        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        company = brain.security_evidence(symbol)

        # Scheduling is measured against a day, and the day is read once
        # here so every sentence in this case counts from the same one.
        # A caller that already built the ledger passes its own day in,
        # so the ledger the committees pointed at and the evidence built
        # beside it cannot straddle midnight and disagree.
        today = today if today is not None else datetime.now(UTC).date()

        quality = self._quality_value(company, quality_assessment, financial_standing)

        cognitive_confidence = (
            portfolio.confidence + market.confidence + risk.confidence
        ) / 3.0

        evidence_score = self._evidence_score(company, cognitive_confidence)

        valuation = self._valuation_score(company)

        # Measured about this security and this account together. The
        # OpportunityAnalyst's number described only the account, so it was
        # the same for every candidate and could never say whether one of
        # them fitted better than another.
        asset_class = brain.asset_class_for(symbol)

        portfolio_fit = self.portfolio_fit.measure(
            symbol,
            brain.portfolio,
            brain.investment_policy,
            asset_class,
        )

        # Everything read about this security, each finding carrying the
        # sense the signal read it with. The full list is the record; the
        # split below is what an investment case can honestly state.
        #
        # The portfolio's strengths and the market's opportunities are not
        # in here. They are identical for every symbol, so they told the
        # reader nothing about the one in front of them. They are still
        # weighed — as scores, and as the context the case is set in — but
        # they are not evidence about a security.
        ledger = findings if findings is not None else self.ledger(symbol, brain, today)

        weighed = ledger.findings

        evidence_weighed = statements(weighed)

        strengths = statements_where(weighed, Sense.FAVOURABLE)

        risks = statements_where(weighed, Sense.ADVERSE)

        context_risks = tuple(
            dict.fromkeys(
                (
                    *portfolio.weaknesses,
                    *market.risks,
                    *risk.risk_factors,
                    # Behavioural biases are risks to the decision, not to the
                    # security: acting against your own policy is a way to
                    # lose money regardless of what the asset does.
                    *reasoning.behavior.observed_biases,
                    *reasoning.opportunity.constraints,
                )
            )
        )

        catalysts = self._catalysts(company, today)

        return DecisionEvidence(
            symbol=symbol,
            quality_score=quality,
            evidence_score=evidence_score,
            valuation_score=valuation,
            risk_score=self._risk_score(company),
            # The reading the score above was banded from, carried whole.
            # The gate reads the score and only the score; the refusal
            # names the volatility, and neither can drift from the other
            # because both come off this one object.
            risk_reading=company.signals.risk if company is not None else None,
            portfolio_fit_score=portfolio_fit.score,
            # Each score's own reasoning, worded where the score is
            # computed. A band is this platform's policy, not a
            # measurement, and a reader who cannot see it cannot tell the
            # two apart.
            score_bases=ScoreBases(
                quality=self._quality_basis(
                    company,
                    quality_assessment,
                    financial_standing,
                    financial_absent_because,
                ),
                evidence=self._evidence_basis(
                    company,
                    reasoning,
                    cognitive_confidence,
                ),
                valuation=self._valuation_basis(company),
                safety=self._safety_basis(company),
                portfolio_fit=self._portfolio_fit_basis(portfolio_fit),
            ),
            evidence_as_of=company.reading if company is not None else None,
            # A known security always leaves a recommendation here, even an
            # unpriceable one; nothing at all means the symbol named nothing
            # the platform could gather evidence about.
            #
            # A quorate grounded assessment is security-level evidence too,
            # and read from a stronger source than the provider strip. This
            # tested the provider half alone, so a company the platform had
            # read a 10-K for was reported as one it held nothing about —
            # and the decision said so on the page printing the band.
            security_evidenced=company is not None or quality_assessment is not None,
            # The assessment itself, not its conclusion. Every sentence
            # about quality below and downstream is worded from this one
            # object, which is the same object the score above came from.
            grounded_quality=quality_assessment,
            asset_class=asset_class,
            hard_reject=False,
            evidence_weighed=evidence_weighed,
            strengths=strengths,
            risks=risks,
            # The same findings, unflattened, plus the positions the
            # committees took over them. Carried so the decision can
            # preserve both and the synthesis can name which committee
            # each part of its reasoning came from.
            findings=ledger,
            opinions=committee_opinions,
            context_risks=context_risks,
            missing_evidence=self._missing_evidence(
                company,
                symbol,
                asset_class,
                quality_assessment,
            ),
            catalysts=catalysts,
        )

    @classmethod
    def _quality_value(
        cls,
        company: CompanyRecommendation | None,
        grounded: BusinessQuality | None,
        standing: FinancialEvidenceStanding = FinancialEvidenceStanding.NEVER_READ,
    ) -> int | None:
        """How good the business is, from the filing where it was read.

        The two routes never blend. A grounded assessment governs
        outright where the statements support one — including when it
        bands `UNKNOWN`, which is a real answer meaning *too little was
        established to say*, and must not fall through to a provider's
        three proxies. Falling back there would let a company the
        filing could not describe borrow a score from its market
        capitalisation.

        **And a withdrawal is not an absence.** Where every reading of
        every statement this platform holds was withdrawn by an audit,
        there is no grounded object at all — so the guarantee above,
        written about an `UNKNOWN` *band*, did not reach the case and the
        provider route re-opened underneath it. That is the same defect
        the band rule exists to prevent, arriving through the one door
        the band cannot cover: not *too little was established to say*
        but *what was established has been taken away*. It is refused
        here, and refused on the member rather than on the sentence.
        """

        if grounded is not None:
            return grounded.score

        if standing is FinancialEvidenceStanding.WITHDRAWN_BY_AUDIT:
            return None

        return cls._quality_score(company)

    @classmethod
    def _quality_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How good the business is, or nothing at all.

        This used to fall back to the portfolio's health score, so a company
        nobody could describe was scored with a number measured from the
        investor's account. Four unrelated companies would report the same
        quality, and that number moved their ranking.
        """

        if company is None:
            return None

        return cls.QUALITY_SCORES.get(company.signals.quality.quality)

    @classmethod
    def _risk_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How risky this security is, measured from its own price history.

        This used to be the portfolio's risk score, which was identical for
        every security and, before that, mostly two hardcoded constants. It
        is now the security's own volatility and drawdown, or nothing.
        """

        if company is None or company.signals.risk is None:
            return None

        severity = company.signals.risk.severity

        return None if severity is None else round(severity * 100)

    @classmethod
    def _valuation_score(
        cls,
        company: CompanyRecommendation | None,
    ) -> int | None:
        """
        How attractive the price is, or nothing at all.

        The fallback here was market momentum, which says nothing about
        whether this company is cheap.
        """

        if company is None:
            return None

        return cls.VALUATION_SCORES.get(company.signals.value.valuation)

    @classmethod
    def _evidence_score(
        cls,
        company: CompanyRecommendation | None,
        cognitive_confidence: float,
    ) -> int:
        """
        How well evidenced this specific case is.

        Without security-level evidence the case rests on portfolio context
        alone, which is weaker ground for a single-name decision.
        """

        cognitive = int(cognitive_confidence * 100)

        if company is None:
            return int(cognitive * cls.UNEVIDENCED_DISCOUNT)

        return int((cognitive + company.confidence) / 2)

    # ── Why each score is the number it is ──────────────────────────
    #
    # Every basis below asks the method above for the number rather than
    # reading the band a second time. Two readings of one band is how a
    # dashboard comes to explain a score it does not have.

    @staticmethod
    def _banded(scores: dict[str, int]) -> str:
        """The whole scale, as a sentence, so the reader sees the ruler."""

        bands = [f"{name} at {value}" for name, value in scores.items()]

        if len(bands) < 2:
            return "".join(bands)

        return f"{', '.join(bands[:-1])} and {bands[-1]}"

    @staticmethod
    def _safety_bands() -> dict[str, int]:
        """
        The risk bands as safety, on the scale the score is reported on.

        Read from the signal's own severities rather than restated here,
        so the scale a reader is shown is the scale the score came off —
        turned once, the same way `DecisionEvidence.safety_score` turns
        the number itself.
        """

        return {
            level: 100 - round(severity * 100)
            for level, severity in RiskSignal.SEVERITIES.items()
        }

    @classmethod
    def _quality_basis(
        cls,
        company: CompanyRecommendation | None,
        grounded: BusinessQuality | None = None,
        standing: FinancialEvidenceStanding = FinancialEvidenceStanding.NEVER_READ,
        absent_because: str | None = None,
    ) -> ScoreBasis:
        """How good the business is, and by whose ruler."""

        if grounded is not None:
            return cls._grounded_quality_basis(grounded)

        if standing is FinancialEvidenceStanding.WITHDRAWN_BY_AUDIT:
            return cls._withdrawn_quality_basis(absent_because)

        if company is None:
            return ScoreBasis(
                basis=(
                    "No security-level analysis was gathered, so business "
                    "quality was not scored. It is never filled in from the "
                    "account's own health."
                ),
            )

        signal = company.signals.quality

        evidence = statements(signal.evidence)

        if cls._quality_score(company) is None:
            return ScoreBasis(
                # The signal's own account where it has one. Only the
                # signal knows why it reads UNKNOWN, and the two reasons
                # are not interchangeable: a company's figures could not
                # be read, while a token's model can score one question
                # of the nineteen it asks and needs two for a band.
                basis=signal.basis
                or (
                    f"Quality reads {signal.quality} — the figures a business "
                    "is judged on could not be read — so no score was given."
                ),
                evidence=evidence,
            )

        derivation = cls._quality_derivation(company)

        scale = cls._banded(cls.QUALITY_SCORES)

        if derivation is None:
            # No factors were carried out with the signal, so the band is
            # all there is to report. Said as the band it is, rather than
            # as arithmetic nobody can check.
            return ScoreBasis(
                basis=(
                    f"Quality reads {signal.quality}, from the findings "
                    f"below. This platform scores {scale}."
                ),
                evidence=evidence,
                rules=(PROVIDER_QUALITY,),
            )

        # The arithmetic leads, because "3 of 3 points earned → HIGH → 80"
        # is checkable and "quality reads HIGH" is a band name a reader
        # can only accept.
        return ScoreBasis(
            basis=(
                f"{derivation.stated()} Quality counts one point per factor "
                f"below and never subtracts one. This platform scores {scale}."
            ),
            evidence=evidence,
            derivation=derivation,
            rules=(PROVIDER_QUALITY,),
        )

    @classmethod
    def _quality_derivation(
        cls,
        company: CompanyRecommendation | None,
    ) -> ScoreDerivation | None:
        """The factors behind the quality score, where it counted any.

        Composed here rather than in the signal because this is where a
        band becomes a number: the signal counts and bands, and the
        score constant is this layer's house rule. Both halves travel
        together or the reader cannot check either.
        """

        if company is None:
            return None

        signal = company.signals.quality

        score = cls._quality_score(company)

        if score is None or not signal.contributions:
            return None

        return ScoreDerivation(
            contributions=signal.contributions,
            earned=signal.earned,
            available=signal.available,
            band=signal.quality,
            score=score,
            scale=tuple(cls.QUALITY_SCORES.items()),
            required=signal.next_band_needs,
            established_factors=signal.available,
            candidate_factors=QualitySignalService.FACTORS,
        )

    @classmethod
    def _withdrawn_quality_basis(
        cls,
        absent_because: str | None,
    ) -> ScoreBasis:
        """Read, then unread by an audit — and therefore not scored.

        The sentence is the composing service's, carried rather than
        composed: that layer knows which statements were withdrawn and
        how many, and re-authoring it here would put the same claim in
        two places with one of them guessing. Where none was supplied,
        the fact is still stated — an unworded withdrawal is not a
        licence to score.

        **No rule is stamped.** A withdrawal assigns no meaning, and a
        stamp would say a ruler had run.
        """

        # Two sentences, two owners. The first is the composing service's
        # account of *what happened to the evidence*, quoted; the second
        # is this layer's account of *what it did about it*, which is the
        # only part it knows. Repeating the first would put one claim in
        # two voices, and the re-observation clause belongs to whichever
        # of them already carries it.
        happened = absent_because or (
            "Every financial statement reading this platform holds for this "
            "security was withdrawn by an offline audit of the filing, so "
            "none of them is counted. Reading the statement again is what "
            "restores authority, and it is an explicit spend."
        )

        return ScoreBasis(
            basis=(
                f"{happened} No business quality is scored from them: a "
                "withdrawn reading is stored history rather than a current "
                "assessment, and the provider's proxies are not consulted "
                "in its place."
            ),
        )

    @classmethod
    def _grounded_quality_basis(
        cls,
        grounded: BusinessQuality,
    ) -> ScoreBasis:
        """The filing-grade quality reading, with its whole arithmetic.

        The label is deliberately narrow. This measures grounded
        profitability and growth quality under currently established
        evidence — not business quality entire, which would need
        returns on capital, capital allocation and a moat this platform
        has no canonical measure for. Calling it the larger thing would
        be the overstatement every other honesty rule here exists to
        prevent.
        """

        scored = [factor for factor in grounded.factors if factor.is_answered]

        evidence: list[str] = []

        # First, because it is the reason the factors below are
        # unavailable rather than one more absence beside them. The
        # sentence is the domain object's own: this layer renders it and
        # does not compose one, so a reader and the platform's own
        # reasoning are looking at the same words.
        refused = grounded.incomparable_top_line

        if refused is not None:
            evidence.append(refused.stated())

        for factor in grounded.factors:
            if factor.is_answered:
                evidence.extend(factor.evidence)
                continue

            # An unavailable or inapplicable factor keeps its own
            # layer's wording, and stays out of the denominator.
            evidence.append(
                f"{factor.asks} — {factor.status}: "
                f"{factor.because or 'no reason recorded'}"
            )

        # Named where a reader would otherwise read the omission as an
        # oversight, or as the platform having found nothing to say.
        evidence.extend(
            f"{excluded.name} is not part of this score. {excluded.because}"
            for excluded in grounded.excluded
        )

        return ScoreBasis(
            basis=(
                f"{grounded.stated()} This measures {grounded.label} from "
                f"{grounded.source}, over the {len(scored)} of "
                f"{len(grounded.factors)} questions its financial model "
                "could answer from established figures. It is not a "
                "complete measure of business quality."
                + (f" {refused.stated()}" if refused is not None else "")
            ),
            evidence=tuple(evidence),
            derivation=cls._grounded_derivation(grounded),
            # Stamped only where the rule assigned a band. An UNKNOWN
            # from too few answered factors is an explained absence, and
            # a rule stamp there would claim a meaning was assigned.
            rules=(QUALITY_GROUNDED,) if grounded.score is not None else (),
        )

    @staticmethod
    def _grounded_derivation(
        grounded: BusinessQuality,
    ) -> ScoreDerivation | None:
        """The factors that scored, in the shape the dossier already shows.

        Only the answered ones carry a row: an unavailable factor is
        not a zero-point factor, and putting it in the table beside one
        that scored nothing would be the very conflation this design
        keeps apart. The unanswered ones are worded in the evidence
        above instead.
        """

        if grounded.score is None:
            return None

        answered = [factor for factor in grounded.factors if factor.is_answered]

        return ScoreDerivation(
            contributions=tuple(
                Contribution(
                    statement=factor.asks,
                    points=factor.points,
                    sense=factor.sense,
                    verdict=factor.verdict,
                )
                for factor in answered
            ),
            earned=grounded.favourable,
            # The denominator is what was answered, never what was
            # asked: a company whose growth could not be read is not
            # thereby a worse business.
            available=grounded.answered,
            band=grounded.band.value,
            score=grounded.score,
            scale=tuple((band.value, value) for band, value in BAND_SCORES.items()),
            # How much of the quality question set could be read at all,
            # which is not what `earned` over `available` measures.
            established_factors=grounded.answered,
            candidate_factors=len(grounded.factors),
        )

    @classmethod
    def _valuation_basis(
        cls,
        company: CompanyRecommendation | None,
    ) -> ScoreBasis:
        """How attractive the price is, and by whose ruler."""

        if company is None:
            return ScoreBasis(
                basis=(
                    "No security-level analysis was gathered, so the price "
                    "was not scored. Market momentum is never used in its "
                    "place: it says nothing about whether this company is "
                    "cheap."
                ),
            )

        signal = company.signals.value

        evidence = statements(signal.evidence)

        if cls._valuation_score(company) is None:
            return ScoreBasis(
                # The signal's own account where it has one, for the same
                # reason the quality basis defers: only the signal knows
                # whether the figures could not be read or are not a
                # question about this asset at all, and the two must not
                # share a sentence.
                basis=signal.basis
                or (
                    f"Valuation reads {signal.valuation} — the figures a price "
                    "is judged against could not be read — so no score was "
                    "given."
                ),
                evidence=evidence,
            )

        return ScoreBasis(
            basis=(
                # The band is named as what it is. The sentence this
                # replaced said "Valuation reads CHEAP, from the findings
                # below" — presenting a house classification as a reading
                # of evidence, above a finding that claimed a benchmark
                # nobody holds.
                f"No valuation benchmark is held, so the forward P/E "
                f"stands alone as an observation. The platform's legacy "
                f"valuation policy (pe-bands@1, unsourced) classes it "
                f"{signal.valuation} against its own fixed bands — a house "
                f"rule, not an evidenced comparison. This platform scores "
                f"{cls._banded(cls.VALUATION_SCORES)}."
            ),
            evidence=evidence,
            rules=(PE_BANDS, VALUATION_SCORES_RULE),
        )

    @classmethod
    def _safety_basis(
        cls,
        company: CompanyRecommendation | None,
    ) -> ScoreBasis:
        """
        How calm this security's own record is, and by whose ruler.

        Shown as safety rather than risk so that every score on the page
        runs the same way. The inversion is stated outright, because a
        reader who has seen "Risk 45" before must be able to see that this
        is the same reading and not a different one.
        """

        if company is None or company.signals.risk is None:
            return ScoreBasis(
                basis=(
                    "This security's price history was not read, so its own "
                    "safety was not scored. The account's risk is never used "
                    "in its place, and an unmeasured risk is never shown as "
                    "a safe security."
                ),
            )

        signal = company.signals.risk

        evidence = statements(signal.evidence)

        if cls._risk_score(company) is None:
            return ScoreBasis(
                basis=(
                    f"Risk reads {signal.level} — the price history was too "
                    "short to measure — so no score was given. An unmeasured "
                    "risk is never reported as safety."
                ),
                evidence=evidence,
            )

        return ScoreBasis(
            basis=(
                f"Risk reads {signal.level}, from the findings below, and "
                f"safety is what is left of 100 — higher is safer. The risk "
                f"bands, as safety: {cls._banded(cls._safety_bands())}."
            ),
            evidence=evidence,
            rules=(RISK_BANDS, RISK_SEVERITY),
        )

    @classmethod
    def _evidence_basis(
        cls,
        company: CompanyRecommendation | None,
        reasoning: ReasoningSnapshot,
        cognitive_confidence: float,
    ) -> ScoreBasis:
        """
        How well evidenced this case is — the one score about the platform.

        It measures the reading, not the security: a low number says this
        case rests on less than the platform can normally see, never that
        the business is worse.
        """

        cognitive = int(cognitive_confidence * 100)

        evidence = [
            f"Portfolio reasoning is {reasoning.portfolio.confidence:.0%} "
            "confident in what it could read.",
            f"Market reasoning is {reasoning.market.confidence:.0%} confident "
            "in what it could read.",
            f"Risk reasoning is {reasoning.risk.confidence:.0%} confident in "
            "what it could read.",
        ]

        if company is None:
            return ScoreBasis(
                basis=(
                    "Nothing about the security itself was gathered, so this "
                    "case rests on portfolio and market reasoning alone. Its "
                    f"{cognitive} of 100 is discounted to 60% for standing on "
                    "the account rather than on the security."
                ),
                evidence=tuple(evidence),
                rules=(COGNITIVE_CONFIDENCE, EVIDENCE_SCORE),
            )

        evidence.append(
            f"The security committee is {company.confidence} of 100 sure of "
            f"its own {company.recommendation} read."
        )

        return ScoreBasis(
            basis=(
                f"The average of how well the reasoning was evidenced "
                f"({cognitive} of 100) and how sure the security committee is "
                f"of its own read ({company.confidence} of 100)."
            ),
            evidence=tuple(evidence),
            rules=(COGNITIVE_CONFIDENCE, EVIDENCE_SCORE),
        )

    @staticmethod
    def _portfolio_fit_basis(
        measure: PortfolioFitMeasure,
    ) -> ScoreBasis:
        """
        How much room the investor's own policy leaves for this security.

        Every term is listed, including the ones the policy gave nothing to
        measure against — an average of two terms presented as an average of
        three is a number that overstates what was asked.
        """

        measured = sum(1 for term in measure.terms if term.room is not None)

        if measured == 0:
            return ScoreBasis(
                basis=(
                    "The investor's policy states no limit this security could "
                    "be measured against, so fit was not scored."
                ),
                evidence=measure.stated_terms,
                kind=ScoreKind.POLICY,
            )

        return ScoreBasis(
            basis=(
                f"The average of the room the investor's own policy leaves, "
                f"across the {measured} of {len(measure.terms)} terms it could "
                f"be measured on. A higher number is more room, not a better "
                f"business."
            ),
            evidence=measure.stated_terms,
            # Not an assessment of anything: it moves when the policy
            # changes, not when the market does.
            kind=ScoreKind.POLICY,
            rules=(PORTFOLIO_FIT,),
        )

    @staticmethod
    def _catalysts(
        company: CompanyRecommendation | None,
        today: date,
    ) -> tuple[str, ...]:
        """
        What is scheduled to happen to this security, dated.

        These used to be the market's opportunities and the account's, which
        are identical under every symbol: "Stable market conditions" was
        MSFT's catalyst and everything else's, so the one line meant to say
        why this security now said nothing about this security at all. Those
        remain weighed, as the context they are.

        What belongs here is something dated that is scheduled to happen to
        this security — today, the company's own next earnings report. It is
        a date and only a date. Nothing here says the report will be good,
        because nothing knows: a catalyst is an event on a calendar, not a
        forecast of its content.
        """

        schedule = company.signals.earnings if company is not None else None

        window = schedule.window if schedule is not None else None

        if window is None or not window.is_ahead_of(today):
            return ()

        return (window.stated(today),)

    @staticmethod
    def _company_findings(
        company: CompanyRecommendation | None,
        today: date,
    ) -> tuple[Finding, ...]:
        """Everything the signals found about this security, with its sense."""

        if company is None:
            return ()

        risk = company.signals.risk

        # `company.evidence` arrives already attributed, by the service
        # that composed it from the value, quality and momentum signals.
        # The three below are attributed here for the same reason: this
        # is the site that knows which reading produced them.
        return (
            *company.evidence,
            *(
                item.about(Dimension.RISK)
                for item in (risk.evidence if risk is not None else ())
            ),
            *DecisionEvidenceBuilder._research_findings(company.signals.research),
            *DecisionEvidenceBuilder._earnings_findings(company, today),
        )

    @staticmethod
    def _earnings_findings(
        company: CompanyRecommendation,
        today: date,
    ) -> tuple[Finding, ...]:
        """
        What the company's calendar says, where it is not a catalyst.

        A report still ahead is a catalyst and is stated there, once. What
        is left is the two ways there is no report ahead, and they are worth
        stating because silence would read as nobody having looked:

        - the last window the provider still publishes, which is the quarter
          just reported rather than the next one;
        - no date published at all.

        Neutral, always. A company reporting soon is neither a reason to buy
        it nor a reason to sell it, and a scheduling fact that carried a
        sense would be a view on a report nobody has read. A calendar that
        could not be read is not here at all — that is a gap in the
        platform, and it is reported as missing evidence.
        """

        schedule = company.signals.earnings

        if schedule is None or schedule.unread:
            return ()

        if schedule.window is None:
            return (
                Finding.neutral(
                    f"No upcoming earnings date is published for {company.symbol}.",
                    Dimension.SCHEDULE,
                ),
            )

        if schedule.window.is_ahead_of(today):
            return ()

        return (
            Finding.neutral(
                f"{schedule.window.stated(today)} No next date is published yet.",
                Dimension.SCHEDULE,
            ),
        )

    @staticmethod
    def _research_findings(
        research: CompanyResearch | None,
    ) -> tuple[Finding, ...]:
        """
        The fundamental analysts' verdicts, weighed as evidence not gated.

        Each analyst's read reaches the case the way the risk signal does:
        as a finding carrying its own sense, for the CIO to weigh against
        everything else. It does not move a gate — quality, valuation and the
        rest still decide that — because whether strong fundamentals settle a
        case is the Artificial CIO's judgement, and folding a new score into
        a gate before it is calibrated is the same step the market gate was
        declined for.
        """

        if research is None:
            return ()

        # Whichever analysts this security's playbook asked for, in the
        # order it asked them. An analyst the playbook declined leaves no
        # finding here and is explained on the playbook itself, so a
        # missing verdict never has to be read as a failed one.
        #
        # Growth is named for what it measures. Its analyst reads
        # provider fields whose period and formula are undocumented
        # (owner ruling 2026-08-23), so its verdict is worded as a
        # provider-reported growth *signal* — "The provider-reported
        # growth signal is declining" — and the unqualified "Growth is
        # declining" is unproducible. The other analysts keep their
        # names; renaming them is the broader authority question this
        # slice deliberately does not open.
        findings = (
            DecisionEvidenceBuilder._opinion_finding(
                DecisionEvidenceBuilder._FINDING_ASPECTS.get(key, key.label),
                opinion,
            )
            for key, opinion in research.opinions.items()
        )

        return tuple(finding for finding in findings if finding is not None)

    #: Per-analyst overrides of the aspect a finding sentence opens
    #: with, where the analyst's honest name is not the analyst's short
    #: one. Keyed by `AnalystKey`, consulted only where present.
    _FINDING_ASPECTS = {AnalystKey.GROWTH: "The provider-reported growth signal"}

    @staticmethod
    def _opinion_finding(
        aspect: str,
        opinion: Opinion[Any],
    ) -> Finding | None:
        """
        One analyst's verdict as a finding, or nothing where it measured none.

        An analyst that could read no figure contributes no finding — its
        silence is a gap, reported as missing evidence, not a neutral verdict
        dressed as a reading. Where it did measure, the sense is read off its
        own 0-100 score, banded once the way a strong signal argues for a case
        and a weak one against.
        """

        if opinion.confidence <= 0.0 or not opinion.evidence:
            return None

        statement = (
            f"{aspect} is {opinion.verdict.value} — {' '.join(opinion.evidence)}"
        )

        if opinion.score >= 75:
            return Finding.favourable(statement, Dimension.RESEARCH)

        if opinion.score <= 40:
            return Finding.adverse(statement, Dimension.RESEARCH)

        return Finding.neutral(statement, Dimension.RESEARCH)

    @classmethod
    def _missing_evidence(
        cls,
        company: CompanyRecommendation | None,
        symbol: str,
        asset_class: AssetClass | None = None,
        grounded: BusinessQuality | None = None,
    ) -> tuple[str, ...]:
        """
        What this case is short of, and that a later cycle could supply.

        "Valuation data is unavailable" reads as a gap a later cycle might
        close. For an asset with no company behind it there is nothing to
        become available, so it is not listed here at all: a token has no
        earnings, the findings already say so in those words, and saying
        it again under *still missing* both repeats the evidence and
        sends the investor back to wait for something that will never
        arrive. Only what could still be read is named here.

        And only what is genuinely absent. Every clause here read the
        provider signals while the quality *score* was read from the
        grounded assessment, so the two halves of one page disagreed:
        AAPL's review condition said quality was unavailable beside its own
        MEDIUM 62, and DIS's beside a HIGH 80. The quality clause now comes
        from the assessment that governs the score.
        """

        # Only an asset positively known to have no company is exempt.
        # An unclassified one is short of data, which may yet arrive.
        has_company = asset_class is None or not asset_class.has_no_company

        missing: list[str] = []

        if company is None:
            # Said as the half it is. A grounded assessment may stand
            # beside this absence, and "no security-level analysis" over
            # the whole case would deny it.
            missing.append(
                f"No security-level analysis is available for {symbol}."
                if grounded is None
                else (
                    f"No market analysis has been gathered for {symbol}: no "
                    "price, valuation, risk or earnings reading stands "
                    "beside the filing evidence."
                )
            )

            quality_gap = cls._absent_quality(company, symbol, grounded, has_company)

            return (*missing, quality_gap) if quality_gap else tuple(missing)

        if has_company and company.signals.value.valuation == "UNKNOWN":
            missing.append(f"Valuation data is unavailable for {symbol}.")

        quality_gap = cls._absent_quality(company, symbol, grounded, has_company)

        if quality_gap:
            missing.append(quality_gap)

        if company.signals.risk is None or company.signals.risk.level == "UNKNOWN":
            # Not "too short": this platform has not read enough of the
            # price history to measure risk, and how much exists is a
            # different claim it has not checked.
            missing.append(
                f"Not enough price history has been read for {symbol} to measure risk."
            )

        # A calendar nobody could read, said as that. A company between
        # reports says so among its findings instead: no date published is
        # something known about the company, not something the platform
        # failed to fetch.
        if company.signals.earnings is not None and company.signals.earnings.unread:
            missing.append(
                f"The earnings calendar for {symbol} could not be read this cycle."
            )

        return tuple(missing)

    @staticmethod
    def _absent_quality(
        company: CompanyRecommendation | None,
        symbol: str,
        grounded: BusinessQuality | None,
        has_company: bool,
    ) -> str | None:
        """What is missing about quality, from the reading that governs it.

        Three states, and collapsing any two of them prints a falsehood:

        - **assessed and banded** — nothing is missing, whichever route
          produced the band;
        - **assessed and inconclusive** — the statements reached quorum and
          the questions they answer were too few to band. The reading
          happened, so calling the data unavailable denies evidence this
          page displays and sends the investor to acquire what is already
          held. The assessment states its own arithmetic; it is quoted;
        - **genuinely unavailable** — no grounded assessment exists at all
          and the provider proxy reads UNKNOWN.

        The precedence is `_quality_value`'s, unchanged and deliberately
        not re-derived in spirit: a grounded assessment governs outright
        where one exists, and the provider proxy is consulted only where
        none does. That is what makes this sentence and that score two
        readings of one object rather than two objects.
        """

        if not has_company:
            return None

        if grounded is not None:
            if grounded.score is not None:
                return None

            # What a later cycle could supply, which is what this list is
            # for — deliberately not the assessment's own arithmetic. The
            # CIO's rationale quotes that, and one page rendering the same
            # sentence under two headings is the repetition the
            # presentation-ownership audit measured six times.
            answerable = len(grounded.factors) - grounded.answered

            return (
                f"Business quality for {symbol} was assessed and could not "
                f"be concluded: {answerable} of {len(grounded.factors)} "
                "quality questions are still unanswerable from its "
                "established figures."
            )

        if company is not None and company.signals.quality.quality == "UNKNOWN":
            return f"Quality data is unavailable for {symbol}."

        return None
