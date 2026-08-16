from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.decision_participation import SignalParticipation
from app.domain.decision_rules import PROVIDER_QUALITY, QUALITY_AUTHORITY
from app.domain.finding import Finding
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.monetary import MonetaryAmount
from app.domain.provider_translation import TranslationWarrant
from app.domain.provider_translations import governed
from app.domain.quality_coverage import (
    FactorStanding,
    QualityCoverage,
    QualityFactor,
)
from app.domain.quality_signal import QualitySignal
from app.domain.score_basis import Contribution

#: The warrant the registry holds for the market-cap crossing, read
#: rather than hardcoded so the day it is earned this consumer sees it.
_MARKET_CAP_TRANSLATION = governed("ValuationSnapshot.market_cap")

_MARKET_CAP_WARRANT = (
    _MARKET_CAP_TRANSLATION.warrant
    if _MARKET_CAP_TRANSLATION is not None
    else TranslationWarrant.UNKNOWN
)

#: The warrants under which a market capitalisation may be compared
#: with an absolute size threshold — `market-cap-input-eligibility@1`.
#:
#: **Explicit membership, and a different membership from Momentum's.**
#: The contrast is the whole argument. Momentum admits ASSUMED because
#: its output is a ratio over two closes of one series, invariant under
#: any linear rescaling of that series. **That proof does not exist
#: here and cannot be constructed**: this consumer compares the figure
#: with an absolute amount, and rescaling is precisely what moves a
#: value across an absolute line.
#:
#: Measured over the 72 live magnitudes rather than argued: **57 of
#: them sit within a factor of 100 of the $10bn threshold**, so a
#: hundredfold denomination error — the pence-versus-pounds error this
#: platform already stores on BP.L — would change which side of the
#: line they fall on. **17 are listings whose magnitude is in a
#: currency this platform never reads at all.** The condition the brief
#: sets — that the unresolved uncertainty cannot change the side of the
#: threshold — is therefore *measured false* for ASSUMED, and ASSUMED
#: is refused.
#:
#: Only VERIFIED and VALIDATED remain: the two warrants that carry a
#: check on the value itself, which is what an absolute comparison
#: needs and what `establishes_domain_fact` already means. DECLARED is
#: refused deliberately — a provider's statement of what a field means
#: establishes its *semantics*, and this consumer additionally needs
#: the *denomination*, which no Yahoo declaration supplies and this
#: platform does not read.
ELIGIBLE_MARKET_CAP_WARRANTS: frozenset[TranslationWarrant] = frozenset(
    {
        TranslationWarrant.VERIFIED,
        TranslationWarrant.VALIDATED,
    }
)


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

    #: The same amount, with the denomination the bare constant always
    #: silently meant. `monetary-comparison@1`'s policy ruling: the
    #: large-cap line is **ten billion US dollars**, and it says so in
    #: a type that cannot be constructed without a currency. Built from
    #: the constant above so the two amounts cannot drift, and the
    #: constant itself stays exactly what `provider-quality@1`'s
    #: fingerprint has always hashed.
    LARGE_CAP = MonetaryAmount(amount=float(LARGE_CAP_THRESHOLD), currency="USD")

    #: Named on the class so the provenance guard can fingerprint the
    #: eligibility rule apart from the bands it gates.
    ELIGIBLE_MARKET_CAP_WARRANTS = ELIGIBLE_MARKET_CAP_WARRANTS

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
                # The question does not apply, which is not the same as
                # an unanswered one: it leaves the expected set instead
                # of lowering coverage.
                applicable=False,
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

        readings = self._factor_readings(company)

        for _, reading in readings:
            if reading is not None:
                counted.append(reading)

        coverage = QualityCoverage(
            standings=tuple(
                FactorStanding(
                    factor=factor,
                    participation=(
                        SignalParticipation.PARTICIPATING
                        if reading is not None
                        else SignalParticipation.EXPECTED_ABSENT
                    ),
                    points=reading[1] if reading is not None else None,
                )
                for factor, reading in readings
            )
        )

        # `quality-authority@1`. The ruler below is unchanged and its
        # thresholds are untouched — what changed is that it only runs
        # once every applicable factor has been read. Short of that
        # Quality abstains rather than banding a business on part of
        # the question set, which #140 measured turning a company that
        # passed everything readable into an adverse vote.
        if not coverage.may_band:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                rule=QUALITY_AUTHORITY,
                evidence=(
                    tuple(finding for finding, _ in counted)
                    or (Finding.neutral("Insufficient quality data."),)
                ),
                # The measured half survives even where no band is
                # authorised: what was read, and how it did.
                contributions=tuple(
                    Contribution(
                        statement=finding.statement,
                        points=points,
                        sense=finding.sense,
                    )
                    for finding, points in counted
                ),
                earned=coverage.earned,
                available=coverage.available,
                basis=coverage.because,
            )

        earned = coverage.earned

        quality = self._band(earned)

        return QualitySignal(
            quality=quality,
            confidence=self.CONFIDENCE[quality],
            rule=PROVIDER_QUALITY,
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

    def _factor_readings(
        self,
        company: CompanyFacts,
    ) -> tuple[tuple[QualityFactor, tuple[Finding, int] | None], ...]:
        """Each quality factor, and its reading where there is one.

        Named per factor rather than accumulated into a count, because
        #140 found the platform could say how many factors it was
        missing and never which — so it could not explain a withheld
        band.
        """

        return (
            (QualityFactor.MARKET_SIGNIFICANCE, self._size(company)),
            (QualityFactor.EARNINGS, self._earnings(company)),
            (QualityFactor.DIVIDEND, self._dividend(company)),
        )

    @staticmethod
    def _earnings(company: CompanyFacts) -> tuple[Finding, int] | None:
        if company.eps is None:
            return None

        if company.eps > 0:
            return (Finding.favourable("Positive earnings."), 1)

        return (Finding.adverse("Negative earnings."), 0)

    @staticmethod
    def _dividend(company: CompanyFacts) -> tuple[Finding, int] | None:
        if company.dividend_yield is None:
            return None

        if company.dividend_yield > 0:
            return (Finding.favourable("Dividend-paying business."), 1)

        return (Finding.neutral("No dividend."), 0)

    def _size(self, company: CompanyFacts) -> tuple[Finding, int] | None:
        """The market-significance factor, or nothing where it cannot be asked.

        `None` is the third state: not below the threshold, not above
        it, and not a zero-point failure — the comparison was refused.
        The caller drops the factor from the count exactly as it drops
        an absent one, so `available` falls to two and the signal says
        how much of the question set it could read.
        """

        magnitude = company.market_cap_magnitude

        if magnitude is None:
            # No standing supplied. The legacy float is read as a
            # measurement under the registry's own warrant for the
            # crossing — which is what a caller writing `market_cap=`
            # directly is asserting — and is then held to the same
            # eligibility as every other magnitude.
            if company.market_cap is None:
                return None

            magnitude = MarketCapMagnitude.measured(
                company.market_cap,
                warrant=_MARKET_CAP_WARRANT,
            )

        # The amount in the threshold's own currency — the magnitude
        # itself where the denominations already agree, the authorised
        # translated amount where an evidenced FX translation carries
        # it across (fx-translation@1), and nothing everywhere else.
        # Reading `magnitude.amount` here would compare Swiss francs
        # against a dollar line, which is the exact comparison this
        # boundary exists to refuse.
        amount = magnitude.comparable_amount(
            self.LARGE_CAP, self.ELIGIBLE_MARKET_CAP_WARRANTS
        )

        if amount is None:
            return None

        if amount >= self.LARGE_CAP_THRESHOLD:
            return (Finding.favourable("Large-cap company."), 1)

        return (Finding.neutral("Small or mid-cap company."), 0)

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
