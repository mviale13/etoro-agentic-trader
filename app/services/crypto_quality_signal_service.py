"""How sound a token is, on what a token actually has."""

from datetime import UTC, datetime

from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.quality_signal import QualitySignal


class CryptoQualitySignalService:
    """
    Assess a cryptocurrency without asking it company questions.

    `QualitySignalService` scores size, earnings and dividends. A token has
    none of those, so it returned UNKNOWN for every crypto asset and the
    case stopped at research — for a preferred asset class, permanently.

    What a token does have, the same provider call already returns. Four
    things, each measured and each meaning something an investor can check:

    Scale — the market value the provider reports for the token. Worded
    with the provider's name on it, because that is what it is: one
    field read from one source, not a network figure this platform
    measured — and the source has already reported $8,105 for a token
    worth billions. A large value is not thereby a good network, but a
    small one is easier to move and easier to abandon.

    Liquidity — a day's reported trading against that market value. This
    is the question of whether a position can be left, which for an
    asset with no earnings is most of what "quality" can honestly mean.

    Issuance — how much of the eventual supply exists already. A token 20%
    issued has five times its float still to come; the holder is diluted by
    a schedule, not by a decision. A token with no stated cap cannot be
    scored on this, and is not.

    Age — how long it has traded. Survival is weak evidence, and it is
    evidence.

    The bands are policy, stated here rather than buried in a score, so a
    reader can disagree with a threshold without doubting the measurement.
    """

    #: Provider-reported market value, in dollars.
    LARGE_NETWORK = 10_000_000_000
    SMALL_NETWORK = 1_000_000_000

    #: A day's volume as a share of that market value.
    LIQUID = 0.02
    ILLIQUID = 0.002

    #: Share of the eventual supply already issued.
    MOSTLY_ISSUED = 0.90
    PARTLY_ISSUED = 0.60

    #: Years of trading history.
    ESTABLISHED_YEARS = 5.0
    YOUNG_YEARS = 2.0

    #: How many of the four a band needs, exactly as `MINIMUM_ANSWERED`
    #: requires of a business. One reading is as easily a gap as a
    #: verdict, and a token judged on its age alone was being banded
    #: MEDIUM on the single fact that it had not disappeared yet.
    MINIMUM_MEASURED = 2

    def build(
        self,
        company: CompanyFacts,
    ) -> QualitySignal:
        evidence: list[Finding] = []
        score = 0
        measured = 0

        for point, finding in (
            self._scale(company),
            self._liquidity(company),
            self._issuance(company),
            self._age(company),
        ):
            if finding is None:
                continue

            measured += 1
            score += point
            evidence.append(finding)

        if measured < self.MINIMUM_MEASURED:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                evidence=tuple(evidence)
                or (
                    Finding.neutral(
                        "This platform has read nothing about this token's "
                        "network, so its quality is not assessed."
                    ),
                ),
            )

        # Judged against what could be measured, so a token missing one
        # reading is not marked down for the reading's absence.
        ratio = score / measured

        if ratio >= 0.75:
            quality, confidence = "HIGH", 60 + measured * 7
        elif ratio >= 0.25:
            quality, confidence = "MEDIUM", 50 + measured * 6
        else:
            quality, confidence = "LOW", 45 + measured * 5

        return QualitySignal(
            quality=quality,
            confidence=min(confidence, 90),
            evidence=tuple(evidence),
        )

    @classmethod
    def _scale(
        cls,
        company: CompanyFacts,
    ) -> tuple[int, Finding | None]:
        value = company.market_cap

        # A provider reporting zero is a provider reporting nothing. A
        # network cannot be worth nothing while trading, so this is the
        # absence it looks like — and it was being scored as an adverse
        # measurement, printed as "$0.00bn", which is a figure nobody
        # measured on an investment page.
        if not value:
            return 0, None

        # The provider's name travels with the figure. This used to read
        # "Network value is only $8,105." — one provider field, worded as
        # a network measurement, standing as a thesis condition. The
        # reading is kept (it is the only scale figure held), but it is
        # never dressed as more than what it is: what the source reports.
        source = cls._source(company)

        if value >= cls.LARGE_NETWORK:
            return 1, Finding.favourable(
                f"{source} reports a market value of {cls._money(value)}."
            )

        if value >= cls.SMALL_NETWORK:
            return 0, Finding.neutral(
                f"{source} reports a market value of {cls._money(value)}."
            )

        return -1, Finding.adverse(
            f"{source} reports a market value of only {cls._money(value)}."
        )

    @staticmethod
    def _source(company: CompanyFacts) -> str:
        """Who reported the figures being read, by name where known."""

        reading = company.fundamentals_reading

        if reading is None or not reading.source:
            return "The data provider"

        return reading.source

    @staticmethod
    def _money(value: float) -> str:
        """
        An amount at a unit that shows it.

        Billions are the right unit for a network and the wrong one for
        what the provider returns when it has lost track of a token:
        Hyperliquid came back as 8,105 dollars and printed as "$0.00bn",
        which reads as a rounding rather than as the nonsense it is. A
        figure is shown at the unit where it is still visible, so an
        investor can see that the provider is wrong instead of reading a
        zero the platform appeared to have measured.
        """

        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:,.1f}bn"

        if value >= 1_000_000:
            return f"${value / 1_000_000:,.0f}m"

        return f"${value:,.0f}"

    @classmethod
    def _liquidity(
        cls,
        company: CompanyFacts,
    ) -> tuple[int, Finding | None]:
        volume = company.volume_24h
        value = company.market_cap

        # Zero on either side is the provider's absence, not a still
        # market: a token nobody traded all day and a token the provider
        # has no figure for are the same zero, and only one of them is a
        # measurement this platform may report.
        if not volume or not value:
            return 0, None

        turnover = volume / value

        # "Of the network" claimed a denominator this platform never
        # measured. Both sides of this ratio are the provider's figures,
        # and the sentence says which value the day is measured against.
        if turnover >= cls.LIQUID:
            return 1, Finding.favourable(
                f"A day's reported trading turns over {turnover * 100:.1f}% "
                "of its market value."
            )

        if turnover >= cls.ILLIQUID:
            return 0, Finding.neutral(
                f"A day's reported trading turns over {turnover * 100:.1f}% "
                "of its market value."
            )

        return -1, Finding.adverse(
            f"A day's reported trading turns over only {turnover * 100:.2f}% "
            "of its market value, so a position may be hard to leave."
        )

    @classmethod
    def _issuance(
        cls,
        company: CompanyFacts,
    ) -> tuple[int, Finding | None]:
        circulating = company.circulating_supply
        cap = company.max_supply

        if not circulating or not cap:
            # No stated cap means no schedule to be diluted by, and no
            # measurement either. It is left out rather than assumed benign.
            return 0, None

        issued = circulating / cap

        if issued >= cls.MOSTLY_ISSUED:
            return 1, Finding.favourable(
                f"{issued * 100:.1f}% of the eventual supply already exists."
            )

        if issued >= cls.PARTLY_ISSUED:
            return 0, Finding.neutral(
                f"{issued * 100:.1f}% of the eventual supply already exists."
            )

        return -1, Finding.adverse(
            f"Only {issued * 100:.1f}% of the eventual supply exists, so "
            "holders are diluted as the rest is issued."
        )

    @classmethod
    def _age(
        cls,
        company: CompanyFacts,
    ) -> tuple[int, Finding | None]:
        inception = company.inception

        if inception is None:
            return 0, None

        years = (datetime.now(UTC) - inception).days / 365.25

        if years >= cls.ESTABLISHED_YEARS:
            return 1, Finding.favourable(f"Traded for {years:.0f} years.")

        if years >= cls.YOUNG_YEARS:
            return 0, Finding.neutral(f"Traded for {years:.1f} years.")

        return -1, Finding.adverse(
            f"Traded for only {years:.1f} years, so little of its record "
            "has been observed."
        )
