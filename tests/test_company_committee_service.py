from app.domain.company_signals import CompanySignals
from app.domain.momentum_signal import MomentumSignal
from app.domain.quality_signal import QualitySignal
from app.domain.value_signal import ValueSignal
from app.services.company_committee_service import CompanyCommitteeService


def build_signals(
    *,
    value: str,
    quality: str,
    momentum: str,
) -> CompanySignals:
    return CompanySignals(
        value=ValueSignal(
            valuation=value,
            confidence=90,
            evidence=(f"Value is {value}.",),
        ),
        momentum=MomentumSignal(
            trend=momentum,
            strength="STRONG",
            confidence=90,
            evidence=(f"Momentum is {momentum}.",),
        ),
        quality=QualitySignal(
            quality=quality,
            confidence=90,
            evidence=(f"Quality is {quality}.",),
        ),
    )


def test_buy_when_signals_are_positive() -> None:
    recommendation = CompanyCommitteeService().evaluate(
        "MSFT",
        build_signals(
            value="CHEAP",
            quality="HIGH",
            momentum="BULLISH",
        ),
    )

    assert recommendation.symbol == "MSFT"
    assert recommendation.recommendation == "BUY"
    assert recommendation.confidence == 100
    assert len(recommendation.evidence) == 3


def test_sell_when_signals_are_negative() -> None:
    recommendation = CompanyCommitteeService().evaluate(
        "MSFT",
        build_signals(
            value="EXPENSIVE",
            quality="LOW",
            momentum="BEARISH",
        ),
    )

    assert recommendation.recommendation == "SELL"
    assert recommendation.confidence == 100


def test_hold_when_signals_are_mixed() -> None:
    recommendation = CompanyCommitteeService().evaluate(
        "MSFT",
        build_signals(
            value="EXPENSIVE",
            quality="HIGH",
            momentum="BULLISH",
        ),
    )

    assert recommendation.recommendation == "HOLD"
    assert recommendation.confidence == 60


def test_unknown_signals_are_neutral() -> None:
    recommendation = CompanyCommitteeService().evaluate(
        "MSFT",
        build_signals(
            value="UNKNOWN",
            quality="UNKNOWN",
            momentum="UNKNOWN",
        ),
    )

    assert recommendation.recommendation == "HOLD"
    assert recommendation.confidence == 50
