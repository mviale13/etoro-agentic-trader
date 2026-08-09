"""Why each score the Artificial CIO decided on is the number it is.

## The scoring contract is stable (the owner's ruling, 2026-08-09)

`Contribution`, `ScoreDerivation` and `ScoreBasis` are the shape every
score on the dossier explains itself in, and they are **not to be
reshaped**. The ruling on the slice that introduced them: *it solved
the right problem at the right layer — keep this scoring contract
stable.*

Stable means what it means elsewhere on this platform. New scores
**consume** these objects; they do not extend them, parallel them, or
introduce a second decomposition shape beside them. The first grounded
consumer — business quality read from the filing — was built entirely
against this contract without altering a field of it, which is the
evidence that the shape is right.

What stability forecloses:

- a second breakdown object for a score whose arithmetic differs. A
  share-of-applicable score and a count-of-factors score are both
  `earned` over `available`, and both say so in `stated()`;
- a weight, a percentage or a penalty added to `Contribution`. Points
  are non-negative and integral because this platform measures no
  weights, and a `+18` would be a number nobody computed;
- a derivation manufactured for a score that bands a single reading. A
  one-row table dresses a threshold up as a tally, and `derivation`
  stays `None` there.

Changing any of it is an owner's decision, recorded here — never a
side effect of adding a score.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.finding import Sense


class ScoreKind(StrEnum):
    """
    What kind of number a score is, which is not the same for all of them.

    Printed side by side at two significant figures, a measurement and an
    interpretation look identical, and the interpretation borrows the
    measurement's authority. Naming the kind is what separates them.
    """

    #: Read directly from data: volatility, beta, a drawdown, a cash
    #: weight. None of the dossier's five headline scores is one of these
    #: — they are what the scores are built out of, and they appear as the
    #: evidence beneath each one.
    MEASUREMENT = "measurement"

    #: Computed from the investor's own policy and constraints. It changes
    #: when the policy changes, not when the market does.
    POLICY = "policy"

    #: A deterministic interpretation of evidence, against a band this
    #: platform chose. Reproducible, arguable, and not a measurement.
    ASSESSMENT = "assessment"

    @property
    def stated(self) -> str:
        """How the kind is named to the investor, in a few words."""

        return _KINDS[self]


_KINDS = {
    ScoreKind.MEASUREMENT: "Measured from data",
    ScoreKind.POLICY: "Derived from your policy",
    ScoreKind.ASSESSMENT: "Assessed against this platform's bands",
}


#: What each score is called, in the order the decision weighs them.
#:
#: Stated here because this is where the scores are described. Anything
#: that words a movement in one of them — "Valuation attractiveness
#: improved, 55 → 80" — reads the name from here rather than choosing its
#: own, so two surfaces cannot call the same score different things.
SCORE_LABELS: dict[str, str] = {
    "quality": "Business quality",
    "evidence": "Evidence strength",
    "valuation": "Valuation attractiveness",
    "safety": "Safety",
    "portfolio_fit": "Portfolio fit",
}


@dataclass(frozen=True, slots=True)
class Contribution:
    """One factor a score counted, and what it was worth.

    Carried from the signal that counted it, never recomposed. The
    statement is the finding's own words, so a contribution and the
    finding beneath it cannot come to say different things.
    """

    statement: str

    #: What this factor added. Never negative on this platform today,
    #: and that is a fact about the scoring rather than about the
    #: company: an adverse factor fails to earn its point rather than
    #: subtracting one. Stated plainly, because a reader who sees only
    #: positive numbers will otherwise assume nothing counted against.
    points: int

    #: How the signal read it. A zero-point factor is not one thing:
    #: `NEUTRAL` is a factor that does not apply, `ADVERSE` is one the
    #: company failed, and a column of bare zeroes cannot tell them
    #: apart.
    sense: Sense

    #: The rule table's own verdict word, where one produced this
    #: contribution — "excellent", "declining". First-class rather than
    #: folded into `statement`, because it is what distinguishes two
    #: companies that reached the same score by different routes, and a
    #: surface that recovered it by splitting a sentence would be doing
    #: domain reasoning where none belongs.
    #:
    #: None for a score whose factors carry no verdict, which is not the
    #: same as a verdict of nothing.
    verdict: str | None = None

    @property
    def earned(self) -> bool:
        return self.points > 0


@dataclass(frozen=True, slots=True)
class ScoreDerivation:
    """How a counted score reached its number, factor by factor.

    The answer to *why 80?*, in arithmetic an investor can check rather
    than a band name they must accept. It exists because the platform
    was already computing it and throwing it away: the quality signal
    counts a point per factor, collapses the count to a band, and the
    band to a constant — so a number that began as `2 of 3` reached the
    dashboard as `62` with nothing between.

    Only for scores that genuinely count factors. A score that places
    one reading in a band — a forward P/E against a threshold — has no
    decomposition, and manufacturing a one-row table for it would dress
    a threshold up as a tally. Those scores carry no derivation, and
    their basis says what they are instead.
    """

    contributions: tuple[Contribution, ...]

    #: Points earned, and points that were available to earn. These are
    #: not the same as the band's requirement, and the difference is the
    #: honest part: a company whose dividend yield could not be read has
    #: two factors available, and a band that asks for three is then out
    #: of reach for a reason that is nothing to do with the business.
    earned: int
    available: int

    #: The band the count fell in, and the number this platform assigns
    #: it. Both stated, because the second is a house rule and a reader
    #: who cannot see it cannot tell it from a measurement.
    band: str
    score: int

    #: Every band and its number, so the reader sees the whole ruler.
    scale: tuple[tuple[str, int], ...]

    #: What the band required. Where `earned` reached `available` and
    #: still fell short, this is what says so.
    required: int | None = None

    #: How much of what this score asks for could be read: the factors
    #: established, over the factors it would consult given everything.
    #:
    #: A different question from `earned` over `available`, and both
    #: belong on the page. *One favourable of three answered* is a
    #: reading of the business; *three of three read* is a reading of
    #: this platform. A score of 62 on a full set and a 62 on a third of
    #: one are not the same claim, and only these two say so.
    #:
    #: None where a score does not know its own candidate set.
    established_factors: int | None = None
    candidate_factors: int | None = None

    @property
    def is_capped_by_unreadable_factors(self) -> bool:
        """Whether a higher band was unreachable for want of data.

        The case worth flagging to an investor: every factor that could
        be read was earned, and the score still is not the top one —
        because the platform could not read enough of the company, not
        because the company fell short.
        """

        return (
            self.required is not None
            and self.earned == self.available
            and self.available < self.required
        )

    @property
    def coverage(self) -> str | None:
        """How much of the score's own question set was readable."""

        if self.established_factors is None or self.candidate_factors is None:
            return None

        return f"{self.established_factors} of {self.candidate_factors} read"

    def stated(self) -> str:
        """The arithmetic as one checkable line."""

        counted = f"{self.earned} of {self.available} points earned"

        if self.is_capped_by_unreadable_factors:
            return (
                f"{counted} — every factor that could be read scored, and "
                f"{self.band} is as far as {self.available} factors reach; "
                f"the next band needs {self.required}."
            )

        return f"{counted} → {self.band} → {self.score}."


