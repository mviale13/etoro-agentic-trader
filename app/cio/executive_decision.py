from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState
from app.domain.asset_class import AssetClass
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.finding import FindingLedger
from app.domain.provenance import Provenance
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
    security_evidenced: bool = True

    #: What kind of asset this is. The Artificial CIO needs it to tell a
    #: measurement that has not arrived from a question that does not
    #: apply: a token has no business quality, and never will.
    asset_class: AssetClass | None = None

    actionable_now: bool = False
    hard_reject: bool = False
    analyst_veto: bool = False

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


class ExecutiveDecision(BaseModel):
    """Final explainable decision produced by the Artificial CIO."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    state: DecisionState
    conviction: int = Field(ge=0, le=100)

    rationale: str
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

    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def belongs_to_watchlist(self) -> bool:
        return self.state.belongs_to_watchlist
