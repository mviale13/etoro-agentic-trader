"""Whether two providers are describing the same economic instrument.

The audit's strongest finding, and the one that replaced its own
premise. MOVRvest joins eToro's instrument to Yahoo's ticker by
passing the broker's symbol through untranslated, then stamps the
broker's display name onto the vendor's numbers — so a ticker
collision is unobservable from the output. Measured live: eToro's
instrument 15618 is named *"Space Exploration Technologies Corp"*
while the ticker `SPCX` has historically denoted an exchange-traded
fund at Yahoo, and the platform holds nothing that decides which
instrument its stored numbers describe.

Invariant 2 already says identity is enforced *before* the reading,
and says it was learned twice — `BTC` resolving against the SEC to a
bitcoin trust, a ticker-to-ISIN lookup returning an Argentine CEDEAR.
This module is that invariant given a type on the equity path.

**A symbol alone is never identity.** Symbols are venue-local, reused
across venues and reassigned over time; two providers agreeing on a
string have agreed about a string. That rule is enforced in
`join_identity` rather than documented beside it, because the join is
the exact place where the temptation is strongest and the failure is
invisible.

This is deliberately **not** a security master. It invents no
canonical identifier and resolves nothing: it records what each
provider claims, states what the evidence supports, and stops. A
conflict is a finding to be shown, not a problem to be settled by
whichever source the code happens to read first.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.domain.provider_translations import YAHOO

#: Words that appear in an instrument's name to say what *kind* of
#: instrument it is. Compared only between two providers' names for
#: the same symbol — never used to classify an instrument, which would
#: be exactly the provider-taxonomy-as-ontology error one layer down.
_INSTRUMENT_FORMS = (
    "etf",
    "etn",
    "etc",
    "ucits",
    "fund",
    "trust",
    "adr",
    "sicav",
)


class IdentityEvidence(StrEnum):
    """What a provider offers towards saying which instrument this is.

    Ordered by nothing. Each kind answers a different question and
    they are not substitutes: an ISIN identifies a security, a symbol
    identifies a listing's local name, a taxonomy token describes what
    the provider thinks the instrument is.
    """

    #: A global instrument identifier — the only evidence here that
    #: identifies a security rather than describing one.
    ISIN = "isin"

    #: An entity identifier: LEI, FIGI. Identifies the issuer or the
    #: instrument depending on the scheme.
    ENTITY_IDENTIFIER = "entity_identifier"

    #: The provider's own internal instrument id. Unique inside that
    #: provider and meaningless outside it.
    PROVIDER_INSTRUMENT_ID = "provider_instrument_id"

    #: The ticker as the provider spells it.
    SYMBOL = "symbol"

    #: The venue the instrument trades at.
    EXCHANGE = "exchange"

    #: The provider's display name for the instrument.
    NAME = "name"

    #: The provider's category token — an asset type id, a quote type.
    TAXONOMY = "taxonomy"

    @property
    def identifies_alone(self) -> bool:
        """Whether this evidence can establish identity by itself.

        Only a global identifier can. Everything else describes or
        names, and the difference is what a cross-provider join is
        forbidden from blurring.
        """

        return self is IdentityEvidence.ISIN


class IdentityStanding(StrEnum):
    """How far a cross-provider join is supported by evidence.

    A separate vocabulary from `EvidenceStanding`, and the reason is
    precise rather than stylistic. `EvidenceStanding` grades how far a
    *provider's claim about a value* can be trusted, and its CLAIMED
    member means "a source reports it and we cannot check it". Here
    the weakest state is different in kind: **no source claims the
    join at all.** Neither eToro nor Yahoo asserts that eToro 15618
    is Yahoo `SPCX` — MOVRvest assumed it by writing one symbol into
    both requests. A vocabulary whose weakest member says "a source
    reports it" cannot express an assumption nobody made.
    """

    #: A global identifier is shared, or an equivalent proof exists.
    #: Nothing on the equity path reaches this today.
    ESTABLISHED = "established"

    #: Independent evidence agrees — name, exchange and taxonomy line
    #: up across providers — without a shared global identifier.
    CORROBORATED = "corroborated"

    #: The join rests on symbol equality and nothing else. The live
    #: state of every security on this platform.
    ASSUMED = "assumed"

    #: Evidence the providers do supply disagrees. The join is not
    #: refuted and it is certainly not established: it is unresolved,
    #: and both accounts are retained.
    UNRESOLVED = "unresolved"

    @property
    def stated(self) -> str:
        return _STANDING_LABELS[self]

    @property
    def establishes_identity(self) -> bool:
        """Whether downstream may treat the two records as one instrument."""

        return self in (IdentityStanding.ESTABLISHED, IdentityStanding.CORROBORATED)


_STANDING_LABELS = {
    IdentityStanding.ESTABLISHED: "Established",
    IdentityStanding.CORROBORATED: "Corroborated",
    IdentityStanding.ASSUMED: "Assumed",
    IdentityStanding.UNRESOLVED: "Sources disagree",
}


@dataclass(frozen=True, slots=True)
class ProviderIdentityClaim:
    """What one provider says the instrument behind a symbol is.

    Every field except the provider and the symbol is optional,
    because most of them are genuinely absent on this path — eToro
    publishes no ISIN, Yahoo publishes no broker instrument id — and
    an absent field must stay absent rather than being filled with
    the one identifier we happen to hold.
    """

    provider: str

    #: The symbol as this provider spells it.
    symbol: str

    #: The provider's own instrument id, where it has one.
    instrument_id: str | None = None

    #: The provider's display name for the instrument.
    name: str | None = None

    #: The provider's category token, exactly as it arrives —
    #: "5", "EQUITY", "ETF". Never translated here.
    taxonomy: str | None = None

    exchange: str | None = None

    isin: str | None = None

    entity_identifier: str | None = None

    @property
    def evidence(self) -> tuple[IdentityEvidence, ...]:
        """Which kinds of identity evidence this claim actually carries."""

        held = [IdentityEvidence.SYMBOL]

        if self.isin:
            held.append(IdentityEvidence.ISIN)

        if self.entity_identifier:
            held.append(IdentityEvidence.ENTITY_IDENTIFIER)

        if self.instrument_id:
            held.append(IdentityEvidence.PROVIDER_INSTRUMENT_ID)

        if self.exchange:
            held.append(IdentityEvidence.EXCHANGE)

        if self.name:
            held.append(IdentityEvidence.NAME)

        if self.taxonomy:
            held.append(IdentityEvidence.TAXONOMY)

        return tuple(held)

    @property
    def stated(self) -> str:
        """This provider's account, in its own terms."""

        described = self.name or self.instrument_id or "an unnamed instrument"

        return f"{self.provider} says {self.symbol} describes {described}."


