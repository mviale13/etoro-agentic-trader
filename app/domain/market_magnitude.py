"""A market capitalisation, and whether it may be compared to a threshold.

The second warrant consumer's input, and the counterpart to
`DailyChange`. The two exist for opposite reasons, and the contrast is
the point of this type.

Momentum could admit an ASSUMED translation because its output is a
**ratio over two closes of one series**, invariant under any linear
rescaling — so the unit and currency an ASSUMED warrant leaves open
cannot corrupt it. **No such protection exists here.** A market
capitalisation is consumed by comparing it with an *absolute*
threshold, and an absolute comparison is exactly what a rescaling
destroys: the same company is above the line in one currency and below
it in another, and 517.2 pence against 517.2 pounds is a hundredfold
difference in the answer.

So this type asks a harder question than `DailyChange` does. Not
merely *was it measured* and *is the translation warranted*, but also
**is the magnitude's denomination established** — because a number
whose unit is unknown cannot be compared with a threshold whose unit
is asserted.

Three states, and the third is the one the platform lacked:

1. a measured magnitude below the threshold;
2. a measured magnitude above it;
3. a magnitude **not admissible for the comparison** — which is not
   zero, not "small", and not neutral. It is the absence of an answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.monetary import MonetaryAmount
from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_translation import TranslationWarrant


@dataclass(frozen=True, slots=True)
class MarketCapMagnitude:
    """A market capitalisation with what is established about it."""

    #: The figure as the platform holds it. `None` where nothing was
    #: reported, in which case `absence` says which kind of nothing.
    amount: float | None

    #: The authority under which the reading is translated into
    #: "this company's market capitalisation".
    warrant: TranslationWarrant

    #: The currency the amount is denominated in, where the platform
    #: has actually established one. **`None` for every security
    #: today**: Yahoo reports a market capitalisation in the listing's
    #: own currency and this platform reads no currency field, so a
    #: euro figure and a dollar figure are the same bare number here.
    currency: str | None = None

    #: True where the currency above is this platform's assumption
    #: rather than a provider's statement. An assumed currency is not
    #: an established one — #134's rule, applied to a magnitude.
    currency_is_assumed: bool = True

    absence: ClaimAbsence | None = None

    def __post_init__(self) -> None:
        if self.amount is None and self.absence is None:
            raise ValueError(
                "a market capitalisation with no value and no reason is "
                "the state that lets an unread figure look like a small "
                "company"
            )

        if self.amount is not None and self.absence is not None:
            raise ValueError(
                "a market capitalisation carries a measurement or an "
                "absence, never both"
            )

    @property
    def is_measured(self) -> bool:
        return self.amount is not None

    @property
    def denomination_established(self) -> bool:
        """Whether the platform knows what unit this magnitude is in.

        The question an absolute comparison cannot avoid and a ratio
        never has to ask. False for every security on this platform
        today, and saying so is the finding rather than a failure.
        """

        return self.currency is not None and not self.currency_is_assumed

    def admissible_for_threshold(
        self,
        warrants: frozenset[TranslationWarrant],
    ) -> bool:
        """Whether this may be compared with an absolute threshold.

        A **conjunction**, because the consumer depends on more than
        one crossing and they fail independently: the semantic
        translation must be one this consumer accepts (*is this figure
        this company's market capitalisation at all*), and the
        denomination must be established (*in what unit*). Either one
        unresolved is enough to make the comparison meaningless, and a
        design that checked only the warrant would pass a figure whose
        currency nobody knows.
        """

        return (
            self.is_measured
            and self.warrant in warrants
            and self.denomination_established
        )

    def comparable_with(
        self,
        threshold: MonetaryAmount,
        warrants: frozenset[TranslationWarrant],
    ) -> bool:
        """Whether this magnitude may be placed against that threshold.

        `admissible_for_threshold` plus the rule #142 forced:
        **identical explicit denominations, or no comparison**. A CHF
        magnitude against a USD threshold is not wrong by a factor —
        it is not yet a comparison at all, and stays refused until a
        separately authorised conversion exists. `monetary-comparison@1`.
        """

        return (
            self.admissible_for_threshold(warrants)
            and self.currency == threshold.currency
        )

    def refusal(
        self,
        warrants: frozenset[TranslationWarrant],
        threshold: MonetaryAmount | None = None,
    ) -> str:
        """Why this magnitude cannot be compared, worded here once.

        Names the crossing that failed rather than the outcome, so a
        reader learns what would have to be established — and never
        implies anything about the company's size.
        """

        if threshold is None:
            if self.admissible_for_threshold(warrants):
                return ""
        elif self.comparable_with(threshold, warrants):
            return ""

        if self.absence is not None:
            return f"Company size is unavailable: {self.absence.stated}."

        if self.warrant not in warrants:
            return (
                "Company size cannot be compared with a size threshold: "
                f"the translation behind the figure is "
                f"{self.warrant.stated.lower()} — {self.warrant.because}."
            )

        if not self.denomination_established:
            return (
                "Company size cannot be compared with a size threshold: the "
                "figure's currency is not established, and a magnitude whose "
                "denomination is unknown cannot be placed above or below an "
                "absolute amount."
            )

        # Established, and in a different currency from the threshold:
        # honest, and waiting on a conversion this platform has not yet
        # authorised. Deliberately not "unavailable" — the figure is
        # known, and what is missing is a licensed transformation.
        assert threshold is not None

        return (
            f"Company size is established in {self.currency} and the size "
            f"threshold is declared in {threshold.currency}; the comparison "
            "is refused pending an authorised currency conversion, which "
            "this platform does not yet hold."
        )

    @classmethod
    def measured(
        cls,
        amount: float,
        *,
        warrant: TranslationWarrant,
        currency: str | None = None,
        currency_is_assumed: bool = True,
    ) -> MarketCapMagnitude:
        return cls(
            amount=amount,
            warrant=warrant,
            currency=currency,
            currency_is_assumed=currency_is_assumed,
        )

    @classmethod
    def unmeasured(
        cls,
        absence: ClaimAbsence,
        *,
        warrant: TranslationWarrant,
    ) -> MarketCapMagnitude:
        return cls(amount=None, warrant=warrant, absence=absence)
