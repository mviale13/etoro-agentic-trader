"""One token's asset quality, from the questions its archetype is asked.

A read-only door in the family every crypto service on this platform
belongs to: it asks `CryptoPlaybookService` what is already held and
stops. It fetches nothing, asks no model and writes nothing, so a page
view may sit behind it.

The order of operations is the design, and it is deliberately the
reverse of a scoring service that starts from the fields it has:

```text
1  applicability   from the archetype alone        (S3)
2  readiness       from the question alone         (S5)
3  standing        from the evidence               (S1, S4.5)
4  verdict         only where all three allow it
```

Nothing at step 3 can change step 1 or step 2. That is what makes
*this question does not apply*, *this platform cannot judge this yet*
and *this asset does badly here* three different sentences that a
surface can print side by side without any of them borrowing another's
authority.

**The supply evidence is read from the S4.6 vocabulary, never from
`CompanyFacts.circulating_supply`.** The generic field does not name a
concept, and the semantic work proved that a number without its concept
cannot be compared with anything. This service reads `SupplyPicture`,
asks for emitted supply and a protocol maximum by name, and reports the
share where both are held — unscored, because that is what the evidence
supports today.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_playbook import DemandCoverage, QuestionCoverage
from app.domain.crypto_quality import (
    MINIMUM_SCORED,
    POINTS_PER_QUESTION,
    RULES,
    CryptoAssetQuality,
    QualityAnswer,
    QualityBand,
    QualityCoverage,
    QualityReadiness,
    QuestionParticipation,
    headline_for,
    readiness_for,
)
from app.domain.crypto_questions import CryptoQuestionKey, QuestionApplicability
from app.domain.evidence_standing import EvidenceStanding
from app.domain.finding import Dimension, Finding, Sense
from app.domain.quality_signal import QualitySignal
from app.domain.score_basis import Contribution
from app.domain.supply_semantics import Comparison, SupplyConcept, SupplyPicture
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.supply_semantics_service import SupplySemanticsService

#: The demand each scorable rule reads its figure from. Named here
#: rather than guessed from the first covered demand: a rule must say
#: which fact it scores, or a later change to the question's demand
#: order would silently re-point it at a different number.
_SCORED_DEMAND = {
    CryptoQuestionKey.MARKET_ROBUSTNESS: "market_cap",
}


class CryptoAssetQualityService:
    """Which durable qualities of this asset the platform can judge today."""

    def __init__(
        self,
        playbook: CryptoPlaybookService | None = None,
        supply: SupplySemanticsService | None = None,
    ) -> None:
        self._playbook = playbook or CryptoPlaybookService()
        self._supply = supply or SupplySemanticsService()

    def established(
        self,
        symbol: str,
        asset_class: AssetClass | None,
    ) -> CryptoAssetQuality | None:
        """This token's quality, or None for anything that is not a token."""

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        playbook = self._playbook.established(normalized, asset_class)

        if playbook is None:
            return None

        picture = self._supply.established(normalized, asset_class)

        answers = tuple(
            self._answer(coverage, picture) for coverage in playbook.coverage
        )

        return self._compose(normalized, answers)

    # ── one question ────────────────────────────────────────────────

    def _answer(
        self,
        coverage: QuestionCoverage,
        picture: SupplyPicture | None,
    ) -> QualityAnswer:
        question = coverage.question.key

        # Applicability first, and it can end the matter. A question the
        # archetype refuses is never reported as evidence this platform
        # lacks — Bitcoin is not short of a holder-accrual figure, it is
        # not asked for one.
        state = coverage.applicability.state

        if state is QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.NOT_APPLICABLE,
                stated=f"{coverage.question.label} is not asked of this asset.",
                because=coverage.applicability.because,
            )

        if state is QuestionApplicability.UNDETERMINED:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.UNDETERMINED,
                stated=(
                    f"Whether {coverage.question.label.lower()} applies "
                    "here is not established."
                ),
                because=coverage.applicability.because,
            )

        ruling = readiness_for(question)

        if ruling.readiness is QualityReadiness.OUTSIDE_ASSET_QUALITY:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.OUTSIDE,
                stated=(
                    f"{coverage.question.label} is asked, and its answer "
                    "is not part of asset quality."
                ),
                because=ruling.because,
            )

        if ruling.readiness is QualityReadiness.NOT_READY:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.UNANSWERABLE,
                stated=f"{coverage.question.label} cannot be judged yet.",
                because=ruling.because,
            )

        if ruling.readiness is QualityReadiness.VISIBLE_NOT_SCORED:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.SHOWN,
                stated=(
                    f"{coverage.question.label}: evidence is held and "
                    "none of it is scored."
                ),
                because=ruling.because,
                shown=self._shown(question, coverage, picture),
            )

        return self._score(coverage, ruling.because)

    def _score(
        self,
        coverage: QuestionCoverage,
        readiness_because: str,
    ) -> QualityAnswer:
        """A scorable question, answered or honestly unanswered."""

        question = coverage.question.key
        rule = RULES[question]

        covered = self._demand(coverage, _SCORED_DEMAND[question])

        # Only established evidence reaches a rule. A conflicted market
        # capitalisation is the case this guards: Arbitrum's two vendors
        # differ by a factor that no band could absorb, and scoring
        # either would publish a number this platform has already said
        # it cannot settle.
        if covered is None or covered.standing is not EvidenceStanding.ESTABLISHED:
            return QualityAnswer(
                question=question,
                participation=QuestionParticipation.SCORABLE_UNANSWERED,
                rule=rule,
                stated=(
                    f"{coverage.question.label} can be scored, and this "
                    "asset's evidence does not reach the standing the "
                    "rule requires."
                ),
                because=self._unanswered_because(covered, rule.measures),
            )

        assert covered.value is not None

        band = rule.band_for(covered.value)

        return QualityAnswer(
            question=question,
            participation=QuestionParticipation.SCORED,
            rule=rule,
            band=band,
            value=covered.value,
            source=covered.source,
            stated=(
                f"{coverage.question.label}: {band.verdict} — "
                f"{_money(covered.value)}, {band.means}."
            ),
            because=(
                f"Rule {rule.name}@{rule.version} reads "
                f"{rule.measures}. {_threshold(band)} "
                f"{covered.source or 'The source'} reports "
                f"{_money(covered.value)}, corroborated independently. "
                f"{readiness_because}"
            ),
        )

    @staticmethod
    def _unanswered_because(
        covered: DemandCoverage | None,
        measures: str,
    ) -> str:
        if covered is None:
            return (
                f"Nothing has been read for {measures}. Reading it is an "
                "explicit spend, and no surface takes it — "
                "`movrvest acquire` does."
            )

        if covered.standing is EvidenceStanding.CONFLICTED:
            return (
                f"Sources make incompatible claims about {measures}, so "
                "no figure is served. A conflicted number is not a low "
                "number, and this question is left unanswered rather "
                "than answered badly. " + (covered.because or "")
            ).strip()

        return (
            f"{measures.capitalize()} is held as "
            f"{covered.standing.stated.lower()} rather than as an "
            "established fact, and no rule on this platform reads an "
            "uncorroborated figure. " + (covered.because or "")
        ).strip()

    # ── evidence shown but not scored ───────────────────────────────

    def _shown(
        self,
        question: CryptoQuestionKey,
        coverage: QuestionCoverage,
        picture: SupplyPicture | None,
    ) -> tuple[str, ...]:
        """What an investor can see beneath an unscored question.

        Every line carries its standing. That is the whole permission
        structure of this state: a claim may be shown because it is
        labelled a claim, and the moment the label came off it would
        have to be scored or hidden.
        """

        if question is CryptoQuestionKey.SUPPLY_AND_DILUTION:
            return self._supply_shown(picture)

        if question is CryptoQuestionKey.MONETARY_SCARCITY:
            return self._scarcity_shown(picture)

        shown: list[str] = []

        for covered in coverage.covered:
            if not covered.standing.serves_value:
                continue

            if covered.methodology:
                shown.append(
                    f"{covered.source or 'The source'} defines it: "
                    f"{covered.methodology} ({covered.standing.stated.lower()})."
                )
                continue

            if covered.value is None:
                continue

            where = f" for {covered.entity}" if covered.entity else ""

            shown.append(
                f"{covered.demand.stated.capitalize()}{where}: "
                f"{_money(covered.value)} — {covered.source or 'one source'}, "
                f"{covered.standing.stated.lower()}."
            )

        return tuple(shown)

    @staticmethod
    def _supply_shown(picture: SupplyPicture | None) -> tuple[str, ...]:
        """The emitted share, named for what it is and nothing more.

        Called *the emitted share of the protocol maximum*, never
        dilution. The ratio says how much of a cap has been issued; what
        the rest arriving would do to a holder depends on when it
        arrives and to whom, and neither is acquired.
        """

        if picture is None or not picture.is_read:
            return ()

        shown: list[str] = []

        emitted = picture.of(SupplyConcept.EMITTED_SUPPLY)
        maximum = picture.of(SupplyConcept.MAX_SUPPLY)

        if not maximum:
            shown.append(
                "No protocol maximum is reported for this asset, so there "
                "is no envelope to measure emission against. An absent "
                "cap is not a defect — two of the assets held have none "
                "by design — and this platform cannot tell a protocol "
                "with no cap from one whose cap it failed to read."
            )
            return tuple(shown)

        cap = maximum[0]

        shown.append(
            f"Protocol maximum: {cap.stated} — "
            f"{', '.join(sorted({fact.source for fact in maximum}))}."
        )

        # A chain reading first, and named as one. Where the vendors
        # disagree with it, the disagreement is the evidence.
        for fact in emitted:
            share = fact.value / cap.value if cap.value else None

            if share is None:
                continue

            shown.append(
                f"{share * 100:.1f}% of that maximum has been emitted — "
                f"{fact.value:,.0f} tokens, {fact.source}, "
                f"{fact.authority.stated.lower()}."
            )

        for comparison in picture.comparisons:
            if comparison.left.concept is not SupplyConcept.EMITTED_SUPPLY:
                continue

            if comparison.verdict is not Comparison.CONFLICTED:
                continue

            shown.append(f"Not settled: {comparison.because}")

        future = picture.of(SupplyConcept.FUTURE_EMISSIONS)

        for fact in future:
            shown.append(
                f"Future, unissued supply: {fact.stated} — {fact.source}. "
                "When it arrives and to whom is not read, so what "
                "pressure it puts on a holder is not measured."
            )

        if not future:
            shown.append(
                "No emission schedule is held, so the share emitted "
                "cannot be turned into what a holder should expect next. "
                "Two assets at the same share can face entirely "
                "different futures."
            )

        return tuple(shown)

    @staticmethod
    def _scarcity_shown(picture: SupplyPicture | None) -> tuple[str, ...]:
        if picture is None or not picture.is_read:
            return ()

        maximum = picture.of(SupplyConcept.MAX_SUPPLY)

        if not maximum:
            return (
                "No protocol maximum is reported, and this platform "
                "cannot distinguish an asset with no cap from one whose "
                "cap it has not read.",
            )

        cap = maximum[0]

        return (
            f"A stated maximum of {cap.stated}, reported by "
            f"{', '.join(sorted({fact.source for fact in maximum}))}.",
            "The issuance schedule is not read, so how fast the "
            "remainder arrives is unknown.",
            "Who is able to change that schedule, and by what process, "
            "is not read. A cap that someone can rewrite is a different "
            "asset from one nobody can.",
        )

    # ── composition ─────────────────────────────────────────────────

    @staticmethod
    def _demand(
        coverage: QuestionCoverage,
        token_fact: str,
    ) -> DemandCoverage | None:
        for covered in coverage.covered:
            if covered.demand.token_fact == token_fact:
                return covered

        return None

    @staticmethod
    def _compose(
        symbol: str,
        answers: tuple[QualityAnswer, ...],
    ) -> CryptoAssetQuality:
        applicable = [
            answer
            for answer in answers
            if answer.participation
            not in (
                QuestionParticipation.NOT_APPLICABLE,
                QuestionParticipation.UNDETERMINED,
            )
        ]

        scorable = [
            answer
            for answer in applicable
            if answer.participation
            in (
                QuestionParticipation.SCORED,
                QuestionParticipation.SCORABLE_UNANSWERED,
            )
        ]

        scored = [answer for answer in applicable if answer.scored]

        coverage = QualityCoverage(
            applicable=len(applicable),
            scorable=len(scorable),
            answered=len(scored),
            shown=sum(
                1
                for answer in applicable
                if answer.participation is QuestionParticipation.SHOWN
            ),
            unanswerable=sum(
                1
                for answer in applicable
                if answer.participation is QuestionParticipation.UNANSWERABLE
            ),
            outside=sum(
                1
                for answer in applicable
                if answer.participation is QuestionParticipation.OUTSIDE
            ),
            undetermined=sum(
                1
                for answer in answers
                if answer.participation is QuestionParticipation.UNDETERMINED
            ),
        )

        # Judged against what was answered, never against what applies.
        # The rule the ruling's sixteenth section states and the platform
        # already lived by: missing evidence must not silently become
        # negative evidence.
        earned = sum(answer.points for answer in scored)
        available = len(scored) * POINTS_PER_QUESTION

        if len(scored) < MINIMUM_SCORED:
            return CryptoAssetQuality(
                symbol=symbol,
                answers=answers,
                coverage=coverage,
                quality="UNKNOWN",
                confidence=_confidence(coverage),
                because=_no_headline_because(coverage, scored),
                earned=earned,
                available=available,
            )

        return CryptoAssetQuality(
            symbol=symbol,
            answers=answers,
            coverage=coverage,
            quality=headline_for(earned, available),
            confidence=_confidence(coverage),
            because=(
                f"{len(scored)} of {coverage.scorable} scorable questions "
                f"were answered, earning {earned} of {available} points."
            ),
            earned=earned,
            available=available,
        )


