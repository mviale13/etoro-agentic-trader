"""Which durable qualities of a digital asset this platform can judge today.

The crypto counterpart of grounded business quality, and built to the
question model S3 established rather than to the fields a provider
happens to return. What it answers, in one sentence:

> **How strong is this economic object on durable, asset-specific
> characteristics — independent of today's market mood, and independent
> of whether it currently looks cheap?**

What it deliberately does not answer: is it going up, is crypto risk-on,
is it attractively valued, should it be bought now, and how much evidence
MOVRvest happens to hold. The first four belong to market context and to
a valuation model that does not exist yet; the last is *confidence*, and
collapsing it into quality is how a platform starts marking an asset
down for its own gaps.

Four vocabularies, kept apart, extending the three S3 already separates:

```text
applicability  ← the archetype alone. Does the question apply at all?
readiness      ← this module. Is the *evidence contract* for the
                 question good enough to carry a score for anyone?
standing       ← EvidenceStanding. Can this asset's figure be trusted?
verdict        ← this module, and only where the first three allow it.
```

**Readiness is a property of the question, never of the asset.** It takes
no symbol and no figure, exactly as `applicability_for` takes no
evidence: a question that is not ready is not ready for Bitcoin either,
and an asset must never be able to make a question scorable by happening
to have data. That is what keeps "we cannot score this yet" and "this
asset scores badly" from ever being the same sentence.

Two rulings are compiled in here as structure rather than as prose.
Market context is unreachable — no return, no relative return, no
breadth, no dominance and no sentiment appears in any rule below, and
the module imports nothing that could supply one. Valuation is
unreachable for the same reason: fully-diluted valuation, capitalisation
over revenue and capitalisation over capital committed are all
computable from facts this platform holds, and none of them is a
quality question.

Nothing here fetches, and no rule reads a figure that is not
`ESTABLISHED`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.crypto_questions import CryptoQuestionKey
from app.domain.finding import Sense


class QualityReadiness(StrEnum):
    """Whether a question's evidence contract can carry a score today.

    Measured against the corpus rather than asserted. Every value below
    is attached to a question with the measurement that put it there, so
    a reader can disagree with the classification by disputing a number
    rather than a judgment.
    """

    #: The question is answerable from evidence this platform is
    #: entitled to trust, and a named rule table turns that evidence
    #: into a verdict. Only these contribute numerically.
    SCORABLE_NOW = "scorable_now"

    #: There is real evidence, and it is not good enough to score. Shown
    #: on the dossier with its standing beside it, counted by nothing.
    #: Hyperliquid's fee economics are the case this state exists for:
    #: economically compelling, single-source, and therefore worth
    #: showing and wrong to score.
    VISIBLE_NOT_SCORED = "visible_not_scored"

    #: Nothing this platform holds answers the question at all. An
    #: acquisition demand, not a verdict, and never a mark against the
    #: asset.
    NOT_READY = "not_ready"

    #: The question is legitimate, is asked, and its answer is not a
    #: property of the asset's quality. Distinct from NOT_READY, which
    #: would promise a score once evidence arrived. Nothing acquired
    #: later moves a question out of this state — only a ruling does.
    OUTSIDE_ASSET_QUALITY = "outside_asset_quality"

    @property
    def stated(self) -> str:
        return _READINESS_LABELS[self]

    @property
    def scores(self) -> bool:
        return self is QualityReadiness.SCORABLE_NOW

    @property
    def is_visible(self) -> bool:
        """Whether the dossier shows the evidence held against it."""

        return self in (
            QualityReadiness.SCORABLE_NOW,
            QualityReadiness.VISIBLE_NOT_SCORED,
        )


_READINESS_LABELS = {
    QualityReadiness.SCORABLE_NOW: "Scored",
    QualityReadiness.VISIBLE_NOT_SCORED: "Shown, not scored",
    QualityReadiness.NOT_READY: "Not yet answerable",
    QualityReadiness.OUTSIDE_ASSET_QUALITY: "Outside asset quality",
}


@dataclass(frozen=True, slots=True)
class ReadinessRuling:
    """Why one question is or is not scored, and what would change it."""

    question: CryptoQuestionKey
    readiness: QualityReadiness

    #: The measurement that decided it. Corpus figures, dated where they
    #: were taken, so the classification is arguable on evidence.
    because: str

    #: What would move it to `SCORABLE_NOW`. None where only a ruling
    #: could — which is the whole difference `OUTSIDE_ASSET_QUALITY`
    #: carries.
    would_change: str | None = None


#: Every question, classified. Measured against the eight-asset corpus
#: and, where eight was too few, against CoinGecko's 250 largest assets
#: read on 2026-08-10.
#:
#: The shape of the result is the finding: **one question of nineteen is
#: scorable**. That is not a gap in this module; it is what the evidence
#: supports, and the eleven `NOT_READY` entries are the acquisition
#: roadmap stated in the currency every other demand on this platform is
#: stated in.
READINESS: dict[CryptoQuestionKey, ReadinessRuling] = {
    CryptoQuestionKey.MARKET_ROBUSTNESS: ReadinessRuling(
        question=CryptoQuestionKey.MARKET_ROBUSTNESS,
        readiness=QualityReadiness.SCORABLE_NOW,
        because=(
            "Market capitalisation is the one asset-specific quantity "
            "that reaches ESTABLISHED on this platform: two independent "
            "claimants agree for six of the eight assets held. It is a "
            "level rather than a change, and under the floor rule below "
            "a uniform 30% market fall re-bands 7.2% of the 250 largest "
            "assets — so it is durable in the sense the ruling requires."
        ),
    ),
    CryptoQuestionKey.LIQUIDITY: ReadinessRuling(
        question=CryptoQuestionKey.LIQUIDITY,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "The measure this platform inherited — a day's volume over "
            "market capitalisation — was measured against the 250 "
            "largest assets and is not a liquidity measure. It ranks "
            "Bitcoin 158th of 233 and 1inch 52nd, while Bitcoin trades "
            "$14.8bn a day and 1inch $7m: a 2,100-fold difference in "
            "what could actually be sold, inverted. Its top is meme and "
            "stablecoin rotation. Absolute volume is honest but "
            "vendor-scoped, so it never establishes, and order-book "
            "depth — the only thing that answers the question — is not "
            "acquired."
        ),
        would_change=(
            "depth at venues this investor could trade on, or a volume "
            "figure whose venue universe two independent sources agree on"
        ),
    ),
    CryptoQuestionKey.SUPPLY_AND_DILUTION: ReadinessRuling(
        question=CryptoQuestionKey.SUPPLY_AND_DILUTION,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "The emitted share of a protocol maximum is a real fact and "
            "this platform can compute it for four assets, but it "
            "corroborates for one. CoinGecko's `total_supply` equals the "
            "protocol maximum exactly for 83 of the 145 capped assets in "
            "the 250 largest — and where a chain reading exists to test "
            "that, it was wrong twice in three: Cardano has emitted 86.2% "
            "of its 45bn cap and Bittensor 53.4% of its 21m, both "
            "published as 100%. So the vendor field cannot stand in for "
            "emitted supply, and a chain reading is a single source."
        ),
        would_change=(
            "an owner ruling that a reproducible primary computation may "
            "establish without a second vendor, or a second independent "
            "reader of chain state"
        ),
    ),
    CryptoQuestionKey.EVIDENCE_MATURITY: ReadinessRuling(
        question=CryptoQuestionKey.EVIDENCE_MATURITY,
        readiness=QualityReadiness.OUTSIDE_ASSET_QUALITY,
        because=(
            "How much of an asset's record has been observed is a "
            "property of the observation, not of the asset. The factor "
            "this replaces scored trading age, which let Bitcoin earn a "
            "quality point for being old and marked a sound young asset "
            "down for existing recently. It belongs to a separate "
            "Evidence Maturity layer, beside confidence."
        ),
    ),
    CryptoQuestionKey.MONETARY_SCARCITY: ReadinessRuling(
        question=CryptoQuestionKey.MONETARY_SCARCITY,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "The question is three claims — that issuance is fixed, that "
            "it is terminal, and that nobody can change it. Only the "
            "first is evidenced: a stated maximum, established for six "
            "assets. The schedule and who may rewrite it are absent for "
            "every one. Scoring the cap alone would answer a three-part "
            "question with one part and call the result monetary "
            "soundness."
        ),
        would_change=(
            "the issuance schedule and the process by which it could be "
            "changed, read from the protocol rather than asserted"
        ),
    ),
    CryptoQuestionKey.MONETARY_ADOPTION: ReadinessRuling(
        question=CryptoQuestionKey.MONETARY_ADOPTION,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "None of its three demands is bound to a source this "
            "platform reads. Holdings by long-term holders, value "
            "settled on the network and published reserve acceptance are "
            "all unacquired."
        ),
        would_change="any one of its three demands acquired",
    ),
    CryptoQuestionKey.NETWORK_SECURITY: ReadinessRuling(
        question=CryptoQuestionKey.NETWORK_SECURITY,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Fees are held for six assets and are one half of what "
            "security is paid with; the other half — issuance to block "
            "producers — is absent for all eight, as is who receives it "
            "and what an attack would cost. A security verdict from the "
            "smaller half of the budget would be a guess wearing a "
            "figure."
        ),
        would_change=(
            "issuance paid to block producers, and the cost of acquiring "
            "enough production to rewrite the ledger"
        ),
    ),
    CryptoQuestionKey.DECENTRALISATION: ReadinessRuling(
        question=CryptoQuestionKey.DECENTRALISATION,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Nothing is held. Block-production distribution, holding "
            "concentration and who may change the rules are unbound for "
            "every asset in the corpus."
        ),
        would_change="validator or holder concentration read from chain state",
    ),
    CryptoQuestionKey.USAGE: ReadinessRuling(
        question=CryptoQuestionKey.USAGE,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Transaction counts and active accounts are unbound for "
            "every asset. The one bound demand — value through a venue's "
            "own book — is a venue measure and answers venue activity, "
            "not whether a network is used."
        ),
        would_change="transaction counts or active accounts over a period",
    ),
    CryptoQuestionKey.ECONOMIC_ACTIVITY: ReadinessRuling(
        question=CryptoQuestionKey.ECONOMIC_ACTIVITY,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "Fees are held for six of eight assets and every one of them "
            "is a single provider's claim, which no rule here may read. "
            "The second demand states the other problem: one day is a "
            "reading and not a trend, and no longer window is acquired."
        ),
        would_change=(
            "a second independent fee source, and the same figure over a "
            "window longer than a day"
        ),
    ),
    CryptoQuestionKey.CAPITAL_COMMITTED: ReadinessRuling(
        question=CryptoQuestionKey.CAPITAL_COMMITTED,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "Capital held is read for seven of eight assets and all of "
            "it is one provider's aggregate. It is also a level that can "
            "leave in a day, so even corroborated it would need a window "
            "before it described anything durable."
        ),
        would_change=(
            "a second independent source, and the same measure over a "
            "period rather than at an instant"
        ),
    ),
    CryptoQuestionKey.ECOSYSTEM_ADOPTION: ReadinessRuling(
        question=CryptoQuestionKey.ECOSYSTEM_ADOPTION,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "What is deployed on a network and how that composition has "
            "moved are unbound. The aggregate capital figure hides "
            "exactly the distinction this question asks for."
        ),
        would_change="per-application holdings on the network, over a period",
    ),
    CryptoQuestionKey.SETTLEMENT_DEPENDENCY: ReadinessRuling(
        question=CryptoQuestionKey.SETTLEMENT_DEPENDENCY,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Which network a rollup settles to, what that costs and in "
            "whose asset are all unbound. The entity mapping records "
            "that Arbitrum's gas is paid in ETH; it holds no cost."
        ),
        would_change="settlement cost paid to the network beneath, over a period",
    ),
    CryptoQuestionKey.SEQUENCER_ECONOMICS: ReadinessRuling(
        question=CryptoQuestionKey.SEQUENCER_ECONOMICS,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Who operates the sequencer, what the operator earns and how "
            "operation could change hands are unbound for the one asset "
            "the question applies to."
        ),
        would_change="the margin between fees collected and settlement paid",
    ),
    CryptoQuestionKey.VENUE_ACTIVITY: ReadinessRuling(
        question=CryptoQuestionKey.VENUE_ACTIVITY,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "Hyperliquid's book and its open positions are both read and "
            "both are one provider's claim. The provider publishes "
            "derivatives volume only behind payment, so the larger half "
            "of the venue is missing from the smaller half's figure."
        ),
        would_change="a second independent venue source, including derivatives volume",
    ),
    CryptoQuestionKey.COMPETITIVE_POSITION: ReadinessRuling(
        question=CryptoQuestionKey.COMPETITIVE_POSITION,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "A share requires the venues competed with, and none is "
            "acquired. A volume figure alone says a venue won and not "
            "that it will keep winning."
        ),
        would_change="the same volume measure for competing venues, over a period",
    ),
    CryptoQuestionKey.PROTOCOL_CAPTURE: ReadinessRuling(
        question=CryptoQuestionKey.PROTOCOL_CAPTURE,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "What a protocol retains is read for the two assets the "
            "question applies to, from one provider, and what the "
            "retained share is spent on is absent for both."
        ),
        would_change="a second independent source for the retained share",
    ),
    CryptoQuestionKey.HOLDER_VALUE_ACCRUAL: ReadinessRuling(
        question=CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
        readiness=QualityReadiness.VISIBLE_NOT_SCORED,
        because=(
            "The acceptance case for this state. Hyperliquid's mechanism "
            "is evidenced in the provider's own words — 99% of perpetual "
            "and spot fees to an Assistance Fund that buys the token — "
            "and the amount beneath it is a single provider's claim. The "
            "mechanism and the amount are separate evidence and only the "
            "mechanism is settled, so the question is shown answered in "
            "kind and unscored in degree."
        ),
        would_change=(
            "a second independent source for the amount reaching holders, "
            "and whether the mechanism is fixed or discretionary"
        ),
    ),
    CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS: ReadinessRuling(
        question=CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS,
        readiness=QualityReadiness.NOT_READY,
        because=(
            "Governance rights, claims on fees or reserves, and whether "
            "either can be changed are unbound for every asset. "
            "'Nothing at all' is a legitimate answer to this question "
            "and this platform cannot yet distinguish it from not having "
            "looked."
        ),
        would_change="the token's rights read from the protocol's own documents",
    ),
}


def readiness_for(question: CryptoQuestionKey) -> ReadinessRuling:
    """Whether this question can carry a score — for any asset.

    **Takes the question and nothing else.** The structural guarantee
    beneath the ruling's tenth section: a function that could see a
    symbol or a figure would let a well-covered asset make a question
    scorable that stays unscorable for everything else, and the
    difference between *this platform cannot judge this yet* and *this
    asset does badly here* would quietly disappear.
    """

    return READINESS[question]


# ── the rule tables ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class QualityBand:
    """One row of a named rule table: a threshold and what it means."""

    #: The rule table's own word, carried into `Contribution.verdict`.
    verdict: str

    #: Points earned. Never negative — the platform's convention is that
    #: an adverse factor fails to earn rather than subtracts, so a
    #: reader seeing only positive numbers is not misled about what
    #: counted against.
    points: int

    sense: Sense

    #: The floor for this band, in the rule's own unit. None on the
    #: bottom row, which is reached by falling through.
    at_least: float | None

    #: What clearing this threshold means for an investor, in words.
    means: str


#: Points a single question can earn. Two rather than one so a rule can
#: express *clears the floor* and *is beyond the floor mattering* without
#: a second factor.
POINTS_PER_QUESTION = 2


@dataclass(frozen=True, slots=True)
class QualityRule:
    """A named, versioned rule table for one question.

    No score exists on this platform without one of these. The version
    is part of the identity: a re-banding is a different rule, and a
    verdict recorded under version 1 is not comparable with one under
    version 2 merely because both say "adequate".
    """

    question: CryptoQuestionKey
    name: str
    version: str

    #: What the rule reads, named as a fact rather than as a verdict.
    measures: str

    #: The investor's question in the form this rule actually answers —
    #: which is narrower than the S3 question, and saying so is the
    #: point.
    answers: str

    bands: tuple[QualityBand, ...]

    #: The measurement the thresholds came from. Dated, and naming the
    #: sample, because a band with no measured basis is a preference.
    measured_basis: str

    def band_for(self, value: float) -> QualityBand:
        """The row this value falls in. Bands are ordered high to low."""

        for band in self.bands:
            if band.at_least is None or value >= band.at_least:
                return band

        return self.bands[-1]


#: Market significance, as a floor test rather than as a ranking.
#:
#: The investor question is not *is it big* but *is it big enough that
#: its price means something and a serious position is not the market*.
#: That question saturates: Bitcoin at $1,307bn is not twenty-nine times
#: sounder than Solana at $45bn, and a rule that scored it that way
#: would be reporting size as quality.
MARKET_ROBUSTNESS_RULE = QualityRule(
    question=CryptoQuestionKey.MARKET_ROBUSTNESS,
    name="market-significance-floor",
    version="1",
    measures="the established market capitalisation of the asset",
    answers=(
        "whether the market in this asset is large enough that its price "
        "is a valuation rather than a quotation"
    ),
    bands=(
        QualityBand(
            verdict="robust",
            points=2,
            sense=Sense.FAVOURABLE,
            at_least=10_000_000_000,
            means=(
                "among the largest assets in the class, with markets deep "
                "enough that no single venue or holder defines the price"
            ),
        ),
        QualityBand(
            verdict="adequate",
            points=1,
            sense=Sense.NEUTRAL,
            at_least=500_000_000,
            means=(
                "large enough to have several independent markets, and "
                "small enough that a large holder still matters"
            ),
        ),
        QualityBand(
            verdict="fragile",
            points=0,
            sense=Sense.ADVERSE,
            at_least=None,
            means=(
                "small enough that one venue's withdrawal or one holder's "
                "exit is a material part of the market"
            ),
        ),
    ),
    measured_basis=(
        "CoinGecko's 250 largest assets, read 2026-08-10. The page spans "
        "$115m to $1,307bn with a median of $307m. $10bn is its 95th "
        "percentile — measured at $8.998bn, rank 13 — and 11 of 250 clear "
        "it; $500m is cleared by 99 of 250. Both thresholds sit in sparse "
        "parts of a heavily skewed distribution, which is why the rule "
        "holds still: a uniform 30% market fall re-bands 18 of 250 assets "
        "(7.2%), and a 50% fall re-bands 35 (14.0%). The thresholds the "
        "platform inherited were $10bn and $1bn; the upper one survives "
        "the measurement and the lower one does not, because $1bn calls "
        "74% of the 250 largest assets fragile and 'extremely small' is "
        "the fragility the question is about."
    ),
)


#: Every rule this model holds. One, and the number is the finding.
RULES: dict[CryptoQuestionKey, QualityRule] = {
    MARKET_ROBUSTNESS_RULE.question: MARKET_ROBUSTNESS_RULE,
}


# ── what the model produces ──────────────────────────────────────────


class QuestionParticipation(StrEnum):
    """How one question participates in one asset's quality.

    The join of applicability and readiness, computed rather than
    declared — which is what keeps a question that does not apply to an
    archetype from ever being reported as evidence this platform lacks.
    """

    #: Applies, is scorable, and was answered from established evidence.
    SCORED = "scored"

    #: Applies and is scorable, and this asset's evidence does not reach
    #: the standing the rule requires. Contributes nothing and counts
    #: against coverage, never against quality.
    SCORABLE_UNANSWERED = "scorable_unanswered"

    #: Applies, and evidence is shown without a score.
    SHOWN = "shown"

    #: Applies, and nothing answers it.
    UNANSWERABLE = "unanswerable"

    #: Applies, and its answer is not part of quality.
    OUTSIDE = "outside"

    #: The wrong question for this kind of asset.
    NOT_APPLICABLE = "not_applicable"

    #: No archetype was established, so whether it applies is unknown.
    UNDETERMINED = "undetermined"

    @property
    def stated(self) -> str:
        return _PARTICIPATION[self]


_PARTICIPATION = {
    QuestionParticipation.SCORED: "Scored",
    QuestionParticipation.SCORABLE_UNANSWERED: "Scorable, unanswered",
    QuestionParticipation.SHOWN: "Shown, not scored",
    QuestionParticipation.UNANSWERABLE: "Not yet answerable",
    QuestionParticipation.OUTSIDE: "Outside asset quality",
    QuestionParticipation.NOT_APPLICABLE: "Not applicable",
    QuestionParticipation.UNDETERMINED: "Undetermined",
}


@dataclass(frozen=True, slots=True)
class QualityAnswer:
    """What one question came to for one asset, and on what."""

    question: CryptoQuestionKey
    participation: QuestionParticipation

    #: The rule that produced a verdict, where one did.
    rule: QualityRule | None = None
    band: QualityBand | None = None

    #: The figure the rule read, and where it came from.
    value: float | None = None
    source: str | None = None

    #: The sentence an investor reads.
    stated: str = ""

    #: Why this question came to what it came to — the readiness ruling
    #: where nothing was scored, the rule and the threshold where
    #: something was.
    because: str = ""

    #: Evidence held but not scored, worded with its standing. The
    #: content of `SHOWN`, and the reason a claimed figure can be seen
    #: without being counted.
    shown: tuple[str, ...] = ()

    @property
    def points(self) -> int:
        return self.band.points if self.band is not None else 0

    @property
    def scored(self) -> bool:
        return self.participation is QuestionParticipation.SCORED


@dataclass(frozen=True, slots=True)
class QualityCoverage:
    """How much of what was asked could be judged. Never a quality claim.

    Two ratios because they answer different questions, and one alone
    always misleads. `answered / scorable` measures this asset's
    evidence; `scorable / in_scope` measures this platform's model, and
    today it is the small one.
    """

    applicable: int
    scorable: int
    answered: int

    shown: int
    unanswerable: int
    outside: int

    #: Questions whose applicability the archetype could not settle.
    #: Counted, and counted *against* reach rather than excluded from
    #: it. Excluding them rewarded the one asset with no established
    #: archetype: Bittensor was asked four questions instead of
    #: nineteen and came out the best-covered security in the corpus,
    #: which inverted the finding — not knowing what an asset is cannot
    #: be a form of knowing about it.
    undetermined: int = 0

    @property
    def in_scope(self) -> int:
        """Every question that applies, plus every one that might.

        The honest denominator. A question refused by an established
        archetype is out of scope for a real reason; a question left
        undetermined is out of scope because nothing was established,
        and those are opposite facts.
        """

        return self.applicable + self.undetermined

    @property
    def model_reach(self) -> float:
        """The share of this asset's questions the model can score at all."""

        return self.scorable / self.in_scope if self.in_scope else 0.0

    @property
    def evidence_reach(self) -> float:
        """The share of scorable questions this asset's evidence answered."""

        return self.answered / self.scorable if self.scorable else 0.0

    @property
    def judged_reach(self) -> float:
        """The share of everything in scope that was actually judged."""

        return self.answered / self.in_scope if self.in_scope else 0.0


