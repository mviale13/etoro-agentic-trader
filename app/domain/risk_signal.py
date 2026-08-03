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