def signal_of(quality: CryptoAssetQuality) -> QualitySignal:
    """The quality model as the signal contract the platform already has.

    An adapter and nothing more: no band, no point and no confidence is
    computed here. It exists so the question model reaches the surfaces
    that already render `QualitySignal` — the dossier's evidence list and
    the score breakdown — without either of them learning a second
    vocabulary.

    Findings carry the scored questions and the shown evidence, in that
    order, and every shown line is worded with its standing. A reader
    seeing them side by side can tell which one a number came out of.
    """

    evidence: list[Finding] = []
    contributions: list[Contribution] = []

    for answer in quality.answers:
        if answer.scored:
            assert answer.band is not None

            evidence.append(
                Finding(
                    statement=answer.stated,
                    sense=answer.band.sense,
                    dimension=Dimension.QUALITY,
                )
            )
            contributions.append(
                Contribution(
                    statement=answer.stated,
                    points=answer.band.points,
                    sense=answer.band.sense,
                    verdict=answer.band.verdict,
                )
            )
            continue

        for line in answer.shown:
            evidence.append(
                Finding(
                    statement=line,
                    # Shown evidence argues neither way by construction.
                    # It is not scored, so presenting it as favourable or
                    # adverse would let a claim act on a case through the
                    # tone of its sentence.
                    sense=Sense.NEUTRAL,
                    dimension=Dimension.QUALITY,
                )
            )

    if not evidence:
        evidence.append(
            Finding(
                statement=quality.because,
                sense=Sense.NEUTRAL,
                dimension=Dimension.QUALITY,
            )
        )

    return QualitySignal(
        quality=quality.quality,
        confidence=quality.confidence,
        evidence=tuple(evidence),
        contributions=tuple(contributions),
        earned=quality.earned,
        available=quality.available,
        # The model's own account travels with it. Without this the
        # executive builder explains a token's UNKNOWN as a company's:
        # "the figures a business is judged on could not be read", about
        # an asset that answered its one scorable question at the top
        # band.
        basis=quality.because,
    )


