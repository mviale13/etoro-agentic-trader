"""What one acquisition cycle read, and what it could not."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exchange_rate import ExchangeRate


@dataclass(frozen=True, slots=True)
class AcquiredSecurity:
    """One security the cycle asked about, and what came back for it.

    The three readings are kept apart because they fail apart and because
    a surface reads them apart: a company can carry a price and no
    fundamentals, and the dossier that results is thin in a way the
    investor can see. Recording only "acquired" would report the same
    word for both.
    """

    symbol: str

    #: The store now holds a price for it.
    priced: bool

    #: The store now holds the fundamentals every ratio is read off.
    fundamentals: bool

    #: The store now holds the published earnings window. `None` where the
    #: question does not apply: a fund and a token have no earnings call,
    #: and they were never asked, which is not the same as being asked and
    #: not knowing.
    calendar: bool | None

    #: The store now holds a third party's published rating. `None`
    #: where the question does not apply — only a token is rated, and
    #: the rating is context the platform shows, never evidence it uses.
    rating: bool | None = None

    #: The store now holds the crypto-native provider's market claims —
    #: the raw material the validation gate judges on read. `None` where
    #: the question does not apply: only a token has them.
    token_facts: bool | None = None

    #: The store now holds the economics of the systems behind this
    #: token. `None` where no economic system is mapped to it — an
    #: unmapped security is not one whose economics came back empty.
    protocol_facts: bool | None = None

    #: The store now holds the chain's own supply quantities. `None`
    #: where this platform has verified no canonical surface for the
    #: chain — which is different from a chain that answered nothing.
    primary_supply: bool | None = None

    #: Whether the store now holds fund flows and disclosed holdings for
    #: this asset. None where no fund group exists — which is the honest
    #: answer for a token with no ETF, and different from a failed read.
    capital_flows: bool | None = None

    #: Whether the store now holds this asset's recent developments.
    #: `None` where no event surface is mapped to it: an asset nobody
    #: publishes a timeline for was never asked, which is not the same
    #: as one that was asked and answered nothing.
    events: bool | None = None

    #: Why the quote vendor's own listing was not read as this security,
    #: where it was not. Empty where it was, and for everything that is
    #: not a cryptocurrency — an equity is quoted under its own ticker
    #: and this question does not arise for it.
    #:
    #: Kept apart from `priced`, because they are different facts and
    #: this slice exists because they were being reported as one. A
    #: refused listing costs the vendor's price *history*; the price
    #: itself comes from the crypto-native pool and is unaffected by it.
    listing_refused: str = ""

    @property
    def complete(self) -> bool:
        """True when everything this security was asked for came back."""

        return self.priced and self.fundamentals and self.calendar is not False


@dataclass(frozen=True, slots=True)
class MarketCycle:
    """What one reading of the crypto environment cost and returned.

    Reported so the operator can see the rate limit being spent. The
    market half of a cycle is a fixed, deterministic number of calls —
    the environment, the categories, the corpus's returns, one breadth
    page, and one page per peer group in use — and a batch that lost
    calls to a rate limit says so rather than looking complete.
    """

    #: How many provider calls the cycle intended to make.
    asked: int

    #: How many pieces of the cycle came back with something in them.
    answered: int

    #: The peer groups read, by the provider's own category identifier.
    peer_groups: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return self.answered == self.asked


@dataclass(frozen=True, slots=True)
class MarketAcquisition:
    """One explicit reading of the market, for the pages that follow it.

    A cycle, not a page view. Every surface on this platform serves what
    is in the store and stops; this is the act that fills it, taken
    deliberately by an operator or a schedule, exactly as `observe` is
    the act that reads a filing.
    """

    securities: tuple[AcquiredSecurity, ...]

    #: The instruments the market strip is made of, as far as they priced.
    instruments: tuple[str, ...]

    vix: float | None

    #: The currency rate the account's euro figures are converted at.
    #: Absent where none could be read, and the figures are absent with it.
    rate: ExchangeRate | None = None

    #: The foreign→USD rates read for the monetary translation
    #: boundary (fx-translation@1) — one per measured foreign
    #: denomination, each absent where it could not be read. Read in
    #: the same cycle as the fundamentals they translate, which is what
    #: gives a (cap, rate) pair the shared observation day the temporal
    #: rule requires.
    translation_rates: tuple[ExchangeRate, ...] = ()

    #: How many provider calls the crypto market cycle made, and how
    #: many answered. A cycle-level reading rather than a per-security
    #: one: the environment is the same for every token, so it is read
    #: once and the count belongs here rather than beside a symbol.
    #: None where no market cycle was attempted.
    crypto_market: MarketCycle | None = None

    @property
    def priced(self) -> tuple[AcquiredSecurity, ...]:
        return tuple(security for security in self.securities if security.priced)

    @property
    def unpriced(self) -> tuple[AcquiredSecurity, ...]:
        """
        Asked for, and no price came back.

        Named rather than counted, because each one is a security whose
        dossier will now say it has no price — and the operator running
        the cycle is the only person who can do anything about it.
        """

        return tuple(security for security in self.securities if not security.priced)

    @property
    def refused_listings(self) -> tuple[AcquiredSecurity, ...]:
        """
        Asked for, and the vendor answered about a different security.

        A separate list from `unpriced` because it is a separate fact,
        and the two were being reported as one sentence. HYPE and TAO
        appear here and not there: each has an established crypto-native
        price, and neither has a vendor price history that is its own.
        """

        return tuple(
            security for security in self.securities if security.listing_refused
        )
