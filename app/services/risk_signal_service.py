from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.risk_signal import RiskSignal


class RiskSignalService:
    """
    Read a security's own risk out of its price history.

    Volatility and drawdown are measurements. The bands below are policy —
    where this platform draws the line between calm and violent — and they
    are stated here rather than buried in a score, so a reader can disagree
    with the threshold without doubting the number.
    """

    #: Annualised volatility, as a ratio.
    CALM = 0.20
    ACTIVE = 0.35
    VIOLENT = 0.60

    #: Observed peak-to-trough fall, as a ratio.
    SHALLOW_DRAWDOWN = 0.20
    DEEP_DRAWDOWN = 0.40

    def build(
        self,
        company: CompanyFacts,
    ) -> RiskSignal:
        volatility = company.realized_volatility
        drawdown = company.max_drawdown

        if volatility is None and drawdown is None:
            return RiskSignal(
                level="UNKNOWN",
                volatility=None,
                max_drawdown=None,
                confidence=20,
                evidence=(
                    Finding.neutral(
                        f"No usable price history for {company.symbol}, so its "
                        "risk is not measured."
                    ),
                ),
            )

        # A measurement's sense is the band it lands in. 12% volatility and
        # 94% volatility are both readings, but only one of them is an
        # argument against holding the security.
        evidence: list[Finding] = []

        if volatility is not None:
            evidence.append(
                self._finding(
                    f"Annualised volatility is {volatility * 100:.1f}% "
                    "over the past year.",
                    self._volatility_level(volatility),
                )
            )

        if drawdown is not None:
            evidence.append(
                self._finding(
                    f"Deepest fall over the past year was {drawdown * 100:.1f}%.",
                    self._drawdown_level(drawdown),
                )
            )

        return RiskSignal(
            level=self._level(volatility, drawdown),
            volatility=volatility,
            max_drawdown=drawdown,
            confidence=90 if volatility is not None and drawdown is not None else 60,
            evidence=tuple(evidence),
        )

    @staticmethod
    def _finding(
        statement: str,
        level: str | None,
    ) -> Finding:
        """A calm reading argues for the security; a violent one against."""

        if level == "LOW":
            return Finding.favourable(statement)

        if level in ("HIGH", "SEVERE"):
            return Finding.adverse(statement)

        return Finding.neutral(statement)

    def _level(
        self,
        volatility: float | None,
        drawdown: float | None,
    ) -> str:
        """The higher of the two readings decides the band."""

        levels = [
            level
            for level in (
                self._volatility_level(volatility),
                self._drawdown_level(drawdown),
            )
            if level is not None
        ]

        order = ("LOW", "MODERATE", "HIGH", "SEVERE")

        return max(levels, key=order.index) if levels else "UNKNOWN"

    def _volatility_level(
        self,
        volatility: float | None,
    ) -> str | None:
        if volatility is None:
            return None

        if volatility < self.CALM:
            return "LOW"

        if volatility < self.ACTIVE:
            return "MODERATE"

        if volatility < self.VIOLENT:
            return "HIGH"

        return "SEVERE"

    def _drawdown_level(
        self,
        drawdown: float | None,
    ) -> str | None:
        if drawdown is None:
            return None

        if drawdown < self.SHALLOW_DRAWDOWN:
            return "LOW"

        if drawdown < self.DEEP_DRAWDOWN:
            return "MODERATE"

        return "HIGH"