@dataclass(frozen=True, slots=True)
class ScoreBasis:
    """
    The reading under one score, and the rule that turned it into a number.

    A figure on an investment dashboard reads as a measurement. Several of
    these are not: they are a band this platform chose, applied to a
    reading it took. "80 / 100" says nothing about where 80 came from, and
    a reader who cannot see the band cannot tell a measurement from a
    house rule.

    So the band is stated beside the score rather than buried inside it —
    the same reason the risk signal states its own thresholds. A reader can
    then disagree with where the line is drawn without doubting the number,
    which is the only kind of disagreement this platform can survive.

    Where nothing was measured, `basis` says why. It never says zero.
    """

    #: The one sentence that turns the reading into the number: the band
    #: applied, the terms averaged, or the reason there is no score.
    basis: str

    #: What the reading itself rests on. Empty where the score rests on no
    #: individual finding, which is not the same as resting on nothing.
    evidence: tuple[str, ...] = ()

    #: What kind of number this is. Assessed by default: most of these are
    #: an interpretation, and the ones that are not say so explicitly.
    kind: ScoreKind = ScoreKind.ASSESSMENT

    #: The arithmetic beneath the score, where the score counted factors.
    #: None for a score that bands a single reading or averages other
    #: scores — those have no decomposition, and inventing one would be
    #: the figure this whole object exists to prevent.
    derivation: ScoreDerivation | None = None


@dataclass(frozen=True, slots=True)
class ScoreBases:
    """
    Every score the decision was made on, each with its basis.

    One object rather than five loose fields, because a score that arrived
    without its basis would be exactly the figure this exists to stop.
    """

    quality: ScoreBasis
    evidence: ScoreBasis
    valuation: ScoreBasis

    #: Safety, not risk: every score this platform shows runs the same way,
    #: and a higher number here is a safer security.
    safety: ScoreBasis

    portfolio_fit: ScoreBasis

    @classmethod
    def unrecorded(cls) -> ScoreBases:
        """
        Five scores whose reasoning nobody stated.

        For evidence built by a path that does not word its scores. The
        scores themselves are real and are still shown; what is absent is
        the account of them, and that absence is said rather than papered
        over with a plausible sentence.
        """

        unstated = ScoreBasis(basis="How this score was reached was not recorded.")

        return cls(
            quality=unstated,
            evidence=unstated,
            valuation=unstated,
            safety=unstated,
            portfolio_fit=unstated,
        )
