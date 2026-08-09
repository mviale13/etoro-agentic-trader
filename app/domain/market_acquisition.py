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

    @property
    def complete(self) -> bool:
        """True when everything this security was asked for came back."""

        return self.priced and self.fundamentals and self.calendar is not False


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
