"""Compose the Executive Writer behind its feature flag."""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.config import get_settings
from app.domain.asset_class import AssetClass
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.providers.narrative_provider import NarrativeProvider
from app.renderers.executive_writer import ExecutiveWriter, NarrativeRejected
from app.services.narrative_providers import build_provider

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

    # Configuration comes from the process environment first and the
    # same `.env` the broker keys live in second — pydantic-settings'
    # own precedence, restated here because the SDK clients and this
    # module would otherwise read only the process environment and
    # silently miss `.env`.
    settings = get_settings()

    configured = (
        (
            os.environ.get(PROVIDER_ENV)
            or settings.movrvest_writer_provider
            or DEFAULT_PROVIDER
        )
        .strip()
        .lower()
    )
    name = (name or configured).strip().lower()

    if name not in DEFAULT_MODELS:
        return (
            f"The Executive Writer does not know the provider {name!r}, "
            "so no narrative was generated."
        )

    override = (os.environ.get(MODEL_ENV) or settings.movrvest_writer_model).strip()
    model = override if override and name == configured else DEFAULT_MODELS[name]

    return build_provider(
        name=name,
        model=model,
        timeout=DRAFT_TIMEOUT,
        purpose="The Executive Writer",
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
        flag = os.environ.get(FLAG) or get_settings().movrvest_executive_writer

        return flag.strip().lower() in {"on", "1", "true"}

    async def narrate(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
        asset_class: AssetClass | None = None,
    ) -> NarrativeOutcome:
        # A security with no company behind it is not worded. Its case is
        # ten findings, most of them absences, and asked to write five
        # sections over that the writer filled the space with work this
        # platform does not do: "prepare diligence and sizing plans",
        # "build operational readiness and risk controls". No such
        # diligence, sizing or controls exist. Every other sentence
        # restated a finding printed directly beneath it.
        #
        # So the case stands as measured. It costs the investor fifteen
        # seconds and a model call less, and loses no reading the
        # structured case did not already give.
        if asset_class is not None and asset_class.has_no_company:
            return NarrativeOutcome(
                narrative=None,
                # Worded by the asset's own noun: this branch now covers
                # a fund as well as a token, and "a digital asset's case"
                # about a Treasury fund would be the platform misnaming
                # what it is refusing to word.
                absent_reason=(
                    f"A {asset_class.noun}'s case is a short list of "
                    "measurements and absences, and wording it added "
                    "nothing the case below does not already say. It is "
                    "left as measured."
                ),
            )

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
