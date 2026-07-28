from app.domain.company_facts import CompanyFacts


def test_company_facts() -> None:
    company = CompanyFacts(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type="Stock",
        exchange="NASDAQ",
        current_price=510.0,
        daily_change_pct=1.5,
        market_cap=3_800_000_000_000,
        forward_pe=35.0,
        eps=14.2,
        dividend_yield=0.72,
        sector="Technology",
        industry="Software",
    )

    assert company.symbol == "MSFT"
    assert company.name == "Microsoft"
    assert company.exchange == "NASDAQ"
    assert company.forward_pe == 35.0
