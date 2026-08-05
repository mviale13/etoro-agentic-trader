"""Compose the Executive Writer behind its feature flag."""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.application.committees.models.committee_opinion import CommitteeOpinion
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.renderers.executive_writer import ExecutiveWriter, NarrativeRejected

#: The flag that turns the writer on. Off by default: the deterministic
#: renderers are canonical, and language generation is opt-in.
FLAG = "MOVRVEST_EXECUTIVE_WRITER"

#: The model that words the case. Overridable so the platform can pin or
#: upgrade without a code change.
MODEL_ENV = "MOVRVEST_WRITER_MODEL"
DEFAULT_MODEL = "claude-opus-5"


@dataclass(frozen=True, slots=True)
class NarrativeOutcome:
    """A narrative, or the worded reason there is none. Never both."""

    narrative: ExecutiveNarrative | None
    absent_reason: str | None


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

        writer = self._writer or self._build_writer()

        if writer is None:
            return NarrativeOutcome(
                narrative=None,
                absent_reason=(
                    "The Executive Writer is on but no Anthropic "
                    "credentials are configured, so no narrative was "
                    "generated."
                ),
            )

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

    @staticmethod
    def _build_writer() -> ExecutiveWriter | None:
        if not (
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ):
            return None

        from anthropic import AsyncAnthropic

        return ExecutiveWriter(
            client=AsyncAnthropic(timeout=90.0),
            model=os.environ.get(MODEL_ENV, DEFAULT_MODEL),
        )
