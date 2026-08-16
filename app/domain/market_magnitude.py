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
from app.domain.monetary_translation import MonetaryTranslation
from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_identity import CrossProviderIdentity, IdentityStanding
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

    #: Whose market capitalisation this is — the #134 cross-provider
    #: join for the symbol the figure arrived under. Identity is a
    #: prerequisite, not a parallel crossing that another crossing can
    #: compensate for: a figure about a disputed subject stays out of
    #: every comparison however well its magnitude, denomination and
    #: translation are established. `None` means the question was never
    #: evaluated, which is not authority either.
    identity: CrossProviderIdentity | None = None

    #: The authorised route from an established foreign denomination
    #: to another currency's threshold — an explicit, evidenced FX
    #: translation of exactly this amount (C6). None where no rate has
    #: been read, where the denomination is not established, or where
    #: the figure is USD and needs none. The original amount above is
    #: never altered: the translation carries the derived claim beside
    #: it, with its own evidence.
    translation: MonetaryTranslation | None = None

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

        if self.translation is not None and (
            self.amount is None
            or self.currency is None
            or self.currency_is_assumed
            or self.translation.original.amount != self.amount
            or self.translation.original.currency != self.currency
        ):
            raise ValueError(
                "a translation must be of exactly this magnitude — the "
                "established amount in its established currency; anything "
                "else is a derived claim about a different figure wearing "
                "this one's evidence"
            )

    @property
    def is_measured(self) -> bool:
        return self.amount is not None

    @property
    def identity_authorised(self) -> bool:
        """Whether the figure's subject is settled enough to consume it.

        Invariant 2 applied to a magnitude: identity is enforced
        *before* the reading, so this term is a prerequisite the other
        three crossings can never compensate for. Two states refuse.
        An **unresolved** join — the providers' own accounts disagree
        about what the symbol is — poisons every downstream authority:
        a perfectly denominated figure about a disputed subject is a
        perfectly denominated answer to an unsettled question. And an
        **unevaluated** join (`None`) is not authority either: a
        prerequisite nobody checked is not a prerequisite met.

        An *assumed* join passes, by #134's own ruling: every live
        join on this platform rests on symbol equality and is named
        ASSUMED rather than silently trusted. Requiring corroboration
        here would be the identity boundary's own future tightening,
        made for the whole platform at once — not smuggled in through
        one consumer's gate.
        """

        return (
            self.identity is not None
            and self.identity.standing is not IdentityStanding.UNRESOLVED
        )

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

        An explicit **conjunction over four crossings**, because the
        consumer depends on all of them and they fail independently:

        - **identity** — whose figure this is (#134); a prerequisite,
          checked first and substitutable by nothing;
        - **magnitude** — a measured figure at all;
        - **translation** — the reading of it as this company's market
          capitalisation is warranted (*is this figure a market cap*);
        - **denomination** — the unit it is expressed in is
          established (*in what unit*).

        Establishing one crossing never settles another: SPCX's USD
        would be establishable while its identity stays disputed, and
        a design that let denomination authority stand in for identity
        authority would compare a perfectly-denominated figure about
        an unsettled subject. Any one term failing refuses the
        comparison.
        """

        return (
            self.identity_authorised
            and self.is_measured
            and self.warrant in warrants
            and self.denomination_established
        )

    def comparable_with(
        self,
        threshold: MonetaryAmount,
        warrants: frozenset[TranslationWarrant],
    ) -> bool:
        """Whether this magnitude may be placed against that threshold.

        `admissible_for_threshold` plus the rule #142 forced —
        **identical explicit denominations, or no comparison** — now
        with the one authorised exception C6 adds: an established
        foreign magnitude carrying an **authorised** FX translation
        into the threshold's currency compares through that
        translation (`fx-translation@1`).

        The order is load-bearing. Translation is consulted *last*,
        only where identity, magnitude and denomination already hold:
        an FX rate can never rescue an unresolved earlier crossing,
        because the conjunction refuses before the translation is ever
        looked at. And an unauthorised translation — a rate from
        another day — is exactly no translation here.
        """

        if not self.admissible_for_threshold(warrants):
            return False

        if self.currency == threshold.currency:
            return True

        return (
            self.translation is not None
            and self.translation.authorised
            and self.translation.target == threshold.currency
        )

    def comparable_amount(
        self,
        threshold: MonetaryAmount,
        warrants: frozenset[TranslationWarrant],
    ) -> float | None:
        """The amount in the threshold's own currency, or nothing.

        The number a consumer may actually place against the
        threshold: the amount itself where the currencies already
        agree, the *translated* amount where an authorised translation
        carries it across, and nothing everywhere else. A consumer
        that read `amount` directly for a foreign magnitude would be
        comparing Swiss francs against a dollar line — the exact
        wrong-by-a-factor comparison this boundary exists to refuse —
        so the translated route exists only through this door.
        """

        if not self.comparable_with(threshold, warrants):
            return None

        if self.currency == threshold.currency:
            return self.amount

        assert self.translation is not None  # guaranteed by comparable_with

        derived = self.translation.translated

        return derived.amount if derived is not None else None

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

        if (
            self.identity is not None
            and self.identity.standing is IdentityStanding.UNRESOLVED
        ):
            # First, because identity is a prerequisite: whatever else
            # is established about the figure, its subject is not
            # settled, and the reason must say *identity* — never
            # currency, and never anything that implies the company's
            # size.
            return (
                "Company size cannot be compared with a size threshold: the "
                "providers' accounts of what this symbol is disagree — "
                f"{self.identity.because} — and no market-cap input is "
                "eligible while the instrument's identity is unresolved, "
                "whatever else is established about the figure."
            )

        if self.absence is not None:
            return f"Company size is unavailable: {self.absence.stated}."

        if self.identity is None:
            return (
                "Company size cannot be compared with a size threshold: "
                "the cross-provider identity of the instrument was never "
                "evaluated, and a figure whose subject is unexamined "
                "cannot enter a comparison."
            )

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
        # honest, and waiting on an authorised translation. The two
        # ways of lacking one are worded apart, because they call for
        # different repairs: no rate was ever read, or a rate is held
        # whose observation belongs to a different day than the
        # figure's own.
        assert threshold is not None

        if self.translation is not None and not self.translation.authorised:
            return (
                f"Company size is established in {self.currency} and the "
                f"size threshold is declared in {threshold.currency}; "
                f"{self.translation.stated}"
            )

        return (
            f"Company size is established in {self.currency} and the size "
            f"threshold is declared in {threshold.currency}; the comparison "
            f"is refused pending an authorised currency translation — no "
            f"{self.currency}→{threshold.currency} exchange-rate "
            "observation is held for the day this figure was observed, and "
            "a rate is never assumed."
        )

    @classmethod
    def measured(
        cls,
        amount: float,
        *,
        warrant: TranslationWarrant,
        currency: str | None = None,
        currency_is_assumed: bool = True,
        identity: CrossProviderIdentity | None = None,
        translation: MonetaryTranslation | None = None,
    ) -> MarketCapMagnitude:
        return cls(
            amount=amount,
            warrant=warrant,
            currency=currency,
            currency_is_assumed=currency_is_assumed,
            identity=identity,
            translation=translation,
        )

    @classmethod
    def unmeasured(
        cls,
        absence: ClaimAbsence,
        *,
        warrant: TranslationWarrant,
        identity: CrossProviderIdentity | None = None,
    ) -> MarketCapMagnitude:
        return cls(amount=None, warrant=warrant, absence=absence, identity=identity)
