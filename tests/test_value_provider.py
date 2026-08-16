from app.providers.value_provider import ValueProvider


class FakeTicker:
    @property
    def info(self):
        return {
            "forwardPE": 21.5,
            "trailingPE": 24.1,
            "pegRatio": 1.4,
            "dividendYield": 0.012,
        }


def test_value_provider(monkeypatch):
    monkeypatch.setattr(
        "yfinance.Ticker",
        lambda symbol: FakeTicker(),
    )

    valuation = ValueProvider().snapshot("MSFT")

    assert valuation.forward_pe == 21.5
    assert valuation.trailing_pe == 24.1
    assert valuation.peg_ratio == 1.4
    assert valuation.dividend_yield == 0.012


def test_fundamentals_are_read_from_the_same_call() -> None:
    valuation = ValueProvider.from_info(
        {
            "revenueGrowth": 0.164,
            "earningsGrowth": 0.21,
            "grossMargins": 0.486,
            "operatingMargins": 0.31,
            "profitMargins": 0.243,
            "returnOnEquity": 1.5,
            "currentRatio": 1.07,
            "operatingCashflow": 118_000_000_000,
            "freeCashflow": 99_000_000_000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
    )

    assert valuation.revenue_growth == 0.164
    assert valuation.gross_margin == 0.486
    assert valuation.net_margin == 0.243
    assert valuation.current_ratio == 1.07
    assert valuation.free_cash_flow == 99_000_000_000
    assert valuation.sector == "Technology"


def test_debt_to_equity_is_normalised_from_percent_to_ratio() -> None:
    """Yahoo reports 78.4 for 0.78x; scored raw, every company reads broke."""

    valuation = ValueProvider.from_info({"debtToEquity": 78.4})

    assert valuation.debt_to_equity == 0.784


def test_missing_or_unreadable_fundamentals_are_absent_not_zero() -> None:
    valuation = ValueProvider.from_info(
        {"grossMargins": None, "debtToEquity": "n/a", "sector": ""}
    )

    assert valuation.gross_margin is None
    assert valuation.debt_to_equity is None
    assert valuation.sector is None


class TestTheStatedZeroIsEvidence:
    """A provider that omits a field has not answered; one that prints
    zero has.

    Measured over the live corpus (QUALITY_BOTTLENECK_AUDIT.md §4):
    Yahoo represents non-payment by *omitting* `dividendYield` — the
    value 0 never appears there for a company — while stating the zero
    explicitly in `trailingAnnualDividendRate` and
    `trailingAnnualDividendYield`. Reading only the omitted field made
    every non-payer arrive as unread, and `quality-authority@1`
    correctly refused to band a business on an unanswered question.
    Payloads below are the live shapes as measured 2026-08-16.
    """

    def test_tesla_states_zero_and_is_read_as_zero(self) -> None:
        valuation = ValueProvider.from_info(
            {
                "trailingAnnualDividendRate": 0.0,
                "trailingAnnualDividendYield": 0.0,
                "payoutRatio": 0.0,
            }
        )

        assert valuation.dividend_yield == 0.0

    def test_amazon_states_zero_and_is_read_as_zero(self) -> None:
        valuation = ValueProvider.from_info(
            {"trailingAnnualDividendRate": 0.0, "trailingAnnualDividendYield": 0.0}
        )

        assert valuation.dividend_yield == 0.0

    def test_adobes_ancient_dividend_does_not_contradict_todays_zero(self) -> None:
        """ADBE serves `lastDividendValue: 0.0065` — from 2005 — beside a
        stated trailing zero. A historical payment is not a current one."""

        valuation = ValueProvider.from_info(
            {
                "trailingAnnualDividendRate": 0.0,
                "trailingAnnualDividendYield": 0.0,
                "lastDividendValue": 0.0065,
                "fiveYearAvgDividendYield": 0.12,
            }
        )

        assert valuation.dividend_yield == 0.0

    def test_a_payer_is_read_from_the_served_field_unchanged(self) -> None:
        """PG's live shape. The served value wins and is not rescaled —
        `dividendYield`'s scale is #133's defect and is untouched here."""

        valuation = ValueProvider.from_info(
            {
                "dividendYield": 3.01,
                "trailingAnnualDividendRate": 4.259,
                "trailingAnnualDividendYield": 0.029523084,
            }
        )

        assert valuation.dividend_yield == 3.01

    def test_a_payload_with_no_dividend_field_at_all_is_unreadable(self) -> None:
        """NESN.ZU's live shape: the vendor answers nothing. Absent stays
        absent — an omission is never read as a zero."""

        valuation = ValueProvider.from_info({"marketCap": 1_000_000.0})

        assert valuation.dividend_yield is None

    def test_a_null_trailing_field_is_not_a_stated_zero(self) -> None:
        valuation = ValueProvider.from_info(
            {"trailingAnnualDividendRate": None, "trailingAnnualDividendYield": None}
        )

        assert valuation.dividend_yield is None

    def test_two_trailing_fields_disagreeing_establish_nothing(self) -> None:
        """One zero, one positive: two statements of one fact that
        contradict each other are not a statement of zero."""

        valuation = ValueProvider.from_info(
            {"trailingAnnualDividendRate": 0.0, "trailingAnnualDividendYield": 0.031}
        )

        assert valuation.dividend_yield is None

    def test_a_positive_trailing_value_is_never_promoted(self) -> None:
        """The crossing carries the zero and nothing else.

        A trailing rate is an amount per share and a trailing yield is
        backward-looking; neither is `dividendYield`'s quantity, so a
        positive value in them is not read as this company's dividend
        yield. Only the zero — which both spellings agree on — is.
        """

        valuation = ValueProvider.from_info({"trailingAnnualDividendRate": 4.259})

        assert valuation.dividend_yield is None

    def test_the_quality_factor_now_reads_a_non_payer(self) -> None:
        """End to end: the stated zero reaches the factor as a measured
        `No dividend.`, where an omission left it unread.

        The factor's own scoring is untouched — zero still earns no
        point — and what changed is that the question is answered at
        all, so completeness can be reached.
        """

        from app.domain.company_facts import CompanyFacts
        from app.services.quality_signal_service import QualitySignalService
        from tests.conftest import admissible_market_cap

        valuation = ValueProvider.from_info(
            {"trailingAnnualDividendRate": 0.0, "trailingAnnualDividendYield": 0.0}
        )

        facts = CompanyFacts(
            instrument_id=1,
            symbol="TSLA",
            name="Tesla",
            asset_type="stock",
            exchange="4",
            market_cap=50_000_000_000.0,
            market_cap_magnitude=admissible_market_cap(50_000_000_000.0),
            eps=1.10,
            dividend_yield=valuation.dividend_yield,
        )

        signal = QualitySignalService().build(facts)

        assert signal.available == 3
        assert signal.earned == 2
        assert signal.quality == "MEDIUM"
        assert "No dividend." in tuple(f.statement for f in signal.evidence)
