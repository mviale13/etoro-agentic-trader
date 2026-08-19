from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from app.domain.monetary import (
    INDEPENDENT_SHARE_COUNT_FIELDS,
    corroborate_denomination,
)
from app.domain.provenance import Provenance
from app.domain.provider_identity import ProviderIdentityClaim, vendor_claim
from app.domain.valuation_snapshot import ValuationSnapshot


@dataclass(frozen=True, slots=True)
class ObservedValuation:
    """One payload's snapshot, with the raw tenancy fields beside it.

    The tenancy fields are observations, never inputs: #215 measured
    `firstTradeDate` marking SPCX's tenancy boundary and failing to
    mark PARA's, so nothing reads meaning out of them here or anywhere
    downstream — they travel to the identity observation stream raw.
    """

    snapshot: ValuationSnapshot
    first_trade_date_ms: int | None = None
    ipo_expected_date: str | None = None


class ValueProvider:
    SOURCE = "Yahoo Finance"

    """
    Read the fundamentals a single provider call already returns.

    One request carries valuation, size, earnings — and the growth, margins,
    balance sheet and cash flow beside them. Reading only part of it and
    reporting the rest as unavailable would understate what the platform can
    evidence about a company, and leave the fundamental analysts nothing to
    analyse though the numbers were already in the response.
    """

    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot:
        """
        The fundamentals this provider reports, or a raised failure.

        `Ticker.info` does not raise when the provider refuses — it
        answers with a payload carrying nothing, which read literally
        becomes a completed reading in which every figure is absent. The
        caller then caches a refusal as knowledge for the rest of the
        day. So a payload that carries nothing is raised here as what it
        is, exactly as the quote path raises on an empty frame, and the
        caller's existing failure handling serves the last real reading
        marked as last known.
        """

        return self.observed(symbol).snapshot

    def observed(
        self,
        symbol: str,
    ) -> ObservedValuation:
        """One fetch, and everything this platform keeps from it.

        The snapshot as `snapshot` has always built it, plus the raw
        tenancy fields the same payload carries — read here because the
        payload is consumed here, and carried *beside* the snapshot
        rather than inside it: the fundamentals cache's shape is frozen
        (#215 ruling), and these fields belong to the identity
        observation stream, not to the valuation.
        """

        info = yf.Ticker(symbol).info

        snapshot = self.from_info(
            info,
            reading=Provenance(source=self.SOURCE, observed_at=datetime.now(UTC)),
        )

        if snapshot.carries_nothing:
            raise RuntimeError(
                f"{self.SOURCE} returned no usable fundamentals for {symbol}"
            )

        first_trade = info.get("firstTradeDateMilliseconds")
        ipo_expected = info.get("ipoExpectedDate")

        return ObservedValuation(
            snapshot=snapshot,
            first_trade_date_ms=(
                int(first_trade)
                if isinstance(first_trade, int) and not isinstance(first_trade, bool)
                else None
            ),
            ipo_expected_date=(
                str(ipo_expected).strip()
                if isinstance(ipo_expected, str) and ipo_expected.strip()
                else None
            ),
        )

    @classmethod
    def from_info(
        cls,
        info: dict[str, Any],
        *,
        reading: Provenance | None = None,
    ) -> ValuationSnapshot:
        """
        Read a valuation snapshot out of one `info` payload.

        Pure and provider-shaped so the reading of the payload can be tested
        without the network, and so the one request's growth, margins and
        cash flow are read from the same dict its valuation is.
        """

        return ValuationSnapshot(
            forward_pe=info.get("forwardPE"),
            trailing_pe=info.get("trailingPE"),
            peg_ratio=info.get("pegRatio"),
            # A payer's yield as the provider serves it, or the
            # provider's own explicit statement that nothing is paid.
            # An omission is still an absence — see `_dividend_yield`.
            dividend_yield=cls._dividend_yield(info),
            market_cap=info.get("marketCap"),
            # The cap's denomination, established from the payload's own
            # arithmetic where it can be, and absent where it cannot.
            # No field is inherited: the quote currency enters only as
            # an input to the identity check, and a cap that does not
            # reconcile establishes nothing (monetary-comparison@1,
            # MARKET_CAP_DENOMINATION.md).
            #
            # The establishing set is the domain's fingerprinted
            # membership — `sharesOutstanding` alone.
            # `impliedSharesOutstanding` is excluded: no evidence in the
            # provider boundary warrants it as a report independent of
            # the market-cap claim, and the live corpus measured it
            # reconstructing cap ÷ price to within 1.1e-7 for 64 of 64
            # securities — an identity that cannot fail checks nothing
            # (PR #143 amendment, MONETARY_COMPARISON.md §6).
            market_cap_denomination=corroborate_denomination(
                cls._ratio(info.get("marketCap")),
                cls._ratio(info.get("regularMarketPrice")),
                tuple(
                    count
                    for field in INDEPENDENT_SHARE_COUNT_FIELDS
                    for count in (cls._ratio(info.get(field)),)
                    if count is not None
                ),
                cls._text(info.get("currency")),
            ),
            # The vendor's own account of what this symbol is, recorded
            # verbatim beside the figures it arrived with, so the
            # cross-provider identity question (#134) can be asked of a
            # stored record instead of only of a live payload. A claim,
            # never a classification.
            vendor_identity=cls._vendor_identity(info),
            eps=info.get("trailingEps", info.get("forwardEps")),
            circulating_supply=info.get("circulatingSupply"),
            max_supply=info.get("maxSupply"),
            volume_24h=info.get("volume24Hr", info.get("regularMarketVolume")),
            inception=cls._inception(info.get("startDate")),
            # The provider reports a fund's expense ratio in percent
            # (0.07 for 0.07%), unlike its margins, which arrive as
            # decimal ratios. Converted here so the snapshot holds one
            # convention — measured against IB01.L, whose issuer states
            # the TER as 0.07% and whose payload carried 0.07.
            expense_ratio=cls._percentage_as_ratio(info.get("netExpenseRatio")),
            # Growth and margins arrive as decimal ratios already.
            revenue_growth=cls._ratio(info.get("revenueGrowth")),
            earnings_growth=cls._ratio(info.get("earningsGrowth")),
            gross_margin=cls._ratio(info.get("grossMargins")),
            operating_margin=cls._ratio(info.get("operatingMargins")),
            net_margin=cls._ratio(info.get("profitMargins")),
            return_on_equity=cls._ratio(info.get("returnOnEquity")),
            # Yahoo reports debt-to-equity as a percentage (195.6 for 1.96x),
            # while the balance-sheet analyst bands it as a ratio. Left as the
            # percentage it arrives as, it would read every company as
            # drowning in debt.
            debt_to_equity=cls._percentage_as_ratio(info.get("debtToEquity")),
            current_ratio=cls._ratio(info.get("currentRatio")),
            operating_cash_flow=cls._ratio(info.get("operatingCashflow")),
            free_cash_flow=cls._ratio(info.get("freeCashflow")),
            sector=cls._text(info.get("sector")),
            industry=cls._text(info.get("industry")),
            reading=reading,
        )

    @classmethod
    def _dividend_yield(cls, info: dict[str, Any]) -> float | None:
        """What the provider says about this company's dividend, or nothing.

        The defect this repairs, measured over the live corpus
        (QUALITY_BOTTLENECK_AUDIT.md §4): **`dividendYield: 0` never
        appears** — the provider represents non-payment by *omitting*
        the field this adapter read, while stating the zero explicitly
        in two fields it discarded. So every non-payer arrived as
        *unread*, and `quality-authority@1` correctly refused to band a
        business on a question it had not answered. 33 companies, 19 of
        them blocked by nothing else.

        The rule, and its two halves are not symmetric:

        - **A served `dividendYield` wins, unchanged.** Its scale is
          the #133 defect and is not touched here; this slice widens
          what is *read*, not how a figure is interpreted.
        - **An omitted `dividendYield` is read as zero only where the
          provider states that zero itself** — `trailingAnnualDividendRate`
          or `trailingAnnualDividendYield` explicitly present and equal
          to zero. That is a provider statement, not an inference from
          silence, which is the whole distinction: absence stays
          absence (`None`), and only a *stated* zero becomes evidence.

        Two guards the corpus forced. A **historical** dividend does
        not contradict a current zero — ADBE serves
        `lastDividendValue: 0.0065` from 2005 beside
        `trailingAnnualDividendRate: 0.0`, and it is a non-payer today.
        And where the two trailing fields **disagree** (one zero, one
        positive), nothing is established: two statements of the same
        fact that contradict each other are not a statement of zero.
        """

        served = cls._ratio(info.get("dividendYield"))

        if served is not None:
            return served

        stated = tuple(
            value
            for value in (
                cls._ratio(info.get("trailingAnnualDividendRate")),
                cls._ratio(info.get("trailingAnnualDividendYield")),
            )
            if value is not None
        )

        if not stated or any(value != 0.0 for value in stated):
            return None

        return 0.0

    @classmethod
    def _vendor_identity(cls, info: dict[str, Any]) -> ProviderIdentityClaim | None:
        """The vendor's identity claim, or nothing where it makes none.

        A payload carrying no name, no category token and no symbol
        offers no account of what the instrument is, and an empty claim
        stored beside the figures would read as the vendor having said
        something.
        """

        claim = vendor_claim(cls._text(info.get("symbol")) or "", info)

        if not (claim.symbol or claim.name or claim.taxonomy or claim.exchange):
            return None

        return claim

    @staticmethod
    def _ratio(value: object) -> float | None:
        """A finite number the provider reported, or nothing."""

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        return float(value)

    @classmethod
    def _percentage_as_ratio(cls, value: object) -> float | None:
        number = cls._ratio(value)

        return number / 100.0 if number is not None else None

    @staticmethod
    def _text(value: object) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _inception(value: object) -> datetime | None:
        """When the asset began trading, if the provider says."""

        if not isinstance(value, (int, float)):
            return None

        try:
            return datetime.fromtimestamp(int(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
