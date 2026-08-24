"""How the knowledge in hand was — or was not — obtained.

Lifted out of `CompanyKnowledgeService` unchanged, so the acquisition
journal and its store can name the same vocabulary the service returns
without importing the service back. The enum, its members and its two
properties are byte-identical to the ones the service defined; the
service re-exports it, so every existing import keeps working.
"""

from __future__ import annotations

from enum import StrEnum


class KnowledgeState(StrEnum):
    """How the knowledge in hand was — or was not — obtained.

    Operationally and semantically different situations that a single
    "no knowledge" would flatten into one. Each calls for something
    different:

    - `AVAILABLE_CACHED` — read from a document already extracted. The
      normal path, and free.
    - `AVAILABLE_ACQUIRED` — a new document was fetched and read this
      cycle. Costs a fetch and two model calls, once per document.
    - `UNAVAILABLE` — no provider holds a source for this security. A
      gap in coverage: try another provider, not the same one again.
    - `PROVIDER_ERROR` — a provider could not be reached. Retrying may
      help, which is exactly what makes it different from a gap.
    - `INVALID_EXTRACTION` — a document was read and failed grounding
      validation. Nothing from it is trusted or partly stored.
    - `DOCUMENT_REFUSED` — the authoritative document exists, was
      retrieved and was parsed, and the section this platform needs
      cannot be supplied from the component or structure it supports.
      **Not a coverage gap**: another provider is not the remedy and an
      immediate retry cannot help, because nothing failed. A future
      capability — following the page ranges a cross-reference index
      names — may change the answer, which is what makes it different
      from a filing that simply does not contain the section.
    """

    AVAILABLE_CACHED = "available_cached"
    AVAILABLE_ACQUIRED = "available_acquired"
    UNAVAILABLE = "unavailable"
    PROVIDER_ERROR = "provider_error"
    INVALID_EXTRACTION = "invalid_extraction"
    DOCUMENT_REFUSED = "document_refused"

    @property
    def is_available(self) -> bool:
        return self in (
            KnowledgeState.AVAILABLE_CACHED,
            KnowledgeState.AVAILABLE_ACQUIRED,
        )

    @property
    def may_succeed_later(self) -> bool:
        """Whether asking again could plausibly produce a different answer.

        `DOCUMENT_REFUSED` is deliberately **false**. Nothing failed and
        nothing is intermittent: the filing says what it says, and the
        same request will be refused for the same structural reason for
        as long as this platform reads the same component. What could
        change the answer is a capability, not a retry.
        """

        return self is KnowledgeState.PROVIDER_ERROR
