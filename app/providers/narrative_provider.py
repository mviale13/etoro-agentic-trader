"""The seam between the Executive Writer and whichever model words a case.

A provider is transport, not judgment. It receives the finished prompts
and the structured-output schema, returns the raw draft text, and does
nothing else: no validation, no repair, no interpretation. Every rule
about what a draft must contain — the grounding contract, the echoed
recommendation, the section vocabulary — belongs to the Executive Writer
and is identical whichever provider carried the request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.token_usage import TokenUsage


class NarrativeDeclined(Exception):
    """The provider's model declined to write.

    A decline is a content outcome, not a wire failure: the request
    reached the model and the model said no. Providers map their own
    decline signal onto this one exception so the Writer can word the
    absence the same way whichever provider declined.
    """


@dataclass(frozen=True, slots=True)
class DraftRequest:
    """Everything a provider needs to produce a draft, provider-neutral."""

    system_prompt: str
    user_prompt: str

    #: The structured-output contract the draft must satisfy, as JSON
    #: Schema. Each provider enforces it with its own mechanism; the
    #: schema itself is shared so both are held to the same contract.
    schema: dict[str, Any]

    max_tokens: int


@dataclass(frozen=True, slots=True)
class Draft:
    """The raw draft and what producing it measurably cost."""

    text: str

    #: The model that actually wrote this, named by the provider.
    model: str

    #: Token counts the provider reported, or None where it reported
    #: none. Never estimated here.
    usage: TokenUsage | None


class NarrativeProvider(Protocol):
    """Anything that can turn a draft request into raw draft text."""

    #: Provider name as a surface would print it, e.g. "Anthropic".
    name: str

    #: The model this provider is configured to call.
    model: str

    async def draft(self, request: DraftRequest) -> Draft: ...
