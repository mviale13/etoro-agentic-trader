from app.domain.committee_decision import CommitteeDecision
from app.services.evidence_renderer import EvidenceRenderer


class RecommendationReportService:
    def render(
        self,
        symbol: str,
        decision: CommitteeDecision,
    ) -> str:
        lines = [
            "Recommendation Report",
            "=" * 24,
            "",
            f"Symbol: {symbol}",
            "",
            f"Recommendation: {decision.recommendation}",
            f"Confidence: {decision.confidence}%",
            "",
            "Committee",
            "",
        ]

        for opinion in decision.opinions:
            lines.append(f"{opinion.member}: {opinion.vote} ({opinion.confidence}%)")

        renderer = EvidenceRenderer()

        for opinion in decision.opinions:
            lines.extend(
                [
                    "",
                    "-" * 40,
                    "",
                    renderer.render(opinion),
                ]
            )

        return "\n".join(lines)
