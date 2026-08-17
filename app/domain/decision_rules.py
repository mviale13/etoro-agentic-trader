"""Every rule that gives a decision input its investment meaning, named.

The Decision Philosophy Audit (`DECISION_PHILOSOPHY_AUDIT.md`) traced
every value that can change `ArtificialCIO.decide()` to its origin and
found eighteen decision-bearing transformations, of which one has a
licensed basis, one has a written argument, and sixteen are unsourced
constants. This module is the audit's smallest consequence: **each of
those transformations becomes a named, versioned identity that travels
with the value it produced**, so a score can answer *which exact rule,
and which version of it, gave this number its investment meaning* —
without anyone reading source code.

**Naming a rule does not validate it.** That sentence is load-bearing
and it is enforced in the types: every rule carries a `RuleStatus`, the
statuses preserve the audit's three-way distinction — licensed, argued,
unsourced — and a version says *this result was produced under this
exact rule*, never *this is the correct way to invest*. Sixteen of the
seventeen rules below are `UNSOURCED`, and registering them here changed
nothing about that: the FAIR wall still stands, the dividend wall still
stands, momentum is still one day's price move, and each of those facts
is now addressable instead of anonymous.

**The registry is data, and the constants stay where they live.** A rule
here names a behaviour; the thresholds implementing it remain in their
owning module, because moving them would be a change to who owns them.
What binds the two is the provenance test's fingerprint: every rule's
governed constants are hashed, and the pinned (key, version,
fingerprint) triple means a threshold cannot move under an unchanged
version, and a version cannot move under unchanged behaviour, without a
test failing — the same discipline committee contracts earned in #113.

Rule granularity follows the audit, not the literals: one rule per
behaviour that can reasonably evolve as a single policy decision. The
provider quality triad is one rule (its points, band and score map move
together); the risk bands and the risk severities are two (rebanding
volatility and re-pricing a band are different decisions).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuleStatus(StrEnum):
    """How far the rule's investment rationale is established.

    The audit's three-way distinction, kept structural so that naming a
    rule cannot quietly upgrade it. `LICENSED` is earned by measurement
    and cited; `ARGUED` has a written rationale at the implementation;
    `UNSOURCED` is existing behaviour, named so it can be examined.
    """

    #: A measured, cited basis established the meaning — the standard
    #: the crypto side's rules already meet.
    LICENSED = "licensed"

    #: A written rationale argues the choice at the implementation
    #: site. An argument is not a measurement.
    ARGUED = "argued"

    #: Existing behaviour with no established rationale. Most of the
    #: registry, and the point of building it.
    UNSOURCED = "unsourced"

    @property
    def stated(self) -> str:
        return {
            RuleStatus.LICENSED: (
                "licensed — a measured, cited basis established this meaning"
            ),
            RuleStatus.ARGUED: (
                "argued — a written rationale exists at the implementation; "
                "an argument is not a measurement"
            ),
            RuleStatus.UNSOURCED: (
                "unsourced — existing behaviour whose investment rationale "
                "nobody has established"
            ),
        }[self]


class RuleKind(StrEnum):
    """Whether the rule interprets evidence or governs a decision."""

    #: Turns a reading into a meaning or a number: a band, a score map,
    #: a confidence formula.
    INTERPRETS_EVIDENCE = "interprets_evidence"

    #: Turns numbers into a state, an action flag or a cap: a gate, a
    #: vote threshold, a veto mapping.
    GOVERNS_DECISION = "governs_decision"


@dataclass(frozen=True, slots=True)
class DecisionRule:
    """One named, versioned decision-bearing rule.

    Identity, not endorsement. Two of these are the same rule exactly
    when key and version agree — which is what lets a result produced
    last month answer whether today's rule is the one that produced it.
    """

    key: str
    version: int
    status: RuleStatus
    kind: RuleKind

    #: Why the status is what it is — the licensor, the argument's
    #: location, or the honest absence. One sentence, for a surface or
    #: a reviewer; never consulted by any code path.
    because: str

    @property
    def identity(self) -> str:
        return f"{self.key}@{self.version}"

    @property
    def stated(self) -> str:
        return f"{self.identity} ({self.status.value})"


def _interprets(key: str, status: RuleStatus, because: str) -> DecisionRule:
    return DecisionRule(
        key=key,
        version=1,
        status=status,
        kind=RuleKind.INTERPRETS_EVIDENCE,
        because=because,
    )


def _governs(
    key: str,
    status: RuleStatus,
    because: str,
    version: int = 1,
) -> DecisionRule:
    return DecisionRule(
        key=key,
        version=version,
        status=status,
        kind=RuleKind.GOVERNS_DECISION,
        because=because,
    )


_AUDIT = "unsourced existing behaviour; measured in DECISION_PHILOSOPHY_AUDIT.md"

# ── the interpretation rules ────────────────────────────────────────

#: Volatility and drawdown → LOW/MODERATE/HIGH/SEVERE.
RISK_BANDS = _interprets("risk-bands", RuleStatus.UNSOURCED, _AUDIT)

#: A risk level → a severity constant → the risk score.
RISK_SEVERITY = _interprets(
    "risk-severity",
    RuleStatus.ARGUED,
    "argued in risk_signal.py: SEVERE is placed above the policy's "
    "maximum acceptable risk deliberately, so a security that swings "
    "that hard is rejected on its own record",
)

#: Forward P/E → CHEAP/FAIR/EXPENSIVE.
PE_BANDS = _interprets("pe-bands", RuleStatus.UNSOURCED, _AUDIT)

#: CHEAP/FAIR/EXPENSIVE → 80/55/25. Jointly with the decision gates,
#: this is the FAIR wall: FAIR scores below the recommendation gate.
VALUATION_SCORES = _interprets("valuation-scores", RuleStatus.UNSOURCED, _AUDIT)

#: The provider triad — market cap, earnings, dividend — its points,
#: its bands and its score map. One rule: they move together, and
#: jointly they are the dividend wall.
PROVIDER_QUALITY = _interprets("provider-quality", RuleStatus.UNSOURCED, _AUDIT)

#: The filing-grounded quality band: favourable share of answered
#: factors, minimum answered, and the shared score ruler.
QUALITY_GROUNDED = _interprets(
    "quality-grounded",
    RuleStatus.LICENSED,
    "licensed by GROUNDED_BUSINESS_QUALITY.md (#81): factors chosen by "
    "measurement over 24 companies, absences refused rather than scored",
)

#: Monetary values compare only under identical explicit
#: denominations. The size threshold is declared USD; a magnitude
#: established in any other currency is refused pending a separately
#: authorised conversion, and an undenominated magnitude is refused
#: outright — absence of denomination is not permission to inherit one.
MONETARY_COMPARISON = _interprets(
    "monetary-comparison",
    RuleStatus.ARGUED,
    "argued in MARKET_CAP_DENOMINATION.md (#142): no provider field "
    "states a market cap's denomination, and BP.L quotes in pence, "
    "reports in dollars and carries a cap in pounds — so inheritance "
    "from any neighbouring currency field picks a wrong answer for a "
    "held security, and only identical explicit denominations compare",
)

#: The one authorised exception to identical-denominations-only: an
#: established foreign magnitude may compare through an explicit,
#: evidenced FX translation into the threshold's currency. The rule
#: owns the translatable set (the four measured foreign denominations
#: against USD), the temporal requirement (rate and subject observed
#: on one UTC day — the daily cadence both stores declare, and the
#: finest rule the held evidence supports), and the two refusals that
#: never soften: a missing rate is never 1:1, and a rate from another
#: day is never "latest".
FX_TRANSLATION = _interprets(
    "fx-translation",
    RuleStatus.ARGUED,
    "argued in MONETARY_TRANSLATION.md (C6): a translated amount is a "
    "derived claim that carries its own evidence — direction fixed at "
    "construction, rate dated and sourced, same-UTC-day with the "
    "figure it translates — and translation is a fourth crossing that "
    "can never rescue identity, magnitude or denomination, because "
    "the comparison consults it only after all three hold",
)

#: Whether Quality may band a business at all: every applicable
#: factor read, or no band.
#:
#: A rule apart from `provider-quality`, whose points, bands and score
#: map are untouched — this decides only whether that ruler runs. #140
#: measured that every partial alternative (relative performance, a
#: coverage floor, a breadth floor) lets deleting a factor move the
#: band's direction, while requiring the whole applicable set leaves a
#: deletion no direction to move.
QUALITY_AUTHORITY = _interprets(
    "quality-authority",
    RuleStatus.ARGUED,
    "argued in QUALITY_BAND_RULER.md (#140): a band earned over part "
    "of the question set describes the reading rather than the "
    "business — measured, 33 securities passed every readable factor "
    "and banded LOW, indistinguishable from the 9 that failed theirs",
)

#: One day's price change → BULLISH/NEUTRAL/BEARISH.
MOMENTUM_BANDS = _interprets("momentum-bands", RuleStatus.UNSOURCED, _AUDIT)

#: Which provider translations Momentum will read as a price move at
#: all — the eligibility question, upstream of the bands.
#:
#: **A separate rule rather than momentum-bands@2**, because the two
#: are independently evolvable and conflating them would misdescribe
#: what changed: the bands did not move, and re-versioning them would
#: claim they had. Admitting a warrant and moving a threshold are
#: different acts with different evidence, and each must be able to
#: happen without implying the other.
#: Which market-cap magnitudes may be compared with an absolute size
#: threshold at all — eligibility, upstream of `provider-quality`'s
#: bands and separately fingerprinted from them.
#:
#: A second rule for the same reason `momentum-input-eligibility` is
#: one: the size threshold did not move, and re-versioning
#: `provider-quality` would claim its ruler had changed when only the
#: admissibility of its input did.
MARKET_CAP_INPUT_ELIGIBILITY = _interprets(
    "market-cap-input-eligibility",
    RuleStatus.ARGUED,
    "argued in quality_signal_service.py: an absolute threshold "
    "comparison has no scale invariance to protect it, and measured "
    "over the live corpus 57 of 72 magnitudes sit within a factor of "
    "100 of the line while 17 are denominated in a currency this "
    "platform never reads — so an assumed translation can change which "
    "side of the threshold a company falls on",
)

MOMENTUM_INPUT_ELIGIBILITY = _interprets(
    "momentum-input-eligibility",
    RuleStatus.ARGUED,
    "argued in momentum_signal_service.py: a daily change is a ratio "
    "over two closes of one series and is invariant under any linear "
    "rescaling of it, so the unit and currency an ASSUMED warrant "
    "leaves open cannot corrupt this quantity — while UNKNOWN, which "
    "leaves the reading's identity unsettled, is refused",
)

#: The vote's strength → the recommendation's confidence.
VOTE_CONFIDENCE = _interprets("vote-confidence", RuleStatus.UNSOURCED, _AUDIT)

#: Account concentration, market quote coverage and a constant,
#: averaged into the cognitive confidence.
COGNITIVE_CONFIDENCE = _interprets("cognitive-confidence", RuleStatus.UNSOURCED, _AUDIT)

#: Cognitive confidence and the vote's confidence → the evidence score,
#: with the unevidenced haircut.
EVIDENCE_SCORE = _interprets("evidence-score", RuleStatus.UNSOURCED, _AUDIT)

#: Policy rooms → the portfolio fit score. The rooms are the investor's
#: own policy; the mean over them is this platform's.
PORTFOLIO_FIT = _interprets("portfolio-fit", RuleStatus.UNSOURCED, _AUDIT)

# ── the decision rules ──────────────────────────────────────────────

#: Three signal bands, weighted 0.40/0.35/0.25, thresholded into
#: BUY/HOLD/SELL.
SIGNAL_VOTE = _governs("signal-vote", RuleStatus.UNSOURCED, _AUDIT)

#: Whether a computed direction may be acted on: every applicable
#: signal established, and at least two of them expressing a reading.
#:
#: A rule apart from `signal-vote` because it answers a different
#: question — the vote says what the evidence points at, this says
#: whether enough of the expected evidence is in hand to act. The
#: weights and the BUY/SELL thresholds are untouched by it.
DECISION_AUTHORITY = _governs(
    "decision-authority",
    RuleStatus.ARGUED,
    "argued in DECISION_KERNEL_ALGEBRA.md (#138): measured over 64 "
    "readings, relative coverage below 1.00 lets a deletion still "
    "reach a decisive call, and relative coverage alone makes a fund "
    "actionable on one signal because a one-signal expected set is "
    "100% covered by construction — so the two gates are independent",
)

#: The nine ordered gates and the policy thresholds they read.
#:
#: **@2** — the thresholds are untouched; what a gate *reads* changed.
#: The security-evidence gate tested the provider-fed analysis alone, so
#: a company whose own statements had reached quorum fell through it and
#: the case was worded "there is nothing to base a decision on" beside
#: the grounded band the same page printed. A quorate grounded
#: assessment is now security-level evidence, and the gate order, the
#: policy constants and every other gate are as they were.
DECISION_GATES = _governs(
    "decision-gates",
    RuleStatus.UNSOURCED,
    _AUDIT + "; evidence input widened in DECISION_EVIDENCE_CONVERGENCE.md",
    version=2,
)

#: The unweighted mean of present scores, capped by state.
#:
#: **@2** — the mean itself is unchanged. What changed is its licence to
#: speak: a case citing no supporting reason is left without a number
#: rather than given one. Four holdings each printed 64 beside an empty
#: `because` and a rationale saying no basis existed, two of them from a
#: two-term mean and two from a three-term one — agreement by
#: coincidence, read by an investor as a measurement.
CONVICTION_MEAN = _governs(
    "conviction-mean",
    RuleStatus.UNSOURCED,
    _AUDIT + "; withheld without a supporting reason, DECISION_EVIDENCE_CONVERGENCE.md",
    version=2,
)

#: A BUY vote is the execution trigger — the final gate to RECOMMEND.
ACTIONABLE_BUY = _governs("actionable-buy", RuleStatus.UNSOURCED, _AUDIT)

#: A SELL vote is an analyst veto — REJECT, ahead of every score.
VETO_SELL = _governs("veto-sell", RuleStatus.UNSOURCED, _AUDIT)


#: Every rule, by key. The registry a test can walk and a surface can
#: quote; adding a decision-bearing threshold without registering it
#: here is what the provenance guards exist to catch.
DECISION_RULES: dict[str, DecisionRule] = {
    rule.key: rule
    for rule in (
        RISK_BANDS,
        RISK_SEVERITY,
        PE_BANDS,
        VALUATION_SCORES,
        PROVIDER_QUALITY,
        QUALITY_AUTHORITY,
        MONETARY_COMPARISON,
        FX_TRANSLATION,
        QUALITY_GROUNDED,
        MOMENTUM_BANDS,
        MOMENTUM_INPUT_ELIGIBILITY,
        MARKET_CAP_INPUT_ELIGIBILITY,
        VOTE_CONFIDENCE,
        COGNITIVE_CONFIDENCE,
        EVIDENCE_SCORE,
        PORTFOLIO_FIT,
        SIGNAL_VOTE,
        DECISION_AUTHORITY,
        DECISION_GATES,
        CONVICTION_MEAN,
        ACTIONABLE_BUY,
        VETO_SELL,
    )
}
