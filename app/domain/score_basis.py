"""Why each score the Artificial CIO decided on is the number it is."""

from __future__ import annotations

from dataclasses import dataclass


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
    risk: ScoreBasis
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
            risk=unstated,
            portfolio_fit=unstated,
        )
