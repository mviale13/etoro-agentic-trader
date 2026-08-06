"""Compose the reader that turns a filing into grounded facts.

Kept apart from the Executive Writer's configuration, and the separation
is not tidiness. The writer's default is a small model at low reasoning
effort, chosen deliberately because wording a finished case is
formatting. Reading is not formatting: it means finding one cell among
forty tables, in a document that may be in German, and stating what is
printed there precisely enough to be checked against the document. A
reader that silently inherited the writer's model would be quietly
downgraded by a decision taken about something else.

So the reader names its own provider, its own model and its own timeout,
and every absence is worded rather than defaulted away. There is no
feature flag: reading a filing is how this platform knows anything
structural about a company, and an unconfigured reader already has an
honest answer — the knowledge is unavailable, and the reason says so.
"""

from __future__ import annotations

import os

from app.config import get_settings
from app.services.company_knowledge_extractor import CompanyKnowledgeExtractor
from app.services.narrative_providers import build_provider

#: Which provider reads a filing.
PROVIDER_ENV = "MOVRVEST_READER_PROVIDER"
DEFAULT_PROVIDER = "openai"

#: The model that reads it. Overridable so the platform can pin or
#: upgrade without a code change; the default depends on the provider.
#:
#: Deliberately not the writer's small default. A reading is checked
#: against the document and a wrong one is refused, so a weaker model
#: does not produce a wrong answer here — it produces no answer, which
#: costs the fetch and the call and leaves the company undescribed.
MODEL_ENV = "MOVRVEST_READER_MODEL"
DEFAULT_MODELS = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-5",
}

#: Wire timeout for one reading, in seconds. Longer than a draft's: the
#: prompt carries every table of a filing's discussion, which on a large
#: 10-K is tens of thousands of characters.
READING_TIMEOUT = 180.0


def resolve_reader() -> CompanyKnowledgeExtractor | str:
    """
    Build the configured reader, or word why it cannot be built.

    A string here is not an error path to be logged and swallowed. It is
    what a surface shows in place of a company's segments, and it travels
    as `KnowledgeOutcome.absent_because` exactly as a provider outage or
    a gap in coverage does.
    """

    settings = get_settings()

    name = (
        (
            os.environ.get(PROVIDER_ENV)
            or settings.movrvest_reader_provider
            or DEFAULT_PROVIDER
        )
        .strip()
        .lower()
    )

    if name not in DEFAULT_MODELS:
        return (
            f"The knowledge reader does not know the provider {name!r}, so no "
            "filing was read."
        )

    override = (os.environ.get(MODEL_ENV) or settings.movrvest_reader_model).strip()

    provider = build_provider(
        name=name,
        model=override or DEFAULT_MODELS[name],
        timeout=READING_TIMEOUT,
        purpose="The knowledge reader",
    )

    if isinstance(provider, str):
        return provider

    return CompanyKnowledgeExtractor(provider)
