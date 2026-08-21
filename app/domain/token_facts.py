"""What is known about a token's market facts, and how firmly.

A provider returning a value does not make that value an established
fact. Yahoo answered $8,105 for a token worth eighteen billion dollars —
apparently valid, materially wrong, and it stood as the token's
invalidation condition. Wrong-but-plausible evidence is more dangerous
than missing evidence, so a token market fact carries its *standing*:
what survived validation, what is merely claimed, what was rejected and
why, and what nobody reports.

These are evidence objects, not scores. Nothing here bands, weighs or
recommends, and no standing is an investment verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.evidence_standing import EvidenceStanding
from app.domain.provenance import Provenance

#: How far a token fact can be trusted.
#:
#: The platform's one standing vocabulary, shared with every other
#: evidence family since protocol fundamentals became the second —
#: "established" must mean the same thing about a market value and
#: about a protocol's fees. The name is kept as the token layer's own
#: so the contract frozen after PR #101 reads unchanged.
TokenFactStanding = EvidenceStanding


#: The facts this domain knows how to hold, in display order. A name
#: outside this set is a programming error, not a new kind of evidence.
TOKEN_FACTS = (
    "market_cap",
    "rank",
    "price_change_24h",
    "spot_volume_24h",
    "spot_volume_change_24h",
    "market_volume_24h",
    "circulating_supply",
    "total_supply",
    "max_supply",
    "fully_diluted_valuation",
    "price",
    "project_age",
)


@dataclass(frozen=True, slots=True)
class TokenFact:
    """One market fact about a token, with its standing and its account.

    `value` is served only where the standing allows one. `because` is
    the worded account of the standing — the corroboration that
    established it, the reason nothing could, or the reason it is
    absent — written here in the domain and carried verbatim.
    """

    fact: str
    standing: TokenFactStanding
    value: float | None = None
    source: str | None = None
    observed_at: datetime | None = None
    because: str | None = None

    #: Every source whose independent agreement established this value —
    #: the served claimant first, then the corroborators. Empty for any
    #: standing but ESTABLISHED, because nothing agreed.
    #:
    #: Carried structurally as well as worded into `because`: a layer
    #: that must name the claimants may not parse a sentence to find
    #: them, and a sentence is not a list.
    claimants: tuple[str, ...] = ()

    #: The versioned rule under which this standing was reached, so a
    #: figure travelling upward names what admitted it instead of
    #: arriving as a bare number. None where no rule admitted it.
    rule: str | None = None

    @property
    def established_value(self) -> float | None:
        """The value if established, and nothing otherwise.

        The consumption door for anything that computes: a claim, a
        conflict and an absence all read as None here, so no score can
        consume a figure that did not survive validation.
        """

        if self.standing is TokenFactStanding.ESTABLISHED:
            return self.value

        return None


@dataclass(frozen=True, slots=True)
class RejectedReading:
    """A claim that did not survive, retained rather than discarded.

    The trust ledger: an investor shown only the surviving figure
    cannot see that a source contradicted it, and a source that was
    wrong once is a fact about the source worth keeping.
    """

    fact: str

    #: What the fact is called to the investor.
    label: str

    #: The value exactly as the source stated it, already worded —
    #: "$8,105", "1,500,000,000", "2020-12-29".
    stated: str

    source: str
    observed_at: datetime | None
    because: str

    @property
    def statement(self) -> str:
        """The ledger line as a surface prints it, worded here once."""

        return (
            f"{self.source}'s {self.label.lower()} of {self.stated} "
            f"was not accepted: {self.because}"
        )


@dataclass(frozen=True, slots=True)
class TokenMarketFacts:
    """Every market fact held about one token, after validation.

    The one object a surface or an assembly consumes. Facts appear in
    `TOKEN_FACTS` order; the readings that did not survive are in
    `rejected`, with their reasons; and the flags below are the two
    deterministic consumption gates other layers need, computed here so
    they are rules of the evidence rather than habits of the callers.
    """

    symbol: str

    #: The native provider's own identifier for this token, as
    #: confirmed by the provider's answer. None where none was read.
    provider_id: str | None

    facts: tuple[TokenFact, ...]

    rejected: tuple[RejectedReading, ...]

    #: Whether Yahoo's own market-cap claim agreed with the established
    #: one. The volume gate: Yahoo's broader `volume_24h` keeps feeding
    #: the liquidity factor only where Yahoo's sibling market-cap claim
    #: was independently corroborated — a source shown wrong about this
    #: instrument does not keep its other claims' authority, and a
    #: source that claimed nothing checkable never earned it.
    yahoo_market_cap_corroborated: bool = False

    #: When the native provider was read. None where it never was.
    read: Provenance | None = None

    def fact(self, name: str) -> TokenFact | None:
        """One fact by name, or None for a name this domain never holds."""

        for fact in self.facts:
            if fact.fact == name:
                return fact

        return None

    def established_value(self, name: str) -> float | None:
        """The established value of one fact, and nothing otherwise."""

        fact = self.fact(name)

        return fact.established_value if fact is not None else None

    @property
    def issued_share(self) -> float | None:
        """Circulating over maximum supply — this platform's arithmetic.

        Computed from two established inputs or not at all: a share of
        a claim would be a claim wearing arithmetic's authority.
        """

        circulating = self.established_value("circulating_supply")
        cap = self.established_value("max_supply")

        if circulating is None or cap is None or cap <= 0:
            return None

        return circulating / cap

    @property
    def fdv_to_market_cap(self) -> float | None:
        """Fully diluted valuation over market value — dilution context.

        The same rule: established inputs or nothing.
        """

        diluted = self.established_value("fully_diluted_valuation")
        market = self.established_value("market_cap")

        if diluted is None or market is None or market <= 0:
            return None

        return diluted / market
