"""Building a model client, once, for everything that talks to a model.

Two jobs in this platform put a prompt to a model: the Executive Writer,
which words a finished case, and the knowledge reader, which locates
facts in a filing. They are configured apart on purpose — one is
formatting and the other is evidence — and they are *built* the same way,
because a provider is a provider.

What stays here is the wiring: which SDK, which credential, which
timeout, and the worded refusal when one of those is missing. What each
caller keeps is the choice of provider and model, which is the part that
differs and the part a reader of the configuration cares about.
"""

from __future__ import annotations

import os

from app.config import get_settings
from app.providers.narrative_provider import NarrativeProvider

#: The providers this platform can build. A name outside this set is a
#: configuration mistake and is worded as one rather than defaulted away.
PROVIDERS = ("anthropic", "openai")


def build_provider(
    name: str,
    model: str,
    timeout: float,
    purpose: str,
) -> NarrativeProvider | str:
    """
    A provider ready to draft, or the sentence a surface should show.

    An unknown provider name, a missing credential and a missing SDK are
    all worded absences, never silent fallbacks — a platform that quietly
    swapped models would be deciding something the investor was told the
    configuration decides. `purpose` names the caller in that sentence,
    so a reader learns which of the two model seams is unconfigured.

    Configuration comes from the process environment first and the same
    `.env` the broker keys live in second — pydantic-settings' own
    precedence, restated here because the SDK clients would otherwise
    read only the process environment and silently miss `.env`.
    """

    settings = get_settings()

    if name not in PROVIDERS:
        return f"{purpose} does not know the provider {name!r}, so it did not run."

    if name == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or settings.anthropic_api_key
        auth_token = (
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or settings.anthropic_auth_token
        )

        if not (api_key or auth_token):
            return (
                f"{purpose} is set to Anthropic and no Anthropic credentials "
                "are configured, so it did not run."
            )

        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            return (
                f"{purpose} is set to Anthropic and the Anthropic SDK is not "
                "installed, so it did not run."
            )

        from app.providers.anthropic_narrative_provider import (
            AnthropicNarrativeProvider,
        )

        return AnthropicNarrativeProvider(
            client=(
                AsyncAnthropic(api_key=api_key, timeout=timeout)
                if api_key
                else AsyncAnthropic(auth_token=auth_token, timeout=timeout)
            ),
            model=model,
        )

    openai_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key

    if not openai_key:
        return (
            f"{purpose} is set to OpenAI and no OpenAI credentials are "
            "configured, so it did not run."
        )

    try:
        from openai import AsyncOpenAI
    except ImportError:
        return (
            f"{purpose} is set to OpenAI and the OpenAI SDK is not installed, "
            "so it did not run."
        )

    from app.providers.openai_narrative_provider import OpenAINarrativeProvider

    return OpenAINarrativeProvider(
        client=AsyncOpenAI(api_key=openai_key, timeout=timeout),
        model=model,
    )
