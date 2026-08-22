"""The dossier's fundamentals under the ruled precedence (2026-08-23).

Filing-established evidence first, provider-reported fallback second,
the exact refusal or absence third — and every acceptance case of the
ruling pinned: a fallback never becomes evidence, identity gates it,
zero is a figure, currency and period are never guessed, and composing
the section spends nothing.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest

from app.domain.financial_understanding import (
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
    StatementKind,
)
from app.domain.fundamentals_presentation import (
    METRICS,
    FundamentalFact,
    FundamentalStanding,
    fundamentals_for,
)
from app.domain.provenance import Provenance
from app.domain.provider_identity import ProviderIdentityClaim
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.value_provider import ValueProvider

MOMENT = datetime(2026, 8, 22, 23, 36, tzinfo=UTC)

#: Disney's shape, reduced: net margin established, gross margin read
#: and not established, in the filing route's own words.
GROSS_MARGIN_ABSENT = (
    "Gross margin needs gross_profit, which is not established: the "
    "reading located no cell holding the concept."
)


def understanding(
    measures: tuple[EstablishedMeasure, ...],
) -> FinancialUnderstanding:
    return FinancialUnderstanding(
        symbol="DIS",
        source=(
            "10-K 0001744489-25-000155 published 2025-11-13, period ended "
            "2025-09-27, via SEC EDGAR (filed with a regulator)"
        ),
        reading=Provenance(source="SEC EDGAR", observed_at=MOMENT),
        quorate=True,
        observation_count=5,
        quorum=5,
        statements=(StatementKind.INCOME_STATEMENT,),
        measures=measures,
    )


def established(measure: FinancialMeasure, value: float) -> EstablishedMeasure:
    return EstablishedMeasure(
        measure=measure,
        value=value,
        stated='"Net income" 13,431 over "Total revenues" 94,425',
    )


def absent(measure: FinancialMeasure, because: str) -> EstablishedMeasure:
    return EstablishedMeasure(measure=measure, value=None, absent_because=because)


def snapshot(**overrides: object) -> ValuationSnapshot:
    values: dict[str, object] = {
        "forward_pe": 14.485079,
        "trailing_pe": 22.222681,
        "peg_ratio": 2.68,
        "dividend_yield": 1.39,
        "gross_margin": 0.37595,
        "operating_margin": 0.19301,
        "net_margin": 0.086990006,
        "revenue_growth": 0.068,
        "earnings_growth": -0.483,
        "return_on_equity": 0.0801,
        "debt_to_equity": 0.39404,
        "current_ratio": 0.709,
        "operating_cash_flow": 16_988_999_680.0,
        "free_cash_flow": 4_860_375_040.0,
        "vendor_identity": ProviderIdentityClaim(
            provider="Yahoo Finance",
            symbol="DIS",
            name="The Walt Disney Company",
        ),
        "reading": Provenance(source="Yahoo Finance", observed_at=MOMENT),
    }
    values.update(overrides)

    return ValuationSnapshot(**values)  # type: ignore[arg-type]


def row(facts: tuple[FundamentalFact, ...], metric: str) -> FundamentalFact:
    return next(fact for fact in facts if fact.metric == metric)


# ── acceptance 1: filing absent + provider present → fallback ───────


def test_a_filing_gap_with_a_stored_provider_value_shows_the_fallback() -> None:
    facts = fundamentals_for(
        understanding((absent(FinancialMeasure.GROSS_MARGIN, GROSS_MARGIN_ABSENT),)),
        snapshot(),
    )

    gross = row(facts, "gross_margin")

    assert gross.standing is FundamentalStanding.PROVIDER_FALLBACK
    assert gross.value == 0.37595
    assert gross.source == "Yahoo Finance"
    assert gross.as_of == "received 2026-08-22"
    assert "Not established from the filing." in gross.because
    assert "provider snapshot, received 2026-08-22" in gross.because


# ── acceptance 2: both present → filing wins, source and words kept ──


def test_filing_evidence_wins_and_keeps_its_source_and_wording() -> None:
    facts = fundamentals_for(
        understanding((established(FinancialMeasure.NET_MARGIN, 0.14224),)),
        snapshot(),
    )

    net = row(facts, "net_margin")

    assert net.standing is FundamentalStanding.FILING_EVIDENCE
    # The filing's figure, not the provider's 0.08699 — a provider value
    # never overwrites filing evidence.
    assert net.value == 0.14224
    assert net.source is not None and "10-K 0001744489-25-000155" in net.source
    assert net.stated == '"Net income" 13,431 over "Total revenues" 94,425'


# ── acceptance 3: provider absent → unavailable, exact words ────────


def test_no_provider_value_preserves_the_filing_routes_exact_absence() -> None:
    facts = fundamentals_for(
        understanding((absent(FinancialMeasure.GROSS_MARGIN, GROSS_MARGIN_ABSENT),)),
        snapshot(gross_margin=None),
    )

    gross = row(facts, "gross_margin")

    assert gross.standing is FundamentalStanding.UNAVAILABLE
    assert gross.value is None
    assert gross.because == GROSS_MARGIN_ABSENT


def test_nothing_held_anywhere_is_unavailable_with_its_reason() -> None:
    facts = fundamentals_for(None, None)

    trailing = row(facts, "trailing_pe")

    assert trailing.standing is FundamentalStanding.UNAVAILABLE
    assert "No stored provider snapshot carries this figure" in trailing.because


# ── acceptance 4: provider identity unresolved → refused ────────────


def test_an_unattributable_provider_figure_is_refused_not_served() -> None:
    facts = fundamentals_for(None, snapshot(vendor_identity=None))

    gross = row(facts, "gross_margin")

    assert gross.standing is FundamentalStanding.REFUSED
    assert gross.value is None
    assert "does not identify what the provider answered about" in gross.because


# ── acceptance 5: stale provider value → dated last-known ───────────


def test_a_last_known_reading_is_a_marked_dated_fallback() -> None:
    facts = fundamentals_for(
        None,
        snapshot(
            reading=Provenance(
                source="Yahoo Finance", observed_at=MOMENT, last_known=True
            )
        ),
    )

    gross = row(facts, "gross_margin")

    assert gross.standing is FundamentalStanding.LAST_KNOWN_PROVIDER_FALLBACK
    assert gross.as_of == "received 2026-08-22"
    assert "last known" in gross.because
    assert "received 2026-08-22" in gross.because


# ── acceptance 6: measured zero remains zero ────────────────────────


def test_a_measured_zero_is_a_figure_not_an_absence() -> None:
    facts = fundamentals_for(None, snapshot(free_cash_flow=0.0))

    fcf = row(facts, "free_cash_flow")

    assert fcf.standing is FundamentalStanding.PROVIDER_FALLBACK
    assert fcf.value == 0.0


# ── acceptance 7 and 8: no guessed currency, no guessed period ──────


def test_a_cash_flow_without_established_currency_carries_none() -> None:
    facts = fundamentals_for(None, snapshot())

    ocf = row(facts, "operating_cash_flow")

    assert ocf.currency is None
    assert "Currency not stated by the stored record." in ocf.because


def test_an_established_financial_currency_is_carried_verbatim() -> None:
    facts = fundamentals_for(None, snapshot(financial_currency="USD"))

    ocf = row(facts, "operating_cash_flow")

    assert ocf.currency == "USD"
    assert "Currency not stated" not in ocf.because

    # And it denominates only currency amounts — a margin has none.
    assert row(facts, "gross_margin").currency is None


def test_no_fallback_ever_states_a_reporting_period() -> None:
    facts = fundamentals_for(None, snapshot(financial_currency="USD"))

    for fact in facts:
        if fact.standing is FundamentalStanding.PROVIDER_FALLBACK:
            assert fact.period is None

            for guessed in ("FY", "annual", "TTM", "trailing twelve"):
                assert guessed not in fact.because

    ocf = row(facts, "operating_cash_flow")

    assert "Reporting period not stated by the stored record." in ocf.because


# ── the boundary: never blended, never mapped across concepts ───────


def test_debt_to_equity_never_reads_the_filing_liabilities_ratio() -> None:
    """LIABILITIES_TO_EQUITY is a different and larger quantity."""

    facts = fundamentals_for(
        understanding((established(FinancialMeasure.LIABILITIES_TO_EQUITY, 11.0),)),
        snapshot(),
    )

    ratio = row(facts, "debt_to_equity")

    assert ratio.standing is FundamentalStanding.PROVIDER_FALLBACK
    assert ratio.value == 0.39404, "the provider's borrowings ratio, never 11.0"

    registry = {metric: measure for metric, _, _, measure, _ in METRICS}

    assert registry["debt_to_equity"] is None


def test_every_required_metric_is_present_exactly_once() -> None:
    facts = fundamentals_for(None, None)

    assert [fact.metric for fact in facts] == [metric for metric, *_ in METRICS]
    assert len(facts) == 12


# ── acceptance 9: composing the section spends nothing ──────────────


def test_the_stored_door_never_reaches_the_provider(
    tmp_path: pathlib.Path,
) -> None:
    class Explosive(ValueProvider):
        def snapshot(self, symbol: str):  # pragma: no cover - the trap
            raise AssertionError("The stored door reached the provider.")

    cache = JsonCache(str(tmp_path / "fundamentals"))

    door = CachedValueProvider(
        provider=Explosive(),
        cache=cache,
        acquires=False,
    )

    unread = door.snapshot("DIS")

    assert unread.reading is None

    # And an unread snapshot offers no fallback: the filing route's own
    # words stand, exactly as they did before this layer existed.
    facts = fundamentals_for(None, unread)

    assert all(fact.standing is FundamentalStanding.UNAVAILABLE for fact in facts)

    # Composing wrote nothing.
    assert list((tmp_path / "fundamentals").glob("*.json")) == []


# ── the schema: financial_currency carried, never invented ──────────


def test_financial_currency_survives_the_cache_round_trip(
    tmp_path: pathlib.Path,
) -> None:
    cache = JsonCache(str(tmp_path / "fundamentals"), schema=5)
    cache.write("DIS", CachedValueProvider._encode(snapshot(financial_currency="USD")))

    served = CachedValueProvider.stored(cache).snapshot("DIS")

    assert served.financial_currency == "USD"


def test_a_schema_four_record_restores_with_no_currency(
    tmp_path: pathlib.Path,
) -> None:
    """A pre-5 record's denomination is not established — never inferred."""

    encoded = CachedValueProvider._encode(snapshot())
    del encoded["financial_currency"]

    legacy = JsonCache(str(tmp_path / "fundamentals"), schema=4)
    legacy.write("DIS", encoded)

    served = CachedValueProvider.stored(
        JsonCache(
            str(tmp_path / "fundamentals"),
            schema=5,
            migrations={4: lambda value: value},
        )
    ).snapshot("DIS")

    assert served.gross_margin == 0.37595
    assert served.financial_currency is None


