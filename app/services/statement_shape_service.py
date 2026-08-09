"""Fetch a company's filing and measure the shape of its statements.

Costs a fetch and nothing else. No model is asked, nothing is stored,
and no observation is taken — which is what makes this safe to run over
a whole corpus, and what makes it a measurement of this platform rather
than knowledge about a company.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.primary_source import (
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
)
from app.domain.statement_shape import DocumentShape, shape_of
from app.providers.primary_source_provider import PrimarySourceResolver
from app.services.company_knowledge_service import KnowledgeState


@dataclass(frozen=True, slots=True)
class ShapeOutcome:
    """The shape, or the reason there is none — never both absent."""

    state: KnowledgeState
    shape: DocumentShape | None = None
    absent_because: str | None = None


class StatementShapeService:
    """What shape a company's current statements have, measured on demand."""

    def __init__(self, sources: PrimarySourceResolver | None = None) -> None:
        self._sources = sources or PrimarySourceResolver()

    def shape(self, symbol: str) -> ShapeOutcome:
        normalized = symbol.upper().strip()

        try:
            source, provider = self._sources.resolve(normalized)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            return ShapeOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                absent_because=str(unavailable),
            )

        return ShapeOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            shape=shape_of(normalized, document),
        )
