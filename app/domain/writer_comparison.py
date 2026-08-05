"""Two providers, one case: what each wrote and what each measurably cost."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.token_usage import TokenUsage


@dataclass(frozen=True, slots=True)
class ProviderRun:
    """
    One provider's attempt at the identical case.

    Exactly one of `narrative` and `absent_reason` is set. Latency is
    wall-clock around the attempt, measured — None only where the
    provider could not be built and nothing ran. Usage is the provider's
    own report; cost is that report priced at the stated table, and each
    is None where its inputs are absent. Nothing here scores the
    language: which narrative reads better is the reader's judgment,
    and both rest on the same findings so the reader judges words, not
    evidence.
    """

    provider: str
    model: str
    narrative: ExecutiveNarrative | None
    absent_reason: str | None

    #: Seconds of wall clock the attempt took, or None where no attempt
    #: was made.
    latency_seconds: float | None

    #: Token counts the provider reported. None on a failed or rejected
    #: draft — the spend was real, but the report did not survive the
    #: failure path, and an unreported count is absent, not zero.
    usage: TokenUsage | None

    #: `usage` priced at the published table, or None where the usage or
    #: the price is absent.
    cost_usd: float | None


@dataclass(frozen=True, slots=True)
class WriterComparison:
    """The identical dossier run through every configured provider."""

    symbol: str
    decision_state: str
    runs: tuple[ProviderRun, ...]

    #: When the price table behind each `cost_usd` was read. Stated so a
    #: cost line never implies a live quote.
    prices_stated_on: date
