from dataclasses import dataclass

from app.domain.momentum_signal import MomentumSignal
from app.domain.quality_signal import QualitySignal
from app.domain.risk_signal import RiskSignal
from app.domain.value_signal import ValueSignal


@dataclass(frozen=True, slots=True)
class CompanySignals:
    value: ValueSignal
    momentum: MomentumSignal
    quality: QualitySignal

    #: How violently the security itself has moved. None where the price
    #: history could not be read at all.
    risk: RiskSignal | None = None
