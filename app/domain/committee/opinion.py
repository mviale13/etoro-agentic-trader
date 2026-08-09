"""What one committee thinks, stated so the Executive layer can weigh it.

A committee used to emit a recommendation, a confidence float and a
sentence. Three of those four things were a score, and the fourth was
written by the committee itself — so the Executive layer could report
*that* two committees agreed but never *why*, and an investor reading
the dossier met a verdict with no visible argument under it.

This is the replacement: a deterministic object that states a position
and shows the evidence it stands on, by reference.

## Four rules that shape it

**A committee advises; it never decides.** Constitution §9. The old
object's `Recommendation` — `STRONG_BUY`, `SELL` — was a committee
naming an action, which is the Artificial CIO's word to say. `Stance`
replaces it, and replaces it rather than joining it: two enumerations
for *what this committee thinks* would be the duplication invariant 9
exists to prevent.

**Polarity is never invented.** Supporting and opposing evidence are
selections over findings whose `Sense` the producing signal recorded
at the moment it read them. This object classifies nothing: it counts
what the signals already said, and a stance is a named rule applied to
those counts.

**Evidence is referenced, never restated.** `supporting` and
`opposing` carry `Finding.ref` addresses into the case's own ledger.
A committee that carried its own prose could state something the
platform never read, and no surface downstream could tell the
difference.

**Not knowing is not a position.** A committee with nothing in its
remit abstains, with the reason worded — it does not return NEUTRAL.
The platform has paid for this distinction twice already: a Risk
Committee returning HOLD read as *risk is acceptable*, which is a
claim, and the same committee returning confidence `0.0` dragged
committee agreement down as though it had objected. `stance=None` says
the committee did not speak. It is not a sixth stance and it never
averages.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.finding import Dimension


class Stance(StrEnum):
    """A committee's position on the security, and only a position.

    Five values, symmetric about neutral. Nothing here names an action:
    a stance is what a committee thinks, and what to *do* about it is
    resolved one layer up, against policy and the portfolio, by the
    Artificial CIO.
    """

    STRONGLY_POSITIVE = "strongly_positive"
    POSITIVE = "positive"

    #: Read, and it argues neither way. Never the answer to *nothing was
    #: read* — that is an abstention, and it is `stance=None`.
    NEUTRAL = "neutral"

    NEGATIVE = "negative"
    STRONGLY_NEGATIVE = "strongly_negative"

    @property
    def is_positive(self) -> bool:
        return self in (Stance.STRONGLY_POSITIVE, Stance.POSITIVE)

    @property
    def is_negative(self) -> bool:
        return self in (Stance.STRONGLY_NEGATIVE, Stance.NEGATIVE)

    @property
    def stated(self) -> str:
        """The stance in words, for a surface that shows it."""

        return self.value.replace("_", " ")


class UncertaintyKind(StrEnum):
    """Why a committee could not settle something.

    Four kinds, and the separations between them are the ones this
    platform has already paid to learn. They differ in what would close
    them, which is the only thing an investor can act on: one wants
    another cycle, one wants another reading, one wants a measurement
    that has never been taken, and one wants a capability that does not
    exist.
    """

    #: Looked for, and not there this cycle. A later fetch may close it.
    EVIDENCE_MISSING = "evidence_missing"

    #: Read more than once, and the readings disagreed. More of the same
    #: reading does not close it; only a narrower question does.
    EVIDENCE_CONFLICTING = "evidence_conflicting"

    #: An input this committee's remit asks for was never measured.
    #: Distinct from missing evidence: nothing failed, and nothing is
    #: pending — the measurement simply has not been taken.
    MEASUREMENT_ABSENT = "measurement_absent"

    #: The question does not apply, or no layer of this platform answers
    #: it yet. A cryptocurrency has no business quality and never will;
    #: a bank's capital adequacy is real and unreachable. Reporting
    #: either as *missing* would promise a measurement that is not
    #: coming.
    OUTSIDE_KNOWLEDGE = "outside_current_knowledge"

    @property
    def is_resolvable(self) -> bool:
        """Whether another cycle of the same work could close it.

        Stated on the kind rather than per instance so that the answer
        cannot vary between two uncertainties of the same kind, which
        is how a surface comes to promise one measurement and not
        another for no visible reason.
        """

        return self in (
            UncertaintyKind.EVIDENCE_MISSING,
            UncertaintyKind.MEASUREMENT_ABSENT,
        )


@dataclass(frozen=True, slots=True)
class Uncertainty:
    """One thing this committee could not settle, and why.

    `about` is carried verbatim from wherever the absence was worded.
    Nothing here composes a new sentence about a gap: the layer that
    found the gap already said what it was, and rewording it at every
    hop is how two surfaces come to describe the same absence
    differently.
    """

    kind: UncertaintyKind

    #: The absence, in the words of the layer that found it.
    about: str

    @property
    def is_resolvable(self) -> bool:
        return self.kind.is_resolvable


class ConfidenceLevel(StrEnum):
    """How far an opinion is worth leaning on, banded from counts."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Confidence:
    """How well evidenced this opinion is — counted, never asserted.

    Every field is a count of something that happened. There is no
    input float, no weighting and no scale factor, because a confidence
    that arrives from outside cannot be checked, and the platform's
    older committee confidences were exactly that: an average of three
    numbers each of which was itself a judgment.

    Confidence measures the *reading*, not the security. A low figure
    says this committee saw less than it asks for. It never says the
    business is worse — that is the stance's job, and conflating the
    two is how a bearish view came to be, by construction, a tentative
    one.

    The counts travel with the band, always. `Agreement` learned this
    first: "narrow" printed without `3/5` is an interpretation wearing
    the authority of a measurement.
    """

    #: Inputs this committee's remit asks for, and how many were measured.
    inputs_measured: int
    inputs_asked: int

    #: Findings in the remit, by the sense their signal recorded.
    supporting: int
    opposing: int

    #: Things the committee could not settle.
    unresolved: int

    @property
    def completeness(self) -> float | None:
        """The share of asked-for inputs that were measured, 0.0 to 1.0.

        None where the remit asks for nothing measurable. A committee
        with no measurable inputs is not a committee that measured
        none, and `0/0` reported as 0% would say the opposite.
        """

        if self.inputs_asked <= 0:
            return None

        return self.inputs_measured / self.inputs_asked

    @property
    def findings_read(self) -> int:
        return self.supporting + self.opposing

    @property
    def level(self) -> ConfidenceLevel | None:
        """The band, from completeness and whether anything was read.

        Deliberately coarse. Three bands is all that counts of this
        size can carry honestly, and a percentage would invite a reader
        to compare two opinions to the point.
        """

        completeness = self.completeness

        if completeness is None or not self.findings_read:
            return None

        if completeness >= 0.8 and not self.unresolved:
            return ConfidenceLevel.HIGH

        if completeness >= 0.5:
            return ConfidenceLevel.MODERATE

        return ConfidenceLevel.LOW

    def stated(self) -> str:
        """The confidence as a surface shows it, counts included."""

        level = self.level

        measured = f"{self.inputs_measured} of {self.inputs_asked} inputs measured"

        if level is None:
            return f"not established ({measured})"

        return f"{level.value} ({measured}, {self.findings_read} findings read)"


