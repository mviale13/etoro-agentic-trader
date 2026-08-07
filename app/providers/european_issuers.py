"""Which company a European ticker means, established rather than guessed.

A ticker is not an identity. `SAN` is Sanofi in Paris and Banco Santander
in Madrid; `BNP.PA` is a convention this platform inherited from a price
feed, and no European register indexes anything by it. The chain that
ends at a filing starts here, and every link in it has to be an authority
rather than a resemblance:

```text
symbol  →  ISIN        →  LEI          →  the filing
          (this file)     (GLEIF)         (filings.xbrl.org)
```

Only the first link is written down, because only the first link has no
authority to ask. The ISIN of a security is a fact a reader can check
against the exchange that lists it in about ten seconds, which is what
makes an entry here reviewable. Everything after it is looked up live
from the body that maintains it.

The temptation this file exists to refuse is deriving the ISIN
automatically. It was tried: `yfinance` will answer `Ticker("ASML.AS").isin`
with `AR0725224551` — an Argentine CEDEAR that tracks ASML, not ASML — and
`BNP.PA` with nothing at all. A wrong ISIN resolves to a real company that
files real reports, and the knowledge read from them is grounded, cited
and about the wrong business. That failure is invisible downstream, which
is exactly why the mapping is a reviewed list and not an inference.

Coverage is therefore small and honest: a security absent from this list
is reported as one this platform has not established an identity for. It
is never a reason to guess at one.

Every entry below was verified by looking the ISIN up at GLEIF and
recording the legal name GLEIF returned. `IssuerIdentityRegistry` checks
that name again at run time, so an entry whose ISIN was mistyped into
another company's cannot quietly start resolving to it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegisteredIssuer:
    """One security, and the company behind it as an authority named it."""

    #: The symbol as this platform names the security.
    symbol: str

    #: The security's ISIN, checkable against the exchange that lists it.
    isin: str

    #: The legal name GLEIF returned for this ISIN when the entry was
    #: added. Not decoration: it is checked again on every lookup, so a
    #: mistyped ISIN that lands on another company is refused rather than
    #: followed. A genuine renaming fails the check too, which is the
    #: right outcome — it means the entry needs verifying again.
    legal_name: str


#: Verified 2026-08-06, each ISIN against GLEIF's ISIN-to-LEI mapping.
#:
#: The German issuers resolve to real companies and to no ESEF filing:
#: Germany's officially appointed mechanism does not publish to
#: filings.xbrl.org, so `EsefFilings` reports them as an indexed gap
#: rather than an unknown company. They are kept here because that is a
#: more useful answer than "never heard of it", and because the day the
#: index gains them nothing needs adding.
_ISSUERS: tuple[RegisteredIssuer, ...] = (
    # France
    RegisteredIssuer("BNP.PA", "FR0000131104", "BNP PARIBAS"),
    RegisteredIssuer("MC.PA", "FR0000121014", "LVMH MOET HENNESSY LOUIS VUITTON"),
    RegisteredIssuer("OR.PA", "FR0000120321", "L'OREAL"),
    RegisteredIssuer("SAN.PA", "FR0000120578", "SANOFI"),
    RegisteredIssuer("TTE.PA", "FR0000120271", "TotalEnergies SE"),
    RegisteredIssuer("SU.PA", "FR0000121972", "SCHNEIDER ELECTRIC SE"),
    RegisteredIssuer(
        "AI.PA",
        "FR0000120073",
        "L'AIR LIQUIDE SOCIETE ANONYME POUR L'ETUDE ET L'EXPLOITATION DES "
        "PROCEDES GEORGES CLAUDE",
    ),
    RegisteredIssuer("RMS.PA", "FR0000052292", "HERMES INTERNATIONAL"),
    RegisteredIssuer("CS.PA", "FR0000120628", "AXA"),
    RegisteredIssuer("DG.PA", "FR0000125486", "VINCI"),
    RegisteredIssuer("SAF.PA", "FR0000073272", "SAFRAN"),
    RegisteredIssuer("EL.PA", "FR0000121667", "ESSILORLUXOTTICA"),
    # Netherlands. Airbus and Stellantis are listed in Paris and Milan and
    # incorporated in the Netherlands, which is why their ISINs are Dutch.
    RegisteredIssuer("ASML.AS", "NL0010273215", "ASML Holding N.V."),
    RegisteredIssuer("AIR.PA", "NL0000235190", "AIRBUS SE"),
    RegisteredIssuer("INGA.AS", "NL0011821202", "ING GROEP N.V."),
    RegisteredIssuer("AD.AS", "NL0011794037", "Koninklijke Ahold Delhaize N.V."),
    RegisteredIssuer("PHIA.AS", "NL0000009538", "Koninklijke Philips N.V."),
    RegisteredIssuer("HEIA.AS", "NL0000009165", "Heineken N.V."),
    RegisteredIssuer("RACE.MI", "NL0011585146", "FERRARI N.V."),
    RegisteredIssuer("STLAM.MI", "NL00150001Q9", "STELLANTIS N.V."),
    # Italy
    RegisteredIssuer("ISP.MI", "IT0000072618", "INTESA SANPAOLO SPA"),
    RegisteredIssuer("ENI.MI", "IT0003132476", "ENI S.P.A."),
    RegisteredIssuer("ENEL.MI", "IT0003128367", "ENEL - SPA"),
    RegisteredIssuer("UCG.MI", "IT0005239360", "UNICREDIT, SOCIETA' PER AZIONI"),
    # Spain
    RegisteredIssuer("SAN.MC", "ES0113900J37", "BANCO SANTANDER S.A."),
    RegisteredIssuer("IBE.MC", "ES0144580Y14", "IBERDROLA SA"),
    RegisteredIssuer("ITX.MC", "ES0148396007", "INDUSTRIA DE DISEÑO TEXTIL, S.A."),
    RegisteredIssuer(
        "BBVA.MC",
        "ES0113211835",
        "BANCO BILBAO VIZCAYA ARGENTARIA SOCIEDAD ANONIMA",
    ),
    # Belgium. Verified 2026-08-07: GLEIF returns UMICORE for the ISIN,
    # and Euronext lists that ISIN as Umicore's Brussels equity.
    RegisteredIssuer("UMI.BR", "BE0974320526", "UMICORE"),
    # Nordics
    RegisteredIssuer("NOVO-B.CO", "DK0062498333", "NOVO NORDISK A/S"),
    RegisteredIssuer("VOLV-B.ST", "SE0000115446", "Aktiebolaget Volvo"),
    RegisteredIssuer("EQNR.OL", "NO0010096985", "EQUINOR ASA"),
    # Germany — identified, and not indexed. See the note above.
    RegisteredIssuer("SAP.DE", "DE0007164600", "SAP SE"),
    RegisteredIssuer("SIE.DE", "DE0007236101", "Siemens Aktiengesellschaft"),
    RegisteredIssuer("ALV.DE", "DE0008404005", "Allianz SE"),
    RegisteredIssuer("BAS.DE", "DE000BASF111", "BASF SE"),
    RegisteredIssuer(
        "BMW.DE",
        "DE0005190003",
        "Bayerische Motoren Werke Aktiengesellschaft",
    ),
    RegisteredIssuer("MBG.DE", "DE0007100000", "Mercedes-Benz Group AG"),
    RegisteredIssuer("DTE.DE", "DE0005557508", "DEUTSCHE TELEKOM AG"),
    RegisteredIssuer(
        "MUV2.DE",
        "DE0008430026",
        "Münchener Rückversicherungs-Gesellschaft Aktiengesellschaft in München",
    ),
    RegisteredIssuer("ADS.DE", "DE000A1EWWW0", "adidas AG"),
    RegisteredIssuer("IFX.DE", "DE0006231004", "Infineon Technologies AG"),
    RegisteredIssuer("DBK.DE", "DE0005140008", "DEUTSCHE BANK AKTIENGESELLSCHAFT"),
    RegisteredIssuer("VOW3.DE", "DE0007664039", "VOLKSWAGEN AKTIENGESELLSCHAFT"),
)


EUROPEAN_ISSUERS: Mapping[str, RegisteredIssuer] = {
    issuer.symbol: issuer for issuer in _ISSUERS
}
