from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.decision_participation import (
    DecisionAuthority,
    SignalParticipation,
    SignalStanding,
)
from app.domain.decision_rules import (
    DECISION_AUTHORITY,
    SIGNAL_VOTE,
    VOTE_CONFIDENCE,
)
from app.domain.finding import Dimension


class CompanyCommitteeService:
    VALUE_WEIGHT = 0.40
    QUALITY_WEIGHT = 0.35
    MOMENTUM_WEIGHT = 0.25

    BUY_THRESHOLD = 0.50
    SELL_THRESHOLD = -0.50

    #: The constants of `vote-confidence@1`, named so the provenance
    #: guard can fingerprint them. The formula reads the verdict's own
    #: strength as its confidence — recorded, not endorsed.
    CONFIDENCE_BASE = 50
    CONFIDENCE_SPAN = 50

    #: What each band contributes to the direction. **A band absent
    #: from these tables is an absence, not a zero** — UNKNOWN is
    #: deliberately not a key, which is the whole separation: it
    #: cannot be looked up, so it cannot vote.
    _VALUE_DIRECTIONS = {"CHEAP": 1, "FAIR": 0, "EXPENSIVE": -1}
    _QUALITY_DIRECTIONS = {"HIGH": 1, "MEDIUM": 0, "LOW": -1}
    _MOMENTUM_DIRECTIONS = {"BULLISH": 1, "NEUTRAL": 0, "BEARISH": -1}

    def evaluate(
        self,
        symbol: str,
        signals: CompanySignals,
    ) -> CompanyRecommendation:
        authority = self._authority(signals)

        # Direction, over participating signals at their **original**
        # weights. No renormalisation: a survivor must not gain
        # authority from a neighbour's absence, which is the failure
        # #138 measured when it modelled renormalising over survivors.
        #
        # Arithmetically this is what the vote always computed — an
        # abstention contributes nothing, which is what scoring it zero
        # also did. What changed is that the abstention is now visible,
        # and that acting on the result is a separate question below.
        score = sum(standing.contribution for standing in authority.standings)

        direction = self._recommendation(score)

        # The two authority gates. A direction the platform may not act
        # on is reported as HOLD — and the lean survives on the
        # recommendation, because forcing it to NEUTRAL would destroy a
        # reading the platform genuinely made.
        recommendation = direction if authority.may_act else "HOLD"

        confidence = round(self.CONFIDENCE_BASE + abs(score) * self.CONFIDENCE_SPAN)

        # Attributed here because here is where the producing signal is
        # known by name. A later layer reading this flat list cannot tell
        # a valuation finding from a quality one except by its wording,
        # and a committee whose remit was matched on wording would be
        # guessing at exactly the thing this composition already knows.
        evidence = (
            *(item.about(Dimension.VALUATION) for item in signals.value.evidence),
            *(item.about(Dimension.QUALITY) for item in signals.quality.evidence),
            *(item.about(Dimension.MOMENTUM) for item in signals.momentum.evidence),
        )

        return CompanyRecommendation(
            symbol=symbol.upper().strip(),
            recommendation=recommendation,
            confidence=confidence,
            summary=self._summary(
                recommendation,
                signals,
            ),
            signals=signals,
            evidence=evidence,
            reading=signals.reading,
            direction=direction,
            authority=authority,
            rules=(SIGNAL_VOTE, VOTE_CONFIDENCE, DECISION_AUTHORITY),
        )

    def _authority(self, signals: CompanySignals) -> DecisionAuthority:
        """Which signals spoke, which were expected, which do not apply."""

        return DecisionAuthority(
            standings=(
                self._standing(
                    "value",
                    self.VALUE_WEIGHT,
                    signals.value.applicable,
                    signals.value.valuation,
                    self._VALUE_DIRECTIONS,
                ),
                self._standing(
                    "quality",
                    self.QUALITY_WEIGHT,
                    signals.quality.applicable,
                    signals.quality.quality,
                    self._QUALITY_DIRECTIONS,
                ),
                self._standing(
                    "momentum",
                    self.MOMENTUM_WEIGHT,
                    signals.momentum.applicable,
                    signals.momentum.trend,
                    self._MOMENTUM_DIRECTIONS,
                ),
            )
        )

    @staticmethod
    def _standing(
        name: str,
        weight: float,
        applicable: bool,
        band: str,
        directions: dict[str, int],
    ) -> SignalStanding:
        """One signal's part, from its own band and applicability.

        A band absent from `directions` is an absence, not a zero — the
        distinction the kernel previously could not draw. A genuine
        middle band *is* in the table, at direction zero, so it
        participates and counts fully towards coverage.
        """

        if not applicable:
            return SignalStanding(
                name=name,
                weight=weight,
                participation=SignalParticipation.NOT_APPLICABLE,
            )

        if band not in directions:
            return SignalStanding(
                name=name,
                weight=weight,
                participation=SignalParticipation.EXPECTED_ABSENT,
            )

        return SignalStanding(
            name=name,
            weight=weight,
            participation=SignalParticipation.PARTICIPATING,
            direction=directions[band],
        )

    def _recommendation(
        self,
        score: float,
    ) -> str:
        if score >= self.BUY_THRESHOLD:
            return "BUY"

        if score <= self.SELL_THRESHOLD:
            return "SELL"

        return "HOLD"

    @staticmethod
    def _summary(
        recommendation: str,
        signals: CompanySignals,
    ) -> str:
        return (
            f"{recommendation}: "
            f"value is {signals.value.valuation.lower()}, "
            f"quality is {signals.quality.quality.lower()}, "
            f"and momentum is {signals.momentum.trend.lower()}."
        )