@dataclass(frozen=True, slots=True)
class CommitteeOpinion:
    """One committee's position on one security, with its grounds.

    Consumed whole by the Executive layer, which adjudicates between
    opinions. This object never adjudicates: it does not know that
    another committee exists, does not rank itself against one, and
    resolves no disagreement. That property is deliberate and is
    borrowed from the assessment contract, where it is constitutional —
    committees that negotiated before the Executive layer ran would
    move the adjudication one layer too early, and the losing position
    would vanish before anything could record it.
    """

    #: Stable identifier, and the name a surface prints.
    committee: str

    #: The readings this committee speaks for. Its remit, declared —
    #: so a reader can tell a committee that found nothing adverse from
    #: one that was never shown the adverse findings.
    remit: frozenset[Dimension]

    #: The position, or nothing at all where the committee did not speak.
    stance: Stance | None

    #: Why it did not speak. Present exactly when `stance` is None.
    abstained_because: str | None

    #: Addresses into the case's finding ledger. Never prose: the
    #: wording lives in the ledger and is resolved for display.
    #:
    #: Order is the order the signals reported. It is not a ranking —
    #: this platform does not measure how strong a finding is, and an
    #: order presented as strength would be a measurement nobody took.
    supporting: tuple[str, ...]
    opposing: tuple[str, ...]

    #: What this committee could not settle.
    uncertainty: tuple[Uncertainty, ...]

    #: How well evidenced the position is. None alongside an abstention:
    #: a committee that did not speak is not a committee that spoke
    #: with low confidence, and averaging the two together is the defect
    #: that made an unmeasurable portfolio risk look like an objection.
    confidence: Confidence | None

    #: The named rule that produced the stance. An opinion that cannot
    #: name its rule cannot exist — the same bar the decision tables
    #: hold themselves to, for the same reason: a conclusion whose rule
    #: is invisible cannot be challenged, only believed.
    decided_by: str

    #: One worded line, composed from the counts above.
    summary: str

    @property
    def has_opinion(self) -> bool:
        """Whether this committee spoke at all."""

        return self.stance is not None

    @property
    def is_contested(self) -> bool:
        """Whether findings were read on both sides of this committee's remit.

        The honest signal that a stance was reached over an argument
        rather than in its absence — and the thing an investor most
        wants flagged, because a positive stance with nothing against
        it means something different from a positive stance that
        outweighed two adverse findings.
        """

        return bool(self.supporting) and bool(self.opposing)
