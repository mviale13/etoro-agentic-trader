from dataclasses import dataclass

from app.domain.company_research import CompanyResearch
from app.domain.earnings_schedule import EarningsSchedule
from app.domain.momentum_signal import MomentumSignal
from app.domain.provenance import Provenance
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

    #: The fundamental analysts' read of the business — growth, profitability,
    #: balance sheet and cash flow. None for anything without a company behind
    #: it (a fund, a token), and for a company only where its fundamentals
    #: were read at all.
    research: CompanyResearch | None = None

    #: When this company next reports, carried from the facts rather than
    #: judged. Nothing here scores a security for reporting soon: a date is
    #: not an argument, and what a report will say is unknown until it is
    #: published. It rides with the signals because this is the object the
    #: investment case reads a security through.
    earnings: EarningsSchedule | None = None

    #: The stalest reading these signals were derived from. Signals are a
    #: judgement about facts, and a judgement is exactly as current as the
    #: facts under it.
    reading: Provenance | None = None
