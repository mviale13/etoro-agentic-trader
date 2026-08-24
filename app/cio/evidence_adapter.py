from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.cio.executive_decision import DecisionEvidence


class EvidenceCategory(StrEnum):
    QUALITY = "QUALITY"
    GROWTH = "GROWTH"
    PROFITABILITY = "PROFITABILITY"
    CASH_FLOW = "CASH_FLOW"
    BALANCE_SHEET = "BALANCE_SHEET"
    MARKET = "MARKET"


class AnalystEvidence(BaseModel):
    """Normalized output from one specialist analyst."""

    model_config = ConfigDict(frozen=True)

    source: str
    category: EvidenceCategory
    score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)

    rationale: str
    strengths: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()


class EvidenceAdapter:
    """Converts specialist opinions into CIO-level decision evidence."""

    def adapt(
        self,
        *,
        symbol: str,
        analyst_evidence: tuple[AnalystEvidence, ...],
        valuation_score: int,
        risk_score: int,
        portfolio_fit_score: int,
        hard_reject: bool = False,
        catalysts: tuple[str, ...] = (),
        next_trigger: str | None = None,
    ) -> DecisionEvidence:
        quality_score = self._weighted_score(analyst_evidence)
        evidence_score = self._evidence_coverage(analyst_evidence)

        evidence_weighed = self._collect_unique(
            item for evidence in analyst_evidence for item in evidence.strengths
        )
        risks = self._collect_unique(
            item for evidence in analyst_evidence for item in evidence.risks
        )
        missing_evidence = self._collect_unique(
            item for evidence in analyst_evidence for item in evidence.missing_evidence
        )

        return DecisionEvidence(
            symbol=symbol,
            quality_score=quality_score,
            evidence_score=evidence_score,
            valuation_score=valuation_score,
            risk_score=risk_score,
            portfolio_fit_score=portfolio_fit_score,
            hard_reject=hard_reject,
            evidence_weighed=evidence_weighed,
            risks=risks,
            missing_evidence=missing_evidence,
            catalysts=catalysts,
            next_trigger=next_trigger,
        )

    @staticmethod
    def _weighted_score(
        evidence_items: tuple[AnalystEvidence, ...],
    ) -> int:
        if not evidence_items:
            return 0

        total_weight = sum(evidence.confidence for evidence in evidence_items)

        if total_weight == 0:
            return 0

        weighted_total = sum(
            evidence.score * evidence.confidence for evidence in evidence_items
        )

        return round(weighted_total / total_weight)

    @staticmethod
    def _evidence_coverage(
        evidence_items: tuple[AnalystEvidence, ...],
    ) -> int:
        if not evidence_items:
            return 0

        category_count = len(
            {evidence.category for evidence in evidence_items},
        )
        category_coverage = min(
            category_count / len(EvidenceCategory),
            1.0,
        )

        average_confidence = sum(
            evidence.confidence for evidence in evidence_items
        ) / len(evidence_items)

        return round(
            average_confidence * category_coverage,
        )

    @staticmethod
    def _collect_unique(items: Iterable[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(items))
