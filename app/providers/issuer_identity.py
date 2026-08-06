"""Who a symbol is, before anything is read on its behalf.

Reading a primary source has two independent failure modes. Grounding
proves that facts belong to a document; it cannot prove that the document
belongs to the security. A perfectly grounded, exactly cited reading of a
genuine annual report is still wrong if the report is someone else's, and
nothing downstream can see that it happened.

This module is the second boundary, for the European path. It turns a
symbol into the filer identity a European register can be asked about,
and it refuses rather than approximates: the symbol must be in the
reviewed list, GLEIF must return exactly one company for its ISIN, and
that company must still be the one the list was verified against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.providers.european_issuers import EUROPEAN_ISSUERS, RegisteredIssuer

#: GLEIF maintains the ISIN-to-LEI mapping under a mandate from the
#: Financial Stability Board. It is the authority for "which legal entity
#: issued this security", which is precisely the question a ticker cannot
#: answer.
LEI_RECORDS_URL = "https://api.gleif.org/api/v1/lei-records"

_NOISE = re.compile(r"[^a-z0-9]+")


class IssuerUnknown(Exception):
    """No identity could be established for this symbol, and it says why.

    A gap. This platform has not established who the security belongs to,
    which is a fact about the platform's coverage and is reported as one.
    """


class IssuerRegistryError(IssuerUnknown):
    """The register could not be reached, or answered something unusable.

    A different situation from a gap, and a subclass so a caller that does
    not care still catches both. "This symbol is not on the reviewed list"
    is settled; "GLEIF timed out" is not, and only one of them is worth
    asking about again.
    """


@dataclass(frozen=True, slots=True)
class IssuerIdentity:
    """A security, and the legal entity that issued it."""

    symbol: str

    isin: str

    #: The Legal Entity Identifier. Global, unambiguous, and the key every
    #: European filing register indexes filers by.
    lei: str

    #: The entity's legal name, as GLEIF states it.
    legal_name: str


def _normalised(name: str) -> str:
    """A name reduced to the characters that distinguish one from another."""

    return _NOISE.sub("", name.casefold())


class IssuerIdentityRegistry:
    """
    Establish which company a symbol means, or refuse to.

    Memoised for the life of the instance, because an issuer's LEI does
    not change between two lookups in one run and the identity is asked
    for twice — once to find the current document, once to check that the
    document fetched is the one that was found.
    """

    def __init__(
        self,
        issuers: dict[str, RegisteredIssuer] | None = None,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._issuers = dict(EUROPEAN_ISSUERS if issuers is None else issuers)
        self._client = client
        self._timeout = timeout
        self._known: dict[str, IssuerIdentity] = {}

    def of(self, symbol: str) -> IssuerIdentity:
        """The legal entity behind this symbol, from the bodies that say so."""

        ticker = symbol.upper().strip()

        if ticker in self._known:
            return self._known[ticker]

        issuer = self._issuers.get(ticker)

        if issuer is None:
            raise IssuerUnknown(
                f"{ticker} is not on this platform's list of European "
                "issuers, so no company was identified for it. A ticker is "
                "not an identity, and one is never guessed at."
            )

        identity = self._identified(issuer)

        self._known[ticker] = identity

        return identity

    def _identified(self, issuer: RegisteredIssuer) -> IssuerIdentity:
        records = self._records(issuer)

        if len(records) != 1:
            # Zero is a security GLEIF holds no issuer for. More than one
            # is an ambiguity, and picking from an ambiguity is how a
            # reading ends up describing the wrong company.
            raise IssuerUnknown(
                f"GLEIF returned {len(records)} companies for {issuer.symbol}'s "
                f"ISIN ({issuer.isin}), so its issuer is not established."
            )

        entity = records[0].get("attributes", {})
        lei = str(entity.get("lei") or "").strip()
        legal_name = str(
            (entity.get("entity") or {}).get("legalName", {}).get("name") or ""
        ).strip()

        if not lei or not legal_name:
            raise IssuerRegistryError(
                f"GLEIF's record for {issuer.symbol} named no company, so its "
                "issuer is not established."
            )

        # The check the reviewed list exists to make possible. An ISIN
        # mistyped into another real company's resolves perfectly well;
        # what it cannot do is come back with the name that was verified.
        expected = _normalised(issuer.legal_name)
        stated = _normalised(legal_name)

        if expected not in stated and stated not in expected:
            raise IssuerUnknown(
                f"{issuer.symbol}'s ISIN ({issuer.isin}) now resolves to "
                f"{legal_name!r}, and it was recorded against "
                f"{issuer.legal_name!r}. The identity is refused until the "
                "entry is verified again."
            )

        return IssuerIdentity(
            symbol=issuer.symbol,
            isin=issuer.isin,
            lei=lei,
            legal_name=legal_name,
        )

    def _records(self, issuer: RegisteredIssuer) -> list[dict[str, Any]]:
        params = {"filter[isin]": issuer.isin}

        try:
            if self._client is not None:
                response = self._client.get(LEI_RECORDS_URL, params=params)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.get(
                        LEI_RECORDS_URL,
                        params=params,
                        follow_redirects=True,
                    )

            response.raise_for_status()

            payload = response.json()
        except Exception as error:
            raise IssuerRegistryError(
                f"GLEIF could not be reached, so {issuer.symbol}'s issuer was "
                "not identified."
            ) from error

        data = payload.get("data") if isinstance(payload, dict) else None

        if not isinstance(data, list):
            raise IssuerRegistryError(
                f"GLEIF returned no record list for {issuer.symbol}, so its "
                "issuer was not identified."
            )

        return [record for record in data if isinstance(record, dict)]
