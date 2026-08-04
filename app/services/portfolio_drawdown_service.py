"""How far this account fell, against how far the investor said it could."""

from __future__ import annotations

from app.domain.drawdown import deepest_drawdown
from app.domain.equity_curve import EquityCurve
from app.domain.portfolio_drawdown import PortfolioDrawdown


class PortfolioDrawdownService:
    """
    Measure the account's worst fall, and score it against the mandate.

    The measurement and the score are deliberately separate. The depth is
    a fact about the account; whether that depth is alarming is a judgement
    about this investor, and the two are stated in different places so a
    reader can accept the first and argue with the second.
    """

    #: Daily observations needed before a fall means anything.
    #:
    #: The same floor a security's own drawdown is held to. A week of
    #: balances can only report the worst fall inside that week, which is
    #: not what "the account's drawdown" is read as meaning.
    MINIMUM_OBSERVATIONS = 30

    #: The fall this platform treats as the most an account should absorb
    #: when the investor has not said. Policy, not a measurement — and the
    #: investor's own figure is used instead wherever they stated one.
    DEFAULT_TOLERANCE_PCT = 20.0

    def measure(
        self,
        curve: EquityCurve | None,
    ) -> PortfolioDrawdown | None:
        """
        The deepest fall in the curve, or nothing.

        Nothing is returned for a curve too short to measure. A drawdown
        is what the account did over a stretch of time, and reporting the
        deepest fall in eleven days as though it were that would put a
        number on a dashboard that nobody could act on.
        """

        if curve is None or curve.observations < self.MINIMUM_OBSERVATIONS:
            return None

        measurement = deepest_drawdown(curve.values)

        if measurement is None:
            return None

        peak = curve.points[measurement.peak_index]
        trough = curve.points[measurement.trough_index]

        return PortfolioDrawdown(
            depth=measurement.depth,
            peak_on=peak.observed_on,
            peak_value_usd=peak.total_value_usd,
            trough_on=trough.observed_on,
            trough_value_usd=trough.total_value_usd,
            current_depth=measurement.current_depth,
            starts_on=curve.points[0].observed_on,
            ends_on=curve.points[-1].observed_on,
            observations=curve.observations,
            reading=curve.reading,
        )

    @classmethod
    def risk_score(
        cls,
        drawdown: PortfolioDrawdown,
        tolerance_pct: float | None = None,
    ) -> float:
        """
        How much of the investor's stated tolerance this fall consumed.

        1.0 means the account has already fallen as far as the investor
        said they were willing to see it fall. Scoring against a mandate
        rather than against a fixed band is what makes the number mean
        something: 15% is a mild year for one investor and a broken
        promise to another.
        """

        tolerance = tolerance_pct

        if tolerance is None or tolerance <= 0:
            tolerance = cls.DEFAULT_TOLERANCE_PCT

        return min(drawdown.depth / (tolerance / 100.0), 1.0)