def test_from_info_reads_the_providers_own_financial_currency() -> None:
    read = ValueProvider.from_info(
        {"grossMargins": 0.37595, "financialCurrency": "CHF"},
        reading=Provenance(source="Yahoo Finance", observed_at=MOMENT),
    )

    assert read.financial_currency == "CHF"

    # Absent stays absent — never inferred from the quote currency.
    silent = ValueProvider.from_info(
        {"grossMargins": 0.37595, "currency": "GBp"},
        reading=Provenance(source="Yahoo Finance", observed_at=MOMENT),
    )

    assert silent.financial_currency is None


# ── the contract's own invariants ───────────────────────────────────


def test_a_showing_standing_requires_a_figure_and_vice_versa() -> None:
    with pytest.raises(ValueError):
        FundamentalFact(
            metric="gross_margin",
            label="Gross margin",
            value=None,
            unit="fraction",
            standing=FundamentalStanding.PROVIDER_FALLBACK,
            source="Yahoo Finance",
            as_of="received 2026-08-22",
            currency=None,
            period=None,
            because="a fallback with no figure",
        )

    with pytest.raises(ValueError):
        FundamentalFact(
            metric="gross_margin",
            label="Gross margin",
            value=0.37,
            unit="fraction",
            standing=FundamentalStanding.UNAVAILABLE,
            source=None,
            as_of=None,
            currency=None,
            period=None,
            because="an absence carrying a figure",
        )
