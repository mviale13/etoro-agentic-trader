from dataclasses import dataclass

from app.domain.finding import Finding


@dataclass(frozen=True, slots=True)
class RiskSignal:
    """
    How violently one security has actually moved.

    This describes the security, not the account holding it, and it
    describes the past rather than predicting the future: volatility and
    drawdown are measurements of an observed window.

    `level` is UNKNOWN when the price history was too short to measure.
    """

    level: str

    #: Annualised standard deviation of daily returns, as a ratio.
    volatility: float | None

    #: Deepest peak-to-trough fall in the window, as a positive ratio.
    max_drawdown: float | None

    confidence: int
    evidence: tuple[Finding, ...]

    #: How violent each band is, as a ratio. Stated once, here, because two
    #: layers were about to hold their own copy of the same judgement.
    #:
    #: SEVERE sits above `DecisionPolicy.maximum_acceptable_risk`, so a
    #: security that swings that hard is rejected on its own record rather
    #: than on a judgement about the account holding it.
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
