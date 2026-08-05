"""Why each score the Artificial CIO decided on is the number it is."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
