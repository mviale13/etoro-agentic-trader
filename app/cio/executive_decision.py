from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState
from app.domain.asset_class import AssetClass
from app.domain.business_quality import BusinessQuality
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.decision_blocker import DecisionBlocker
from app.domain.decision_rules import DecisionRule
from app.domain.finding import FindingLedger
from app.domain.provenance import Provenance
from app.domain.risk_signal import RiskSignal
from app.domain.score_basis import ScoreBases


class DecisionEvidence(BaseModel):
    """
    Normalized evidence consumed by the Artificial CIO.

    A score of None means the platform did not measure it. It never means
    zero, and it is never filled in from something else: a gate that was not
    measured cannot be cleared, so the investment case simply does not
    progress past the point where that measurement is required.
    """

    # An unrecognised field is an error, not something to drop quietly.
    # While this model accepted extras, `strengths=(...)` went on being
    # passed after the field was renamed and simply vanished — evidence
    # that was gathered, handed over, and silently reported as absent.
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(min_length=1)

    quality_score: int | None = Field(default=None, ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    valuation_score: int | None = Field(default=None, ge=0, le=100)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    #: How much room the portfolio has for this security, under the
    #: investor's own policy. None when the policy states no limit this
    #: could be measured against.
    portfolio_fit_score: int | None = Field(default=None, ge=0, le=100)

    #: Why each score above is the number it is: the reading under it, the
    #: band this platform applied, and the findings the reading rests on.
    #:
    #: The Artificial CIO does not read this — it gates on the scores. It
    #: rides here because the score and the reason for it must travel
    #: together: a band is a house rule, and a rule the investor cannot
    #: see is indistinguishable from a measurement.
    #:
    #: None only where a caller built evidence without stating one.
    score_bases: ScoreBases | None = None

    @property
    def safety_score(self) -> int | None:
        """
        The risk score, turned the way every other score here runs.

        Risk is the one measurement on this platform where a high number is
        bad, and a dashboard that mixes directions cannot be read: four
        nineties do not average to anything meaningful if one of them means
        the opposite of the other three. The Artificial CIO already knew
        this — it inverted risk before averaging into conviction — but it
        did so inline, so the concept existed without a name and every
        other surface went on showing the raw, inverted figure.

        The gates still read `risk_score`. A ceiling on risk is the natural
        way to write "this is too dangerous", and rewriting it as a floor
        on safety would restate one policy in two directions.

        None stays None. A risk nobody measured is not a safe security, and
        `100 - nothing` would be the most dangerous number this platform
        could print.
        """

        return None if self.risk_score is None else 100 - self.risk_score

    #: When the security's own evidence was read.
    #:
    #: The portfolio and market readings behind this case are not dated —
    #: they come from eToro, whose fetch time nothing records yet — so this
    #: covers the security's evidence and says so rather than standing for
    #: the whole case.
    evidence_as_of: Provenance | None = None

    #: Whether the Brain held any security-level evidence for this symbol.
    #:
    #: False when nothing about the security itself was gathered — the
    #: symbol names nothing the platform could describe, so the quote and
    #: fundamentals were never fetched. This is a different situation from a
    #: security that was looked at and whose quality simply could not be
    #: measured, and the two must not share a rationale: one says "we have
    #: no analysis of this"; the other says "we analysed it and this part
    #: was unavailable".
    #:
    #: *Any* is the whole of it, and it used to be keyed to one half. This
    #: read `company is not None` — the provider-fed analysis alone — so a
    #: company whose own audited statements had reached quorum and banded
    #: was reported as a security the platform held nothing about. UNP
    #: printed a grounded MEDIUM 62 on the same page as "there is nothing
    #: to base a decision on".
    security_evidenced: bool = True

    #: The grounded quality assessment governing this case, where the
    #: company's statements reached quorum.
    #:
    #: Carried so that the gate, the rationale and the review condition
    #: read the one object the scores section renders. It is not a second
    #: quality result and nothing re-derives a band from it: the score
    #: above was computed from this very object, and this is that object
    #: rather than a copy of its conclusion. One rendered page cannot
    #: contradict itself about quality if there is only one quality to
    #: read.
    #:
    #: None where no such assessment exists — no statements, or none at
    #: quorum — which is the state where a provider proxy legitimately
    #: stands in.
    grounded_quality: BusinessQuality | None = None

    #: What kind of asset this is. The Artificial CIO needs it to tell a
    #: measurement that has not arrived from a question that does not
    #: apply: a token has no business quality, and never will.
    asset_class: AssetClass | None = None

    #: The security's own risk reading, carried whole rather than as the
    #: score derived from it.
    #:
    #: `risk_score` is a band's severity turned into a number, and the
    #: number alone cannot say what was measured: 85 is the SEVERE band,
    #: and *why* AMD sits in it — 71.8% annualised volatility over the
    #: past year — lives here. The gate still reads the score and only
    #: the score, so nothing about the decision moves; this is what lets
    #: the refusal name the reading instead of a surface guessing at it
    #: or a sentence being reassembled by parsing prose. None where
    #: nothing measured it.
    risk_reading: RiskSignal | None = None

    hard_reject: bool = False

    #: Every finding read about this security, favourable or not.
    #:
    #: This was called `strengths`, and it never was. It carries whatever
    #: the signals measured — "Large-cap company." sits beside "Negative
    #: earnings." and "Insufficient quality data." — so anything that
    #: presented it as a list of strengths would be reporting an absent
    #: measurement as a reason to invest.
    evidence_weighed: tuple[str, ...] = ()

    #: The findings that argue for this security, and only those. The name
    #: is safe to use again: the signals now state the sense they read each
    #: finding with, so this is a selection rather than the whole list
    #: wearing a flattering label.
    strengths: tuple[str, ...] = ()

    #: The findings that argue against this security.
    risks: tuple[str, ...] = ()

    #: The canonical findings themselves, each addressable.
    #:
    #: `evidence_weighed`, `strengths` and `risks` above are this
    #: ledger flattened to text, kept because every existing surface
    #: reads them. They are a projection, not a second source: anything
    #: that needs to know which reading produced a finding, or to point
    #: at one without restating it, asks the ledger.
    findings: FindingLedger = FindingLedger()

    #: What each committee concluded, and on which findings.
    #:
    #: Carried on the evidence so the Artificial CIO can preserve them
    #: verbatim on the decision. A committee's position is part of the
    #: record of how a decision was reached, and a record that kept
    #: only the outcome could never show that a committee dissented.
    opinions: tuple[CommitteeOpinion, ...] = ()

    #: Risks belonging to the account and the market rather than to the
    #: security, plus the behavioural risks of acting against policy.
    #: Identical under every symbol, and kept apart for that reason.
    context_risks: tuple[str, ...] = ()

    missing_evidence: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()

    next_trigger: str | None = None

    #: The named, versioned rules the builder applied in producing this
    #: evidence's action flags — today, the BUY-is-actionable and
    #: SELL-is-veto mappings. Identity, never endorsement: the score
    #: rules ride on `score_bases`, each beside the number it produced.
    rules: tuple[DecisionRule, ...] = ()


class ExecutiveDecision(BaseModel):
    """Final explainable decision produced by the Artificial CIO."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    state: DecisionState

    #: How much conviction this case carries, or nothing at all.
    #:
    #: None where the decision cites no supporting reason. Four companies
    #: with wildly different evidence — a freshly-banded railroad, a
    #: semantically-refused bank, a stale industrial, a deadlocked staple —
    #: each printed 64 beside an empty `key_strengths`, an empty
    #: `evidence_weighed` and a rationale saying no basis existed. A number
    #: standing next to "nothing" is confidence nobody computed.
    #:
    #: Never zero in its place: zero is the lowest conviction on the scale,
    #: which is itself a judgment, and this is the absence of one. Same rule
    #: as every score on `DecisionEvidence`, for the same reason.
    conviction: int | None = Field(default=None, ge=0, le=100)

    #: What the number above is, in words: how it was computed, which
    #: state capped it, and under which rule.
    #:
    #: A conviction printed alone reads as enthusiasm. AMD's is 40 — the
    #: REJECT cap of `conviction-mean@1`, not a measurement that came out
    #: at 40 — and the two are indistinguishable without this. Empty only
    #: where a caller built a decision without stating one.
    conviction_basis: str = ""

    #: How many score families produced a score for this decision, and
    #: how many `conviction-mean@1` expects. Carried on the decision
    #: rather than left to be re-derived elsewhere, so the count the
    #: sentence above states is checkable against the decision that
    #: stated it. None where a caller built a decision without a
    #: conviction reading at all.
    conviction_participating: int | None = None
    conviction_expected: int | None = None

    #: The score families that produced nothing here, named. An absent
    #: score is missing evidence and never a low score: this bounds what
    #: the conviction covers, and no consumer may read it as an adverse
    #: finding about the security.
    conviction_absent_families: tuple[str, ...] = ()

    rationale: str

    #: What stands between this case and its next state, named by the
    #: gate that stopped it rather than inferred from the state.
    #:
    #: None where a caller built a decision without one; a decision that
    #: cleared every gate carries `DecisionBlocker.none()`, which is a
    #: sentence rather than an absence.
    blocker: DecisionBlocker | None = None

    evidence_as_of: Provenance | None = None
    evidence_weighed: tuple[str, ...] = ()
    key_strengths: tuple[str, ...] = ()
    key_risks: tuple[str, ...] = ()

    #: The findings this decision was reached over, addressable, and the
    #: committee positions taken on them — preserved verbatim, including
    #: the ones that did not prevail. A decision that recorded only its
    #: own outcome could be read but not audited.
    findings: FindingLedger = FindingLedger()
    opinions: tuple[CommitteeOpinion, ...] = ()
    context_risks: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()

    next_trigger: str | None = None

    #: The named, versioned rules this decision was reached under — the
    #: gate procedure and the conviction arithmetic. *Produced under
    #: this exact rule*, never *this is the correct way to invest*.
    decided_under: tuple[DecisionRule, ...] = ()

    #: The exact records this decision rests on, where it rests on
    #: records that carry their own identity.
    #:
    #: Empty for a decision reached from scores: those are computed from
    #: readings that have no stable identity of their own, and inventing
    #: one to fill this field would claim a traceability that does not
    #: exist. A decision that *does* name its sources can be compared
    #: against an earlier one exactly — which is what lets the journal
    #: tell *the same answer from the same evidence* from *the same
    #: answer from new evidence*.
    evidence_records: tuple[str, ...] = ()

    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def belongs_to_watchlist(self) -> bool:
        return self.state.belongs_to_watchlist
