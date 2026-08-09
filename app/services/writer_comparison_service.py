"""Run the identical dossier through every configured writing provider."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.thesis.investment_thesis import InvestmentThesis
from app.domain.writer_comparison import ProviderRun, WriterComparison
from app.providers.model_prices import PRICES_STATED_ON, cost_usd
from app.renderers.executive_writer import ExecutiveWriter, NarrativeRejected
from app.services.executive_writer_service import DEFAULT_MODELS, resolve_provider


@dataclass(frozen=True, slots=True)
class _Unbuilt:
    """A provider that could not be constructed, with the reason worded."""

    provider: str
    model: str
    reason: str


#: How each provider name prints. The built providers carry their own
#: label; this covers the ones that could not be built.
PROVIDER_LABELS = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
}


@dataclass(slots=True)
class WriterComparisonService:
    """
    One case, every provider, and only measured differences reported.

    Both providers receive the identical findings, prompts and schema,
    and both drafts pass through the identical validator — so what
    differs between the runs is language, latency and spend, never
    evidence or rules. Latency is wall clock, measured here. Usage is
    what each provider reported. Cost prices that report at the stated
    table. Which narrative reads better is not scored: judging language
    is the reader's, and a number claiming to measure it would be the
    kind of invented figure this platform exists to refuse.
    """

    #: Injected writers, for tests and for callers that already built
    #: them. Empty means build from configuration.
    writers: tuple[ExecutiveWriter, ...] = ()

    #: Which providers to build when none are injected.
    providers: tuple[str, ...] = field(default=tuple(DEFAULT_MODELS))

    async def compare(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> WriterComparison:
        runs: list[ProviderRun] = []

        for entry in self._entries():
            if isinstance(entry, _Unbuilt):
                runs.append(
                    ProviderRun(
                        provider=entry.provider,
                        model=entry.model,
                        narrative=None,
                        absent_reason=entry.reason,
                        latency_seconds=None,
                        usage=None,
                        cost_usd=None,
                    )
                )
                continue

            runs.append(
                await self._run(
                    entry,
                    symbol=symbol,
                    decision=decision,
                    thesis=thesis,
                    evidence=evidence,
                    opinions=opinions,
                )
            )

        return WriterComparison(
            symbol=symbol,
            decision_state=decision.state.value,
            runs=tuple(runs),
            prices_stated_on=PRICES_STATED_ON,
        )

    def _entries(self) -> tuple[ExecutiveWriter | _Unbuilt, ...]:
        if self.writers:
            return self.writers

        entries: list[ExecutiveWriter | _Unbuilt] = []

        for name in self.providers:
            resolved = resolve_provider(name)

            if isinstance(resolved, str):
                entries.append(
                    _Unbuilt(
                        provider=PROVIDER_LABELS.get(name, name),
                        model=DEFAULT_MODELS.get(name, "unknown"),
                        reason=resolved,
                    )
                )
            else:
                entries.append(ExecutiveWriter(provider=resolved))

        return tuple(entries)

    @staticmethod
    async def _run(
        writer: ExecutiveWriter,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> ProviderRun:
        provider = writer.provider
        started = time.perf_counter()

        try:
            result = await writer.write_measured(
                symbol=symbol,
                decision=decision,
                thesis=thesis,
                evidence=evidence,
                opinions=opinions,
            )
        except NarrativeRejected as rejection:
            # The attempt was real, so its duration is reported; the
            # usage report did not survive the failure path, and an
            # unreported count is absent, not zero.
            return ProviderRun(
                provider=provider.name,
                model=provider.model,
                narrative=None,
                absent_reason=str(rejection),
                latency_seconds=time.perf_counter() - started,
                usage=None,
                cost_usd=None,
            )
        except Exception:
            return ProviderRun(
                provider=provider.name,
                model=provider.model,
                narrative=None,
                absent_reason=(
                    "The writing model could not be reached, so no "
                    "narrative was generated."
                ),
                latency_seconds=time.perf_counter() - started,
                usage=None,
                cost_usd=None,
            )

        return ProviderRun(
            provider=provider.name,
            model=provider.model,
            narrative=result.narrative,
            absent_reason=None,
            latency_seconds=time.perf_counter() - started,
            usage=result.usage,
            cost_usd=cost_usd(provider.model, result.usage),
        )
