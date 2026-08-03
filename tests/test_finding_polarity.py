"""What a signal knows when it scores, and used to throw away."""

from app.domain.company_facts import CompanyFacts
from app.domain.finding import Sense, statements, statements_where
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService


def facts(**overrides: object) -> CompanyFacts:
    defaults: dict[str, object] = {
        "instrument_id": 1,
        "symbol": "TEST",
        "name": "Test",
        "asset_type": "stock",
        "exchange": "4",
    }

    return CompanyFacts(**{**defaults, **overrides})  # type: ignore[arg-type]


def test_a_loss_making_company_does_not_report_a_strength() -> None:
    """
    "Negative earnings." was indistinguishable from "Positive earnings."

    Both were bare strings in the same tuple, so any surface presenting
    that tuple as a case for the security presented a loss as a reason to
    buy it.
    """

    signal = QualitySignalService().build(
        facts(market_cap=50_000_000_000.0, eps=-3.0, dividend_yield=0.0)
    )

    assert statements_where(signal.evidence, Sense.FAVOURABLE) == (
        "Large-cap company.",
    )
    assert statements_where(signal.evidence, Sense.ADVERSE) == ("Negative earnings.",)


def test_a_measurement_that_argues_neither_way_is_neutral() -> None:
    """
    Being mid-cap is not a failing, and this service never scored it as one.

    It awards a point for size or no point, never a penalty, so the absence
    of the point is an observation rather than an argument.
    """

    signal = QualitySignalService().build(
        facts(market_cap=2_000_000_000.0, eps=1.0, dividend_yield=0.0)
    )

    neutral = statements_where(signal.evidence, Sense.NEUTRAL)

    assert "Small or mid-cap company." in neutral
    assert "No dividend." in neutral


def test_an_absent_measurement_is_never_an_argument() -> None:
    """It reports that nothing could be read, which is neither for nor against."""

    quality = QualitySignalService().build(facts())
    value = ValueSignalService().build(facts())

    for signal in (quality, value):
        assert statements_where(signal.evidence, Sense.FAVOURABLE) == ()
        assert statements_where(signal.evidence, Sense.ADVERSE) == ()


def test_a_risk_readings_sense_is_the_band_it_lands_in() -> None:
    """
    12% volatility and 94% volatility are both measurements.

    Only one of them is an argument against holding the security, and the
    service already draws that line to set the risk level.
    """

    calm = RiskSignalService().build(facts(realized_volatility=0.12, max_drawdown=0.10))
    violent = RiskSignalService().build(
        facts(realized_volatility=0.94, max_drawdown=0.61)
    )

    assert statements_where(calm.evidence, Sense.ADVERSE) == ()
    assert len(statements_where(calm.evidence, Sense.FAVOURABLE)) == 2

    assert statements_where(violent.evidence, Sense.FAVOURABLE) == ()
    assert len(statements_where(violent.evidence, Sense.ADVERSE)) == 2


def test_the_full_record_survives_the_split() -> None:
    """Sorting findings by sense must not lose any of them."""

    signal = QualitySignalService().build(
        facts(market_cap=50_000_000_000.0, eps=-3.0, dividend_yield=0.02)
    )

    by_sense = tuple(
        statement
        for sense in (Sense.FAVOURABLE, Sense.ADVERSE, Sense.NEUTRAL)
        for statement in statements_where(signal.evidence, sense)
    )

    assert sorted(by_sense) == sorted(statements(signal.evidence))