def _no_headline_because(
    coverage: QualityCoverage,
    scored: list[QualityAnswer],
) -> str:
    """Why no band was emitted — about the model or about the asset.

    The two are different failures and the investor is owed the
    difference. A model that can only score one question would produce
    no band for a perfect asset; an asset whose one scorable figure
    conflicts produces none either, and only one of those is a reason to
    go and acquire something.
    """

    if coverage.scorable < MINIMUM_SCORED:
        # `applicable` and `in_scope` differ only where an archetype
        # left questions undetermined, and printing one where the
        # header prints the other read as an arithmetic error on the
        # single security it happens to — Bittensor, asked four
        # questions of a possible nineteen.
        undetermined = (
            f", and {coverage.undetermined} more whose applicability "
            "nothing has established"
            if coverage.undetermined
            else ""
        )

        return (
            f"No quality band is emitted. This asset is asked "
            f"{coverage.applicable} questions{undetermined}. "
            f"{coverage.scorable} of them can be scored at all, and a "
            f"band requires {MINIMUM_SCORED}. That is a statement about "
            "this platform's evidence, not about the asset: "
            f"{_plural(coverage.shown, 'question has', 'questions have')} "
            "evidence that is shown and not counted, and "
            f"{_plural(coverage.unanswerable, 'has', 'have')} none yet."
        )

    return (
        f"No quality band is emitted. {len(scored)} of "
        f"{coverage.scorable} scorable questions were answered and a "
        f"band requires {MINIMUM_SCORED}. The unanswered ones are "
        "unanswered, not failed."
    )


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _confidence(coverage: QualityCoverage) -> int:
    """How far the coverage supports whatever was concluded.

    Confidence is about the evidence and quality is about the asset, and
    this is the seam where a platform usually confuses them. It is
    computed from coverage alone — no band, no figure, no verdict enters
    it — so an asset can never be marked down for a gap or marked up for
    a strong reading it happened to have.

    The denominator is everything in scope, including the questions an
    unestablished archetype left undetermined. Measured on the corpus
    before that was so: Bittensor, the one security with no archetype,
    came out the *most* confident of the eight, because four questions
    were asked of it instead of nineteen. Not knowing what an asset is
    is not a form of knowing about it.
    """

    if not coverage.in_scope:
        return 10

    return max(10, min(90, round(10 + coverage.judged_reach * 80)))


def _money(value: float) -> str:
    """An amount at a unit that keeps it visible.

    Billions are right for a network and wrong for what a provider
    returns when it has lost a token: Hyperliquid came back as 8,105
    dollars once and printed as "$0.00bn", which reads as a rounding
    rather than as the nonsense it was.
    """

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.0f}m"

    if abs(value) >= 1_000:
        return f"${value:,.0f}"

    return f"${value:,.2f}"


def _threshold(band: QualityBand) -> str:
    if band.at_least is None:
        return "It clears no threshold in the table."

    return f"The {band.verdict} band starts at {_money(band.at_least)}."