#: How many scored questions a headline band requires.
#:
#: Two, inherited unchanged from the factor quorum the crypto signal
#: already enforced and from `MINIMUM_ANSWERED` on the company side. One
#: reading is as easily a gap as a verdict, and the asset judged on a
#: single factor was the defect that put the quorum there. Raising or
#: lowering it is a scoring-contract change and is not S5's to make.
MINIMUM_SCORED = 2


@dataclass(frozen=True, slots=True)
class CryptoAssetQuality:
    """One asset's quality: the questions, the answers, and what is missing."""

    symbol: str

    #: Every question, in declaration order, with how it participated.
    answers: tuple[QualityAnswer, ...]

    coverage: QualityCoverage

    #: HIGH, MEDIUM, LOW — or UNKNOWN, which is not a low score and is
    #: never produced by an asset's evidence being poor.
    quality: str

    confidence: int

    #: Why the headline is what it is, including why it is absent.
    because: str

    earned: int = 0
    available: int = 0

    @property
    def scored(self) -> tuple[QualityAnswer, ...]:
        return tuple(answer for answer in self.answers if answer.scored)

    @property
    def visible(self) -> tuple[QualityAnswer, ...]:
        """Answers with evidence worth showing, scored or not."""

        return tuple(
            answer
            for answer in self.answers
            if answer.participation
            in (QuestionParticipation.SCORED, QuestionParticipation.SHOWN)
        )


#: How earned points become a band, once the quorum is met.
#:
#: **Unexercised on the current corpus.** One question is scorable, the
#: quorum is two, and no asset reaches this table today. It is stated
#: rather than left implicit so that the first slice to make a second
#: question scorable finds a named rule to argue with — and it must be
#: re-measured then, because a mapping that has never run on real inputs
#: is a design, not a measurement.
HEADLINE_BANDS = (
    (0.75, "HIGH"),
    (0.35, "MEDIUM"),
    (0.0, "LOW"),
)


def headline_for(earned: int, available: int) -> str:
    """The band a share of the available points falls in."""

    if available <= 0:
        return "UNKNOWN"

    share = earned / available

    for floor, band in HEADLINE_BANDS:
        if share >= floor:
            return band

    return "LOW"