@dataclass(frozen=True, slots=True)
class CrossProviderIdentity:
    """Two providers' accounts of one symbol, and what they support.

    Holds both claims whatever the standing. A conflict resolved by
    dropping one account would leave the surface unable to show the
    investor that anything was ever in question.
    """

    symbol: str
    claims: tuple[ProviderIdentityClaim, ...]
    standing: IdentityStanding

    #: Why the standing is what it is, in this platform's own words.
    because: str

    @property
    def establishes_identity(self) -> bool:
        return self.standing.establishes_identity

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(claim.provider for claim in self.claims)

    @property
    def accounts(self) -> tuple[str, ...]:
        """Each provider's account, retained side by side."""

        return tuple(claim.stated for claim in self.claims)

    @property
    def stated(self) -> str:
        return (
            f"{self.symbol}: identity is {self.standing.stated.lower()} "
            f"— {self.because}"
        )


def vendor_claim(symbol: str, info: dict[str, Any]) -> ProviderIdentityClaim:
    """The data vendor's account of a symbol, read from its own payload.

    Yahoo's `quoteType` ("EQUITY", "ETF") is the vendor's own category
    token and is carried raw, exactly as the broker's numeric id is: it
    is evidence about what the vendor thinks, which is what a
    cross-provider check needs and what must never become a domain
    classification on the way through.

    Lives in the domain rather than the identity service because two
    layers now build it — the service, for an ad-hoc question, and
    acquisition, which stores the claim beside the fundamentals it
    arrived with so the join can be asked of a stored record. One
    concept, one implementation.
    """

    def text(key: str) -> str | None:
        value = info.get(key)

        return value.strip() if isinstance(value, str) and value.strip() else None

    return ProviderIdentityClaim(
        provider=YAHOO,
        symbol=text("symbol") or symbol,
        name=text("longName") or text("shortName"),
        taxonomy=text("quoteType"),
        exchange=text("exchange"),
        isin=None,
    )


