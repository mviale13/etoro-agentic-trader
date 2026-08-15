"""Short-term price momentum — and what it requires before it will speak.

The first consumer of the provider boundary (#134). Its input used to
be a bare `float`, which could not distinguish a security that did not
move from one whose movement was never measured; the adapter wrote
`0.0` for both, and this service read the second as NEUTRAL at
confidence 60. **Neutral is an analytical conclusion; an acquisition
failure is not one**, and a conclusion drawn from a manufactured
number is false evidence regardless of how reasonable it looks.

So this service now states what authority it needs, and abstains when
it does not have it. It gains no new score for abstaining: an
unestablished move takes the UNKNOWN path that has always existed for
an absent one.
"""

from __future__ import annotations

from app.domain.company_facts import CompanyFacts
from app.domain.daily_change import ChangeBasis, DailyChange
from app.domain.decision_rules import MOMENTUM_BANDS, MOMENTUM_INPUT_ELIGIBILITY
from app.domain.finding import Finding
from app.domain.momentum_signal import MomentumSignal
from app.domain.provider_translation import TranslationWarrant

#: The translation warrants under which Momentum will read a number as
#: a price move — `momentum-input-eligibility@1`.
#:
#: **Explicit membership, never an ordering.** There is no "at least
#: DECLARED": each member is admitted for a stated reason, and a
#: warrant absent from this set is refused whatever it is called.
#:
#: Why ASSUMED is sufficient *here*, and this is the whole argument:
#: a daily change is not a provider figure at all. This platform
#: computes it as `(latest - previous) / previous` over two closes of
#: **one series**, and that ratio is invariant under any linear
#: rescaling of the series. Whether Yahoo's closes are pence or
#: pounds, dollars or a yield times ten, the *change between two of
#: them* is the same number. So the two things ASSUMED leaves open for
#: a price — its unit and its currency — cannot corrupt this
#: particular reading, and refusing ASSUMED would silence Momentum for
#: every security on the platform to protect against an error that is
#: arithmetically impossible for this quantity.
#:
#: That argument is deliberately narrow and **does not generalise**.
#: It works because the consumer needs a *ratio*; a consumer needing a
#: magnitude — a dividend yield, a market capitalisation — gets no
#: such protection from scale invariance, which is exactly why this
#: slice repairs one input and not the others.
#:
#: UNKNOWN is refused because it means the provenance is insufficient
#: to say why the mapping would be valid at all. That is not a weaker
#: version of ASSUMED: it is the state in which the platform cannot
#: name what the number is, and no invariance argument can rescue a
#: quantity whose identity is unsettled.
#:
#: VERIFIED, VALIDATED and DECLARED are admitted for the ordinary
#: reason — each carries evidence or a provider statement about what
#: the reading means, which is more than this consumer needs.
ELIGIBLE_WARRANTS: frozenset[TranslationWarrant] = frozenset(
    {
        TranslationWarrant.VERIFIED,
        TranslationWarrant.VALIDATED,
        TranslationWarrant.DECLARED,
        TranslationWarrant.ASSUMED,
    }
)


class MomentumSignalService:
    STRONG_POSITIVE_THRESHOLD = 2.0
    POSITIVE_THRESHOLD = 0.5
    NEGATIVE_THRESHOLD = -0.5
    STRONG_NEGATIVE_THRESHOLD = -2.0

    #: Named on the class so the provenance guard can fingerprint the
    #: eligibility rule the same way it fingerprints the bands.
    ELIGIBLE_WARRANTS = ELIGIBLE_WARRANTS

    def build(
        self,
        company: CompanyFacts,
    ) -> MomentumSignal:
        change = self._change(company)

        if change is None or not change.admissible_under(self.ELIGIBLE_WARRANTS):
            return self._unknown(change)

        # Established from here down: a measured move, under a warrant
        # this consumer accepts, described over a period the evidence
        # supports.
        percent = change.percent

        assert percent is not None  # guaranteed by `admissible_under`

        window = change.window

        if percent >= self.STRONG_POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                rule=MOMENTUM_BANDS,
                strength="STRONG",
                confidence=85,
                evidence=(
                    Finding.favourable(
                        f"{company.symbol} gained {percent:+.2f}% {window}."
                    ),
                    Finding.favourable(
                        "Short-term price momentum is strongly positive."
                    ),
                ),
            )

        if percent >= self.POSITIVE_THRESHOLD:
            return MomentumSignal(
                trend="BULLISH",
                rule=MOMENTUM_BANDS,
                strength="MODERATE",
                confidence=70,
                evidence=(
                    Finding.favourable(
                        f"{company.symbol} gained {percent:+.2f}% {window}."
                    ),
                    Finding.favourable("Short-term price momentum is positive."),
                ),
            )

        if percent <= self.STRONG_NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                rule=MOMENTUM_BANDS,
                strength="STRONG",
                confidence=85,
                evidence=(
                    Finding.adverse(
                        f"{company.symbol} declined {percent:+.2f}% {window}."
                    ),
                    Finding.adverse("Short-term price momentum is strongly negative."),
                ),
            )

        if percent <= self.NEGATIVE_THRESHOLD:
            return MomentumSignal(
                trend="BEARISH",
                rule=MOMENTUM_BANDS,
                strength="MODERATE",
                confidence=70,
                evidence=(
                    Finding.adverse(
                        f"{company.symbol} declined {percent:+.2f}% {window}."
                    ),
                    Finding.adverse("Short-term price momentum is negative."),
                ),
            )

        # A genuine, admissible flat session. This is the only path that
        # may still call the security neutral, and it is reached only
        # because something was actually measured.
        return MomentumSignal(
            trend="NEUTRAL",
            rule=MOMENTUM_BANDS,
            strength="WEAK",
            confidence=60,
            evidence=(
                Finding.neutral(f"{company.symbol} moved {percent:+.2f}% {window}."),
                Finding.neutral("No meaningful short-term momentum is visible."),
            ),
        )

    @staticmethod
    def _change(company: CompanyFacts) -> DailyChange | None:
        """The move this security's facts carry, however they carry it.

        `daily_change` is authoritative where the acquisition supplied
        one. Where only the legacy `daily_change_pct` float is present,
        it is read as a measured change under an ASSUMED warrant and an
        unstated session — which is what a caller writing that field
        directly is asserting. The compatibility path is honest
        because the defect was never the float in isolation: it was the
        *adapter* manufacturing one where nothing had been measured,
        and the adapter no longer does.
        """

        if company.daily_change is not None:
            return company.daily_change

        if company.daily_change_pct is None:
            return None

        return DailyChange.measured(
            company.daily_change_pct,
            warrant=TranslationWarrant.ASSUMED,
            basis=ChangeBasis.UNKNOWN_SESSION,
        )

    def _unknown(self, change: DailyChange | None) -> MomentumSignal:
        """No opinion, and the reason it is not an opinion.

        The same UNKNOWN this service has always returned for an absent
        change — deliberately not a new state and not a new score.
        What is new is that a manufactured zero arrives here instead of
        arriving at NEUTRAL.
        """

        because = (
            change.refusal(self.ELIGIBLE_WARRANTS)
            if change is not None
            else "Daily price change is unavailable."
        )

        return MomentumSignal(
            trend="UNKNOWN",
            strength="UNKNOWN",
            confidence=20,
            rule=MOMENTUM_INPUT_ELIGIBILITY,
            evidence=(Finding.neutral(because),),
        )
