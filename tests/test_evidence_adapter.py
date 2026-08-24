from app.cio import (
    AnalystEvidence,
    EvidenceAdapter,
    EvidenceCategory,
)


def analyst(
    *,
    source: str,
    category: EvidenceCategory,
    score: int,
    confidence: int,
    veto: bool = False,
) -> AnalystEvidence:
    return AnalystEvidence(
        source=source,
        category=category,
        score=score,
        confidence=confidence,
        rationale="Test rationale.",
        strengths=(f"{source} strength.",),
        risks=(f"{source} risk.",),
        veto=veto,
    )


def test_adapter_produces_normalized_decision_evidence() -> None:
    items = (
        analyst(
            source="GrowthAnalyst",
            category=EvidenceCategory.GROWTH,
            score=90,
            confidence=80,
        ),
        analyst(
            source="ProfitabilityAnalyst",
            category=EvidenceCategory.PROFITABILITY,
            score=70,
            confidence=100,
        ),
    )

    result = EvidenceAdapter().adapt(
        symbol="MSFT",
        analyst_evidence=items,
        valuation_score=65,
        risk_score=30,
        portfolio_fit_score=75,
    )

    assert result.symbol == "MSFT"
    assert result.quality_score == 79
    assert result.valuation_score == 65
    assert len(result.evidence_weighed) == 2
    assert len(result.risks) == 2


def test_the_adapter_carries_no_veto() -> None:
    """The owner's ruling of 2026-08-24, at the second producer.

    `AnalystEvidence.veto` fed `DecisionEvidence.analyst_veto`, which
    no longer exists. The field is gone rather than left unread: a
    veto nothing can act on is dead vocabulary that reads as live.
    """

    from app.cio.evidence_adapter import AnalystEvidence

    assert "veto" not in AnalystEvidence.model_fields

    result = EvidenceAdapter().adapt(
        symbol="TEST",
        analyst_evidence=(
            analyst(
                source="BalanceSheetAnalyst",
                category=EvidenceCategory.BALANCE_SHEET,
                score=20,
                confidence=95,
            ),
        ),
        valuation_score=80,
        risk_score=80,
        portfolio_fit_score=80,
    )

    assert not hasattr(result, "analyst_veto")


def test_empty_evidence_produces_zero_scores() -> None:
    result = EvidenceAdapter().adapt(
        symbol="TEST",
        analyst_evidence=(),
        valuation_score=50,
        risk_score=50,
        portfolio_fit_score=50,
    )

    assert result.quality_score == 0
    assert result.evidence_score == 0