def _forms(name: str | None) -> frozenset[str]:
    """Which instrument-form words a provider's name carries."""

    if not name:
        return frozenset()

    lowered = name.casefold()

    return frozenset(form for form in _INSTRUMENT_FORMS if form in lowered)


def join_identity(
    symbol: str,
    claims: tuple[ProviderIdentityClaim, ...],
) -> CrossProviderIdentity:
    """State what the held evidence supports about a cross-provider join.

    Deterministic, and it resolves nothing. The ladder:

    - a shared global identifier establishes identity;
    - independent agreement on instrument *form* corroborates it;
    - disagreement about form leaves it unresolved, both accounts kept;
    - symbol equality alone leaves it assumed, which is the honest
      description of every join this platform performs today.
    """

    if len(claims) < 2:
        return CrossProviderIdentity(
            symbol=symbol,
            claims=claims,
            standing=IdentityStanding.ASSUMED,
            because=(
                "only one provider describes this symbol, so nothing cross-checks it"
            ),
        )

    isins = {claim.isin for claim in claims if claim.isin}

    if len(isins) > 1:
        return CrossProviderIdentity(
            symbol=symbol,
            claims=claims,
            standing=IdentityStanding.UNRESOLVED,
            because=(
                "the providers carry different global identifiers for this "
                "symbol, so they are describing different securities"
            ),
        )

    if len(isins) == 1 and all(claim.isin for claim in claims):
        return CrossProviderIdentity(
            symbol=symbol,
            claims=claims,
            standing=IdentityStanding.ESTABLISHED,
            because=(
                f"every provider carries the same global identifier "
                f"({next(iter(isins))})"
            ),
        )

    forms = [_forms(claim.name) for claim in claims if claim.name]

    stated_forms = [form for form in forms if form]

    if len(stated_forms) >= 2:
        if any(form != stated_forms[0] for form in stated_forms[1:]):
            return CrossProviderIdentity(
                symbol=symbol,
                claims=claims,
                standing=IdentityStanding.UNRESOLVED,
                because=(
                    "the providers' own names describe different kinds of "
                    "instrument, and nothing held decides which this is"
                ),
            )

        return CrossProviderIdentity(
            symbol=symbol,
            claims=claims,
            standing=IdentityStanding.CORROBORATED,
            because=(
                "the providers' own names agree on what kind of instrument "
                "this is, though no global identifier confirms it"
            ),
        )

    # One provider names a form the other does not mention. That is not
    # agreement and it is not a contradiction: silence is not assent,
    # and reading it either way is how SPCX became a company.
    if len(stated_forms) == 1:
        return CrossProviderIdentity(
            symbol=symbol,
            claims=claims,
            standing=IdentityStanding.UNRESOLVED,
            because=(
                "one provider's name states what kind of instrument this is "
                "and the other's does not mention it, so the accounts "
                "cannot be checked against each other"
            ),
        )

    return CrossProviderIdentity(
        symbol=symbol,
        claims=claims,
        standing=IdentityStanding.ASSUMED,
        because=(
            "the join rests on symbol equality alone, and a shared symbol "
            "is not evidence that two providers describe one instrument"
        ),
    )
