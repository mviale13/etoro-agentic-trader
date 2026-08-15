from dataclasses import dataclass

from app.domain.company_signals import CompanySignals
from app.domain.decision_rules import DecisionRule
from app.domain.finding import Finding
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class CompanyRecommendation:
    symbol: str
    recommendation: str
    confidence: int
    summary: str
    signals: CompanySignals
    evidence: tuple[Finding, ...]

    #: When the facts behind this were read.
    reading: Provenance | None = None

    #: The named, versioned rules that produced the recommendation and
    #: its confidence — the vote and its confidence formula. The band
    #: rules behind the vote's three inputs ride on the signals
    #: themselves, so the whole chain is assemblable without reading
    #: source. Identity, never endorsement.
    rules: tuple[DecisionRule, ...] = ()
