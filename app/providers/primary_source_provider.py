"""The seam between knowledge acquisition and wherever a filing lives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.primary_source import (
    PrimarySource,
    PrimarySourceUnavailable,
    SourceDocument,
)


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

    Where nothing resolves, every provider's reason is carried into the
    failure. "Not listed with the SEC" and "the SEC could not be reached"
    are different situations, and a caller that only learned "no source"
    could not tell a gap in coverage from an outage.
    """

    def __init__(
        self,
        providers: Sequence[PrimarySourceProvider] | None = None,
    ) -> None:
        if providers is None:
            from app.providers.edgar_provider import EdgarProvider

            providers = (EdgarProvider(),)

        self._providers = tuple(providers)

    def resolve(self, symbol: str) -> tuple[PrimarySource, PrimarySourceProvider]:
        """The current document for this company, and who supplied it."""

        reasons: list[str] = []

        for provider in self._providers:
            try:
                return provider.resolve(symbol), provider
            except PrimarySourceUnavailable as unavailable:
                reasons.append(f"{provider.name}: {unavailable}")

        raise PrimarySourceUnavailable(
            " ".join(reasons)
            or f"No primary-source provider is configured, so nothing was "
            f"looked for on {symbol}."
        )
