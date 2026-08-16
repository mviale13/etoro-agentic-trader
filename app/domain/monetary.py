"""Monetary values compare only when both sides say what they are in.

The boundary #142 established the need for. The platform held one
absolute monetary threshold — `LARGE_CAP_THRESHOLD = 10_000_000_000` —
whose denomination existed nowhere but in the author's head, and
compared undenominated provider magnitudes against it: Nestlé's
208bn *Swiss francs* against ten billion *of nothing in particular*.

The governing rule, now typed rather than assumed:

    Monetary values may be compared only when both sides have an
    explicit denomination. Different denominations require a
    separately authorised conversion. Absence of denomination is not
    permission to inherit one.

Two deliberate absences in this module:

- **No conversion.** A CHF magnitude against a USD threshold is
  *refused pending conversion*, not converted. FX translation is a
  distinct transformation with its own rate source, timestamp and
  warrant, and it belongs to its own future rule — hiding it inside a
  comparison would repeat the conflation this arc has been unwinding.
- **No inheritance.** A denomination is established by evidence or it
  is absent. The quote currency and the statement currency are
  measured facts about *other* quantities: BP.L quotes in pence,
  reports in dollars, and its market cap is in pounds — one instrument,
  three currencies, and any inheritance rule picks a wrong one.

What *can* establish a denomination is arithmetic. Where the
provider's own figures satisfy `market_cap = price × shares` exactly,
the market cap **is** that product, and a product inherits its unit
from its factors: the cap is denominated in whatever the price is
quoted in. That is a derivation, not an assumption — and where the
identity fails, nothing is established and the silence stands.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: How far the provider's own arithmetic may drift and still count as
#: the identity holding — rounding and intraday update lag between two
#: figures of one payload, exactly the timing allowance the crypto
#: gate's INTERNAL_TOLERANCE is. An order-of-magnitude error cannot
#: hide inside it.
IDENTITY_TOLERANCE = 0.005

#: Quote units that are minor units of a major currency, with the
#: factor between them. **A fact about the currency, not about any
#: provider**: one hundred pence are one pound by definition of
#: sterling. Consulted only when the direct identity fails and the
#: scaled one holds exactly — which is how BP.L's cap is established
#: as GBP from arithmetic rather than guessed from geography.
MINOR_UNITS: dict[str, tuple[str, int]] = {
    "GBp": ("GBP", 100),
}


@dataclass(frozen=True, slots=True)
class MonetaryAmount:
    """An amount that says what it is denominated in.

    The smallest representation that makes a monetary policy constant
    honest: an amount and an explicit currency, neither optional. A
    threshold built from this can never again mean "ten billion of
    whatever arrives".
    """

    amount: float
    currency: str

    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError(
                "a monetary amount must say what currency it is in; an "
                "unlabelled amount is the constant this type exists to "
                "make impossible"
            )

    @property
    def stated(self) -> str:
        """The amount as a surface prints it — currency first, visibly."""

        return f"{self.currency} {self.amount:,.0f}"

    def __repr__(self) -> str:  # pragma: no cover - repr shape
        return f"MonetaryAmount({self.stated})"


class DenominationBasis(StrEnum):
    """How a market-cap denomination came to be what it is — or is not.

    Four states, and the distinction between the last two is
    load-bearing: a reconciliation that *failed* is a structural fact
    about share classes or depositary receipts, not a currency doubt,
    and presenting it as `currency unknown` would send an ADR to the
    wrong boundary for repair.
    """

    #: The provider's own arithmetic holds: cap = price × shares in
    #: the quote unit, so the cap's denomination is the quote
    #: currency, by derivation.
    CORROBORATED = "corroborated"

    #: The arithmetic holds only at the minor-unit factor: the price
    #: ticks in a minor unit and the cap is stated in the major one.
    #: Established, in the major unit.
    MINOR_UNIT = "minor_unit"

    #: The arithmetic fails for structural reasons — dual share
    #: classes, depositary receipts. **Not a denomination doubt**; a
    #: different boundary owns it.
    UNRECONCILED = "unreconciled"

    #: The inputs to the check were not all present.
    INSUFFICIENT = "insufficient"

    @property
    def establishes(self) -> bool:
        return self in (DenominationBasis.CORROBORATED, DenominationBasis.MINOR_UNIT)


@dataclass(frozen=True, slots=True)
class MarketCapDenomination:
    """What a market cap is denominated in, and how that was decided."""

    #: The established currency, or None where nothing establishes one.
    currency: str | None

    basis: DenominationBasis

    #: The account, worded at establishment so every surface says the
    #: same thing.
    because: str

    def __post_init__(self) -> None:
        if self.basis.establishes and self.currency is None:
            raise ValueError("an establishing basis must name the currency")

        if not self.basis.establishes and self.currency is not None:
            raise ValueError(
                "a non-establishing basis cannot carry a currency; that "
                "would be an inherited denomination wearing a basis"
            )

    @property
    def established(self) -> bool:
        return self.currency is not None


def corroborate_denomination(
    market_cap: float | None,
    price: float | None,
    shares: tuple[float, ...],
    quote_currency: str | None,
) -> MarketCapDenomination:
    """Establish a market cap's denomination from arithmetic, or refuse.

    The only establishment rule this platform holds, from #142's
    measurement: where `cap = price × shares` within tolerance, the
    cap is the product of a price in the quote unit and a unitless
    count, so its denomination **is** the quote currency — derived,
    not inherited. Where the price ticks in a known minor unit and the
    identity holds at the minor-unit factor instead, the cap is in the
    major unit (BP.L: ratio exactly 0.010 → pounds).

    `shares` may carry more than one published count (shares
    outstanding, implied shares outstanding); the identity holding for
    any one of them is the corroboration, since each is the provider's
    own statement of the same quantity.

    Everything else refuses. A failed identity is UNRECONCILED — a
    structural fact, not a currency doubt — and missing inputs are
    INSUFFICIENT. **No suffix, geography or field inheritance appears
    anywhere in this function**, which is the property the BP.L
    regression pins.
    """

    counts = tuple(count for count in shares if count and count > 0)

    if not market_cap or not price or price <= 0 or not counts or not quote_currency:
        return MarketCapDenomination(
            currency=None,
            basis=DenominationBasis.INSUFFICIENT,
            because=(
                "The market cap's denomination is not established: the "
                "figures needed to corroborate it (price, share count, "
                "quote currency) were not all reported."
            ),
        )

    for count in counts:
        ratio = market_cap / (price * count)

        if abs(ratio - 1.0) <= IDENTITY_TOLERANCE:
            return MarketCapDenomination(
                currency=quote_currency,
                basis=DenominationBasis.CORROBORATED,
                because=(
                    f"The market cap equals price × shares in the listing's "
                    f"own quote unit, so it is denominated in "
                    f"{quote_currency} by arithmetic."
                ),
            )

    minor = MINOR_UNITS.get(quote_currency)

    if minor is not None:
        major, factor = minor

        for count in counts:
            ratio = market_cap / ((price / factor) * count)

            if abs(ratio - 1.0) <= IDENTITY_TOLERANCE:
                return MarketCapDenomination(
                    currency=major,
                    basis=DenominationBasis.MINOR_UNIT,
                    because=(
                        f"The price ticks in {quote_currency} and the market "
                        f"cap equals price × shares only at the "
                        f"{factor}-to-one minor-unit factor, so the cap is "
                        f"denominated in {major} by arithmetic."
                    ),
                )

    return MarketCapDenomination(
        currency=None,
        basis=DenominationBasis.UNRECONCILED,
        because=(
            "The market cap does not reconcile with price × shares for any "
            "published share count. That is a structural fact about the "
            "instrument (share classes, depositary receipts), not a "
            "currency doubt, and it is not repaired here."
        ),
    )
