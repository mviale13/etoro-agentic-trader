from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.quality_signal import QualitySignal
from app.domain.score_basis import Contribution


class QualitySignalService:
    """How good the business is, counted one factor at a time.

    Three factors, each worth a point or no point. The count bands to
    HIGH, MEDIUM or LOW, and the band becomes a number further down.

    The count used to be a local integer, discarded the moment it was
    banded — so a score that began as *2 of 3* reached the dashboard as
    *62* with nothing in between, and an investor asking why could only
    be told the band. The factors are now carried out with the signal,
    which is the same repair `Sense` and `Dimension` needed: the layer
    that knows was throwing it away.

    Nothing here scores negatively. A factor the company fails earns no
    point rather than subtracting one, so the column an investor reads
    has no minus signs in it — a fact about this scoring rather than
    about the company, and stated on `Contribution` so it cannot be
    mistaken for the second.
    """

    LARGE_CAP_THRESHOLD = 10_000_000_000

    #: How many factors this score consults given everything. Declared
    #: so a surface can say how much of the question set was readable —
    #: two of three read is a statement about this platform, and it must
    #: not be mistaken for a statement about the company.
    FACTORS = 3

    #: Points needed for each band, hardest first. Kept as data because
    #: the derivation shows the reader the whole ruler, and a ruler
    #: written twice is a ruler that comes to disagree with itself.
    BANDS: tuple[tuple[str, int], ...] = (
        ("HIGH", 3),
        ("MEDIUM", 2),
        ("LOW", 0),
    )

    CONFIDENCE = {"HIGH": 90, "MEDIUM": 75, "LOW": 65}

    def build(
        self,
        company: CompanyFacts,
        asset_class: AssetClass | None = None,
    ) -> QualitySignal:
        # The factors below are company questions — size, earnings,
        # dividend — and an asset positively known to have no business
        # behind it is not asked them at all. Asked anyway, a fund whose
        # only readable field was a structural dividend of zero scored
        # LOW: an accumulating share class cannot distribute by design,
        # and the zero was read as a payout fact. The same boundary the
        # value signal already holds, applied to the question set rather
        # than to a sentence.
        if asset_class is not None and asset_class.has_no_company:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                evidence=(
                    Finding.neutral(
                        f"A {asset_class.noun} has no business quality to assess."
                    ),
                ),
                basis=(
                    f"Quality is not scored: a {asset_class.noun} is not a "
                    "business, and the company-quality factors — size, "
                    "earnings, dividend — are questions this platform does "
                    "not ask about it."
                ),
            )

        # Each finding carries the sense this service scored it with, so
        # nothing downstream has to guess. Size and dividend are scored as
        # a point or no point, never as a penalty — a small company is not
        # thereby a bad one — so the absence of the point is neutral.
        counted: list[tuple[Finding, int]] = []

        if company.market_cap is not None:
            if company.market_cap >= self.LARGE_CAP_THRESHOLD:
                counted.append((Finding.favourable("Large-cap company."), 1))
            else:
                counted.append((Finding.neutral("Small or mid-cap company."), 0))

        if company.eps is not None:
            if company.eps > 0:
                counted.append((Finding.favourable("Positive earnings."), 1))
            else:
                counted.append((Finding.adverse("Negative earnings."), 0))

        if company.dividend_yield is not None:
            if company.dividend_yield > 0:
                counted.append((Finding.favourable("Dividend-paying business."), 1))
            else:
                counted.append((Finding.neutral("No dividend."), 0))

        if not counted:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                evidence=(Finding.neutral("Insufficient quality data."),),
            )

        earned = sum(points for _, points in counted)

        quality = self._band(earned)

        return QualitySignal(
            quality=quality,
            confidence=self.CONFIDENCE[quality],
            evidence=tuple(finding for finding, _ in counted),
            contributions=tuple(
                Contribution(
                    statement=finding.statement,
                    points=points,
                    sense=finding.sense,
                )
                for finding, points in counted
            ),
            earned=earned,
            # Only the factors this company's data allowed us to look at.
            # A company whose dividend yield could not be read has two
            # available, and cannot reach a band asking for three — for
            # a reason that is nothing to do with the business.
            available=len(counted),
            next_band_needs=self._next_band_needs(quality),
        )

    @classmethod
    def _band(cls, earned: int) -> str:
        for band, needed in cls.BANDS:
            if earned >= needed:
                return band

        return "LOW"

    @classmethod
    def _next_band_needs(cls, quality: str) -> int | None:
        """Points for the band above this one, or nothing at the top."""

        bands = [band for band, _ in cls.BANDS]

        position = bands.index(quality)

        if position == 0:
            return None

        return cls.BANDS[position - 1][1]
