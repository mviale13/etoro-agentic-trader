"""The seam between knowledge acquisition and wherever a filing lives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.issuer_identity import IssuerIdentity, issuer_id_in, reconcile
from app.domain.primary_source import (
    PrimarySource,
    PrimarySourceUnavailable,
    SourceDocument,
)


class HeldIdentity(Protocol):
    """What this platform already believes a symbol denotes.

    A callable rather than a store, so the resolver stays a provider
    seam and does not learn how evidence is kept. `None` where nothing
    is held, which is a first reading rather than an agreement.
    """

    def __call__(self, symbol: str) -> IssuerIdentity | None: ...


class PrimarySourceProvider(Protocol):
    """
    Anything that can find and fetch a company's own published account.

    A provider is acquisition, not interpretation. It resolves which
    document is current, fetches it, and divides it into the two sections
    the extraction reads. It never decides what the document means, and
    the rules the extraction holds it to are identical whichever provider
    supplied it.

    `resolve` is deliberately separate from `fetch` and deliberately
    cheap. Knowledge is kept against a document's key, so a caller that
    already holds knowledge for the current document should be able to
    discover that without downloading it.
    """

    #: The provider as a reader would name it, e.g. "SEC EDGAR".
    name: str

    def resolve(self, symbol: str) -> PrimarySource:
        """
        Which document is this company's current account of itself.

        Raises `PrimarySourceUnavailable`, worded, where this provider
        holds nothing for the security.
        """
        ...

    def fetch(self, source: PrimarySource) -> SourceDocument:
        """The document itself, divided into the sections that are read."""
        ...


class PrimarySourceResolver:
    """
    Ask each provider in turn, and report honestly when none can answer.

    Order is priority: the most authoritative source that holds the
    company wins. EDGAR is first because a regulator's own record is the
    strongest form of the document, and a company it does not hold is not
    a company without an annual report — it is one filed somewhere this
    platform reaches next, or not yet at all.

    ESEF follows it, and closes exactly that gap for Europe. The order
    matters for the issuers that are in both: a European group listed in
    New York files a 20-F with the SEC and an annual financial report at
    home, and EDGAR's is the one already proven to read well.

    Investor Relations is last, and last for a reason that is about
    authority rather than quality. A document a regulator received
    carries a filing obligation and a dated record; the identical
    document published by the company that wrote it carries neither. So
    it is asked only where no register holds the company at all — which
    today is every German issuer.

    Where nothing resolves, every provider's reason is carried into the
    failure. "Not listed with the SEC" and "the SEC could not be reached"
    are different situations, and a caller that only learned "no source"
    could not tell a gap in coverage from an outage.
    """

    def __init__(
        self,
        providers: Sequence[PrimarySourceProvider] | None = None,
        held_identity: HeldIdentity | None = None,
    ) -> None:
        # Resolved at construction and never in a signature, which is
        # the rule `evidence_root` earned: a default frozen at import
        # binds to whatever the process was pointed at first.
        if held_identity is None:
            from app.services.issuer_identity_service import held_issuer_identity

            held_identity = held_issuer_identity

        self._held_identity = held_identity

        if providers is None:
            from app.providers.edgar_provider import EdgarProvider
            from app.providers.esef_provider import EsefProvider
            from app.providers.investor_relations_provider import (
                InvestorRelationsProvider,
            )

            providers = (
                EdgarProvider(),
                EsefProvider(),
                InvestorRelationsProvider(),
            )

        self._providers = tuple(providers)

    def resolve(self, symbol: str) -> tuple[PrimarySource, PrimarySourceProvider]:
        """The current document for this company, and who supplied it."""

        reasons: list[str] = []

        for provider in self._providers:
            try:
                resolved = provider.resolve(symbol)
            except PrimarySourceUnavailable as unavailable:
                reasons.append(f"{provider.name}: {unavailable}")
                continue

            # Before the document is fetched, and before anything reads
            # a word of it. A reassignment is not an outage and must not
            # fall through to the next provider: `IssuerReassigned`
            # propagates rather than joining `reasons`, because trying
            # the next register for a symbol whose issuer is in doubt is
            # how the wrong company's filing gets served anyway.
            reconcile(self._held_identity(symbol), _claimed(resolved))

            return resolved, provider

        raise PrimarySourceUnavailable(
            " ".join(reasons)
            or f"No primary-source provider is configured, so nothing was "
            f"looked for on {symbol}."
        )


def _claimed(source: PrimarySource) -> IssuerIdentity:
    """The identity a freshly resolved source asserts about its symbol.

    Read from the document's own address, which every source already
    carries — so this needed no new field and no stored record was
    rewritten to gain the guarantee.
    """

    return IssuerIdentity(
        symbol=source.symbol,
        registry=source.provider,
        issuer_id=issuer_id_in(source.location) or "",
        name=source.company,
        observed_on=source.published_on,
    )
