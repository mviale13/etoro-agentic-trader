"""Base investment opinion."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class InvestmentOpinion[EvidenceT](BaseModel):
    """
    Common opinion produced by every analyst.

    Domain-specific opinions extend this model with additional fields.
    """

    model_config = ConfigDict(frozen=True)

    confidence: float

    strengths: tuple[str, ...] = ()

    weaknesses: tuple[str, ...] = ()

    evidence: tuple[EvidenceT, ...] = ()
