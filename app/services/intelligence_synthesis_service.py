"""Compose the Intelligence Synthesist behind its own flag.

`ExecutiveWriterService`'s shape, and deliberately not its instance. The
two are different jobs on the same infrastructure: the writer words a
finished *decision* and is switched off for digital assets entirely —
*"a digital asset's case is a short list of measurements and absences,
and wording it added nothing"* — while this reads a *current
intelligence* packet for exactly those assets. One flag could not
express both, so there are two, on the same convention and the same
provider seam.

**Synthesis is optional; evidence is not.** Every failure path returns
a status and a sentence, and the deterministic brief renders underneath
regardless. Nothing here can leave a surface with neither a synthesis
nor a reason.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from app.config import get_settings
from app.domain.crypto_intelligence import CryptoIntelligenceSnapshot
from app.domain.intelligence_journal import TemporalFact
from app.domain.intelligence_synthesis import (
    IntelligenceSynthesis,
    SynthesisStatus,
    absent,
)
from app.domain.provenance import Provenance
from app.providers.narrative_provider import NarrativeProvider
from app.renderers.intelligence_synthesist import (
    IntelligenceSynthesist,
    SynthesisRejected,
    build_findings,
)
from app.services.narrative_providers import build_provider

#: The flag that turns synthesis on. Off by default, exactly as the
#: Executive Writer is: the deterministic brief is canonical and
#: language generation is opt-in.
FLAG = "MOVRVEST_INTELLIGENCE_SYNTHESIS"

#: Which model does the reading. The Executive Writer's own variables,
#: deliberately: *which provider this platform talks to* is one
#: decision, and making an operator configure it twice would let the two
#: drift apart for no reason. What is separate is the **on switch**,
#: because wording a decision and reading an intelligence packet are
#: different jobs and an operator may well want one without the other.
PROVIDER_ENV = "MOVRVEST_WRITER_PROVIDER"
MODEL_ENV = "MOVRVEST_WRITER_MODEL"

DEFAULT_PROVIDER = "openai"
DEFAULT_MODELS = {"anthropic": "claude-opus-5", "openai": "gpt-5-nano"}

#: A synthesis is one call over an already-assembled packet.
SYNTHESIS_TIMEOUT = 90.0

#: Below this there is not enough to connect. A synthesis over two
#: findings is a restatement with a model call attached, and the
#: deterministic brief already says it better.
MINIMUM_FINDINGS = 4


class IntelligenceSynthesisService:
    """A reading of the intelligence packet, or the reason there is none."""

    def __init__(self, synthesist: IntelligenceSynthesist | None = None) -> None:
        self._synthesist = synthesist

    @staticmethod
    def enabled() -> bool:
        flag = os.environ.get(FLAG) or get_settings().movrvest_intelligence_synthesis

        return flag.strip().lower() in {"on", "1", "true"}

    async def synthesise(
        self,
        snapshot: CryptoIntelligenceSnapshot,
        history: tuple[TemporalFact, ...] = (),
    ) -> IntelligenceSynthesis:
        symbol = snapshot.symbol

        if not self.enabled():
            return absent(
                symbol,
                SynthesisStatus.DISABLED,
                "Synthesis is off. The structured intelligence below is the "
                "canonical rendering, and always is.",
            )

        if len(build_findings(snapshot, history)) < MINIMUM_FINDINGS:
            return absent(
                symbol,
                SynthesisStatus.THIN,
                "Too little has been read for this asset to be worth "
                "connecting. Acquiring more is an explicit spend — "
                "`movrvest acquire` does it.",
            )

        synthesist = self._synthesist

        if synthesist is None:
            resolved = resolve_provider()

            if isinstance(resolved, str):
                return absent(symbol, SynthesisStatus.UNCONFIGURED, resolved)

            synthesist = IntelligenceSynthesist(provider=resolved)

        return await self._written(snapshot, synthesist, symbol, history)

    async def _written(
        self,
        snapshot: CryptoIntelligenceSnapshot,
        synthesist: IntelligenceSynthesist,
        symbol: str,
        history: tuple[TemporalFact, ...] = (),
    ) -> IntelligenceSynthesis:

        try:
            sections, model = await synthesist.synthesise(snapshot, history)
        except SynthesisRejected as rejection:
            # The guard worked. Say so plainly: a refused draft is a fact
            # about this platform's checking, not an embarrassment to
            # hide behind a generic outage message.
            return absent(
                symbol,
                SynthesisStatus.REJECTED,
                f"A synthesis was drafted and refused: {rejection}",
            )
        except Exception:
            return absent(
                symbol,
                SynthesisStatus.UNAVAILABLE,
                "The synthesis model could not be reached, so the "
                "structured intelligence below stands on its own.",
            )

        what_matters, why_it_matters, watch_next = sections

        return IntelligenceSynthesis(
            symbol=symbol,
            status=SynthesisStatus.WRITTEN,
            what_matters=what_matters,
            why_it_matters=why_it_matters,
            watch_next=watch_next,
            model=model,
            reading=Provenance(
                source=f"Intelligence Synthesist ({model})",
                observed_at=datetime.now(UTC),
            ),
        )


def resolve_provider() -> NarrativeProvider | str:
    """The configured provider, or the sentence a surface should show.

    The knowledge reader's pattern rather than an import from the
    Executive Writer: each seam names its own provider and model and
    they share `build_provider`, which is the wiring. Importing the
    writer's resolver instead would have put the decision layer one
    import away from a module that must never reach it.
    """

    settings = get_settings()

    name = (
        (
            os.environ.get(PROVIDER_ENV)
            or settings.movrvest_writer_provider
            or DEFAULT_PROVIDER
        )
        .strip()
        .lower()
    )

    if name not in DEFAULT_MODELS:
        return (
            f"The Intelligence Synthesist does not know the provider "
            f"{name!r}, so no synthesis was generated."
        )

    override = (os.environ.get(MODEL_ENV) or settings.movrvest_writer_model).strip()

    return build_provider(
        name=name,
        model=override or DEFAULT_MODELS[name],
        timeout=SYNTHESIS_TIMEOUT,
        purpose="The Intelligence Synthesist",
    )
