"""What kind of investment case a dossier is, and what belongs on it.

One dossier page serves every security, and until now it was a company
dossier that crypto happened to flow through: a token's network readings
sat under "Business quality", the playbook card was headed "Company
type", and the filings section reported "No filing has been read" about
a subject that publishes none — an absence of work where the truth is an
absence of the thing itself.

This is the asset-specific dossier definition beneath the shared shell.
It decides *semantics only*: what the case is titled, what the
classification heading is, what each score is called, and whether
filing-grade understanding applies to the subject at all. It selects no
analyst (the playbook does), computes no score, and holds no threshold.
The surface renders what it declares and infers nothing — which is what
keeps "one is a business, one is a network" a fact the backend states
rather than a guess two frontends could make differently.

Keyed on `AssetClass` — the identity-level fact ("what kind of thing a
security is") rather than the playbook ("how it should be read"),
because a dossier's kind must exist even for a security nothing has
been gathered about.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from app.domain.asset_class import AssetClass
from app.domain.score_basis import score_labels_for


class DossierKind(StrEnum):
    """The kind of investment case a dossier presents.

    Coarser than `AssetClass` on purpose: it names the *frameworks this
    platform has*, not the kinds of asset that exist. A fund dossier is
    a named future specialization — until it is built, an ETF is served
    the general case rather than a company case wearing its name.
    """

    EQUITY = "equity"
    CRYPTO = "crypto"

    #: The unspecialised case: served with the company framework, and
    #: titled without claiming the subject is a business. ETFs and
    #: unclassified securities live here until their own dossier kind
    #: is earned.
    GENERAL = "general"


@dataclass(frozen=True, slots=True)
class DossierDefinition:
    """The semantics one dossier carries, worded once, backend-side.

    Every field is presentation the domain owns. None of them reaches a
    score, a playbook or a decision: two securities with different
    definitions and identical evidence decide identically.
    """

    kind: DossierKind

    #: What the case is called at the top of the page.
    title: str

    #: The heading over the classification card: a company has a company
    #: type, a token has an asset type, and an unclassified security is
    #: not silently promoted to either.
    classification_heading: str

    #: What each of the five scores is called on this dossier. The names
    #: come from `score_basis`, which is the one place scores are named.
    score_labels: Mapping[str, str]

    #: Whether filing-grade understanding applies to this subject. False
    #: only where the subject *publishes no filings* — a property of the
    #: asset class, not a gap in acquisition — and then the reason says
    #: so in those terms.
    filings_apply: bool
    filings_inapplicable_because: str | None = None


def _no_filings_because(asset_class: AssetClass) -> str:
    """Why the filings sections do not belong on this dossier.

    Worded as a property of the asset class. The acquisition-shaped
    absence ("no filing has been read — reading one is an explicit
    spend") is the honest sentence for a company; printed under a token
    it promises work nobody can do.
    """

    return (
        f"A {asset_class.noun} publishes no filings and no financial "
        "statements, so there is nothing of that kind to read. This is "
        "a property of the asset class, not missing evidence."
    )


_EQUITY = DossierDefinition(
    kind=DossierKind.EQUITY,
    title="Equity dossier",
    classification_heading="Company type",
    score_labels=MappingProxyType(score_labels_for(AssetClass.STOCK)),
    filings_apply=True,
)

_CRYPTO = DossierDefinition(
    kind=DossierKind.CRYPTO,
    title="Crypto dossier",
    classification_heading="Asset type",
    score_labels=MappingProxyType(score_labels_for(AssetClass.CRYPTO)),
    filings_apply=False,
    filings_inapplicable_because=_no_filings_because(AssetClass.CRYPTO),
)

#: A commodity is not a crypto dossier, and it is not a company either:
#: it shares the crypto case's one structural fact — no filings exist —
#: and nothing else. It stays on the general framework until a commodity
#: dossier is earned, with the filings sections honestly absent.
_COMMODITY = DossierDefinition(
    kind=DossierKind.GENERAL,
    title="Investment dossier",
    classification_heading="Asset type",
    score_labels=MappingProxyType(score_labels_for(AssetClass.COMMODITY)),
    filings_apply=False,
    filings_inapplicable_because=_no_filings_because(AssetClass.COMMODITY),
)

#: A fund is not a company case either, and its filings absence is a
#: different fact from a token's: this platform does not claim a fund
#: publishes nothing — its readers ask company questions of company
#: filings, and the fund playbook does not ask those questions. The
#: limit is this platform's, and it is worded as this platform's.
#: Still `GENERAL`: a fund dossier is a named future specialization,
#: and until one is earned an ETF is served the general case rather
#: than a company case wearing its name.
_FUND = DossierDefinition(
    kind=DossierKind.GENERAL,
    title="Investment dossier",
    classification_heading="Investment type",
    score_labels=MappingProxyType(score_labels_for(AssetClass.ETF)),
    filings_apply=False,
    filings_inapplicable_because=(
        "Company filing knowledge is not part of the fund playbook: a "
        "fund holds other securities rather than running a business of "
        "its own, and this platform's filing readers ask company "
        "questions. This is a limit of this platform's coverage of "
        "funds, not missing evidence about the fund."
    ),
)

_GENERAL = DossierDefinition(
    kind=DossierKind.GENERAL,
    title="Investment dossier",
    classification_heading="Investment type",
    score_labels=MappingProxyType(score_labels_for(None)),
    filings_apply=True,
)


def definition_for(asset_class: AssetClass | None) -> DossierDefinition:
    """The dossier definition for this kind of security.

    Total, so a dossier's semantics exist before any evidence does. A
    security whose class nobody established gets the general case — the
    titles make no claim an UNKNOWN cannot carry.
    """

    if asset_class is AssetClass.CRYPTO:
        return _CRYPTO

    if asset_class is AssetClass.COMMODITY:
        return _COMMODITY

    if asset_class is AssetClass.ETF:
        return _FUND

    if asset_class is AssetClass.STOCK:
        return _EQUITY

    return _GENERAL
