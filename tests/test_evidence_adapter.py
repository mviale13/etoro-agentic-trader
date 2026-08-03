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


def test_adapter_propagates_analyst_veto() -> None:
    items = (
        analyst(
            source="BalanceSheetAnalyst",
            category=EvidenceCategory.BALANCE_SHEET,
            score=20,
            confidence=95,
            veto=True,
        ),
    )

    result = EvidenceAdapter().adapt(
        symbol="TEST",
        analyst_evidence=items,
        valuation_score=80,
        risk_score=80,
        portfolio_fit_score=80,
    )

    assert result.analyst_veto is True


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
