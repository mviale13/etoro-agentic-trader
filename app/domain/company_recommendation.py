from dataclasses import dataclass

from app.domain.company_signals import CompanySignals
from app.domain.decision_participation import DecisionAuthority
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

    #: What the evidence points at, before authority is considered.
    #:
    #: Carried apart from `recommendation` because the two answer
    #: different questions and a scalar could not hold both: a security
    #: whose readings lean bullish while the platform holds too little
    #: of the expected evidence is a HOLD *with a bullish lean*, and
    #: flattening that to NEUTRAL would destroy a reading the platform
    #: genuinely made. None where no direction was computed.
    direction: str | None = None

    #: Which signals spoke, which were expected and silent, which do
    #: not apply — and therefore whether the direction may be acted on.
    authority: DecisionAuthority | None = None

    @property
    def lean_without_authority(self) -> str | None:
        """A direction the platform holds but may not act on, if any.

        The investor-facing distinction this separation exists for:
        *the evidence leans bearish and we do not hold enough of it* is
        a different statement from *the evidence is balanced*, and
        before this they were the same word.
        """

        if self.authority is None or self.authority.may_act:
            return None

        if self.direction in (None, "HOLD"):
            return None

        return self.direction

    #: The named, versioned rules that produced the recommendation and
    #: its confidence — the vote and its confidence formula. The band
    #: rules behind the vote's three inputs ride on the signals
    #: themselves, so the whole chain is assemblable without reading
    #: source. Identity, never endorsement.
    rules: tuple[DecisionRule, ...] = ()
