from dataclasses import dataclass
from datetime import datetime

from app.domain.monetary import MarketCapDenomination
from app.domain.provenance import Provenance
from app.domain.provider_identity import ProviderIdentityClaim


@dataclass(frozen=True)
class ValuationSnapshot:
    """What the fundamentals provider reports about one security.

    `reading` is when the data was actually read, and from where. A
    snapshot replayed from cache keeps its original observation time, so
    nothing downstream can mistake yesterday's fundamentals for today's.
    """

    forward_pe: float | None
    trailing_pe: float | None
    peg_ratio: float | None
    dividend_yield: float | None

    market_cap: float | None = None

    #: What the market cap is denominated in, where the payload's own
    #: arithmetic establishes it — and the honest classification where
    #: it does not. None on records written before the boundary existed,
    #: which restore as not established rather than as anything else.
    market_cap_denomination: MarketCapDenomination | None = None

    #: The vendor's own account of what this symbol is — name, category
    #: token, venue — recorded verbatim at acquisition so the
    #: cross-provider identity question (#134) can be asked of a stored
    #: record. None on records written before it was captured, which
    #: restore with the vendor having said nothing rather than with a
    #: reconstructed claim.
    vendor_identity: ProviderIdentityClaim | None = None
    eps: float | None = None

    #: What a token has instead of a balance sheet: how much of it exists,
    #: how much ever will, how much changes hands, and how long it has.
    circulating_supply: float | None = None
    max_supply: float | None = None
    volume_24h: float | None = None
    inception: datetime | None = None

    #: What a fund has where a company has margins: what owning it costs,
    #: as a decimal ratio of assets per year (0.0007 is 0.07%). Read from
    #: the same provider call as everything above — it was already in the
    #: response and being discarded while the fund playbook named cost of
    #: ownership a priority. A fact, never a score.
    expense_ratio: float | None = None

    #: Company fundamentals, all as decimal ratios (0.12 is 12%) and all read
    #: from the same provider call as the valuation above. A company has these
    #: where a token has the supply fields. `debt_to_equity` and
    #: `current_ratio` are plain ratios; the cash flows are absolute amounts
    #: in the reporting currency, read for their sign more than their size.
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None

    #: The currency the provider says the company's financial figures
    #: are reported in — its own `financialCurrency` field, carried
    #: verbatim. Distinct from the quote currency (BP.L quotes in GBp
    #: and reports in USD), which is exactly why no consumer may infer
    #: one from the other. None on records written before schema 5,
    #: which restore with the denomination not established.
    financial_currency: str | None = None
    sector: str | None = None
    industry: str | None = None

    reading: Provenance | None = None

    @property
    def observed_at(self) -> datetime | None:
        """When this was read, if it says."""

        return self.reading.observed_at if self.reading is not None else None

    @property
    def carries_nothing(self) -> bool:
        """
        True when the payload this was read from held no figure at all.

        The distinction between a reading and a failed one, which the
        fundamentals provider cannot make for itself: `Ticker.info` does
        not raise when the provider refuses, it answers with a payload
        that has nothing in it. Read literally that becomes a snapshot
        where every figure is absent, dated now — a completed reading
        which happens to say that nothing is true about the company.

        No security answers with nothing. Not a delisted one, not a
        token: a payload this empty is the provider declining, and a
        caller that cannot tell the two apart caches the refusal as
        knowledge. McDonald's spent a day reported as a company whose
        quality had not been measured, from one rate-limited call.
        """

        return not any(
            value is not None
            for field, value in vars(self).items()
            if field != "reading"
        )
