"""Compose the Executive Writer behind its feature flag."""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.application.committees.models.committee_opinion import CommitteeOpinion
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.config import get_settings
from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.providers.narrative_provider import NarrativeProvider
from app.renderers.executive_writer import ExecutiveWriter, NarrativeRejected

#: The flag that turns the writer on. Off by default: the deterministic
#: renderers are canonical, and language generation is opt-in.
FLAG = "MOVRVEST_EXECUTIVE_WRITER"

#: Which provider words the case. OpenAI is the configured default;
#: Anthropic is the seam's first implementation and one env var away.
#: Every provider is held to the same draft contract and the same
#: validator, so switching changes the language, never the rules.
PROVIDER_ENV = "MOVRVEST_WRITER_PROVIDER"
DEFAULT_PROVIDER = "openai"

#: The model that words the case. Overridable so the platform can pin or
#: upgrade without a code change; the default depends on the provider.
MODEL_ENV = "MOVRVEST_WRITER_MODEL"
DEFAULT_MODELS = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-5-nano",
}

#: Wire timeout for a draft, in seconds — generous, because a narrative
#: is written once per dossier, not per keystroke.
DRAFT_TIMEOUT = 90.0


@dataclass(frozen=True, slots=True)
class NarrativeOutcome:
    """A narrative, or the worded reason there is none. Never both."""

    narrative: ExecutiveNarrative | None
    absent_reason: str | None


def resolve_provider(name: str | None = None) -> NarrativeProvider | str:
    """
    Build the configured provider, or word why it cannot be built.

    The return is either a provider ready to draft or the sentence a
    surface should show: unknown provider name, missing credentials, or
    a missing SDK are all worded absences, never silent fallbacks — a
    platform that quietly swapped writing models would be deciding
    something the investor was told the configuration decides.

    `name` asks for a specific provider — the comparison harness builds
    each one this way. The model override applies only to the provider
    the environment actively configures: it names one model, and pinning
    a second provider to a first provider's model would be nonsense
    worded as configuration.
    """

    configured = os.environ.get(PROVIDER_ENV, DEFAULT_PROVIDER).strip().lower()
    name = (name or configured).strip().lower()

    if name not in DEFAULT_MODELS:
        return (
            f"The Executive Writer does not know the provider {name!r}, "
            "so no narrative was generated."
        )

    override = os.environ.get(MODEL_ENV, "").strip()
    model = override if override and name == configured else DEFAULT_MODELS[name]

    # Keys come from the process environment first and the same `.env`
    # the broker keys live in second — pydantic-settings' own
    # precedence, restated here because the SDK clients would otherwise
    # read only the process environment and silently miss `.env`.
    settings = get_settings()

    if name == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or settings.anthropic_api_key
        auth_token = (
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or settings.anthropic_auth_token
        )

        if not (api_key or auth_token):
            return (
                "The Executive Writer is on but no Anthropic "
                "credentials are configured, so no narrative was "
                "generated."
            )

        from anthropic import AsyncAnthropic

        from app.providers.anthropic_narrative_provider import (
            AnthropicNarrativeProvider,
        )

        return AnthropicNarrativeProvider(
            client=(
                AsyncAnthropic(api_key=api_key, timeout=DRAFT_TIMEOUT)
                if api_key
                else AsyncAnthropic(auth_token=auth_token, timeout=DRAFT_TIMEOUT)
            ),
            model=model,
        )

    openai_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key

    if not openai_key:
        return (
            "The Executive Writer is on but no OpenAI credentials "
            "are configured, so no narrative was generated."
        )

    try:
        from openai import AsyncOpenAI
    except ImportError:
        return (
            "The Executive Writer is set to OpenAI but the OpenAI SDK "
            "is not installed, so no narrative was generated."
        )

    from app.providers.openai_narrative_provider import OpenAINarrativeProvider

    return OpenAINarrativeProvider(
        client=AsyncOpenAI(api_key=openai_key, timeout=DRAFT_TIMEOUT),
        model=model,
    )


class ExecutiveWriterService:
    """
    Produce a narrative when allowed, and an honest absence otherwise.

    Every failure path returns a reason in words: the flag being off, no
    credentials, the model declining, a draft failing the grounding
    validator. A surface can always state why there is no narrative,
    which matters on a platform whose product is trust.
    """

    def __init__(self, writer: ExecutiveWriter | None = None) -> None:
        self._writer = writer

    @staticmethod
    def enabled() -> bool:
        return os.environ.get(FLAG, "").strip().lower() in {"on", "1", "true"}

    async def narrate(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> NarrativeOutcome:
        if not self.enabled():
            return NarrativeOutcome(
                narrative=None,
                absent_reason=(
                    "The Executive Writer is off. The structured case "
                    "above is the canonical rendering."
                ),
            )

        writer = self._writer

        if writer is None:
            resolved = resolve_provider()

            if isinstance(resolved, str):
                return NarrativeOutcome(narrative=None, absent_reason=resolved)

            writer = ExecutiveWriter(provider=resolved)

        try:
            narrative = await writer.write(
                symbol=symbol,
                decision=decision,
                thesis=thesis,
                evidence=evidence,
                opinions=opinions,
            )
        except NarrativeRejected as rejection:
            return NarrativeOutcome(narrative=None, absent_reason=str(rejection))
        except Exception:
            # A provider outage is not a reason to fail the dossier; the
            # deterministic rendering stands on its own.
            return NarrativeOutcome(
                narrative=None,
                absent_reason=(
                    "The writing model could not be reached, so no "
                    "narrative was generated."
                ),
            )

        return NarrativeOutcome(narrative=narrative, absent_reason=None)
