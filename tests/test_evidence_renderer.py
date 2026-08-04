from app.domain.committee_evidence import CommitteeEvidence
from app.domain.committee_opinion import CommitteeOpinion
from app.services.evidence_renderer import EvidenceRenderer


def test_render():
    opinion = CommitteeOpinion(
        member="Momentum",
        vote="BUY",
        confidence=87,
        rationale="Strong momentum.",
        evidence=(
            CommitteeEvidence(
                title="Market outlook",
                value="BULLISH",
            ),
        ),
    )

    rendered = EvidenceRenderer().render(opinion)

    assert "Momentum Committee" in rendered
    assert "BUY" in rendered
    assert "Market outlook: BULLISH" in rendered
    assert "Strong momentum." in rendered
