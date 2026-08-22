from dataclasses import dataclass

from app.domain.decision_rules import DecisionRule
from app.domain.finding import Finding
from app.domain.market_sensitivity import MarketSensitivity


@dataclass(frozen=True, slots=True)
class RiskSignal:
    """
    How violently one security has actually moved, and with what.

    This describes the security, not the account holding it, and it
    describes the past rather than predicting the future: volatility,
    drawdown and market sensitivity are measurements of an observed window.

    `level` is UNKNOWN when the price history was too short to measure. It
    bands the security's own volatility and drawdown only. Market sensitivity
    is carried and reported beside them but does not move the band: how hard a
    security swings and how much it swings *with the market* are different
    risks, and folding one into the other would hide which is which. What a
    high beta means for a decision is a judgement the Artificial CIO makes
    against the market it faces, not a level fixed here.
    """

    level: str

    #: Annualised standard deviation of daily returns, as a ratio.
    volatility: float | None

    #: Deepest peak-to-trough fall in the window, as a positive ratio.
    max_drawdown: float | None

    confidence: int
    evidence: tuple[Finding, ...]

    #: How much this security moves with its benchmark. None where it was
    #: not measured. Reported, never folded into `level`.
    market_sensitivity: MarketSensitivity | None = None

    #: The named, versioned rule that assigned this reading its meaning
    #: — identity, never endorsement. None where nothing was banded: an
    #: UNKNOWN produced by absence had no meaning assigned at all.
    rule: DecisionRule | None = None

    #: How violent each band is, as a ratio. Stated once, here, because two
    #: layers were about to hold their own copy of the same judgement.
    #:
    #: SEVERE's 0.85 sat above the former decision gate's threshold of 70,
    #: and until the owner's ruling of 2026-08-21 that placement rejected
    #: the thesis outright. The constants are unchanged; where they act
    #: is not: the severity reaches conviction as safety, and the band
    #: selects the Capital Action Envelope's tightest security-risk
    #: ceiling — a bound on the position's size, never on whether the
    #: case may be considered.
    SEVERITIES = {
        "LOW": 0.20,
        "MODERATE": 0.45,
        "HIGH": 0.65,
        "SEVERE": 0.85,
    }

    @property
    def severity(self) -> float | None:
        """This security's own risk, or nothing where it was not measured."""

        return self.SEVERITIES.get(self.level)
