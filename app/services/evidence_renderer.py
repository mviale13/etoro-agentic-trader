from app.domain.committee_opinion import CommitteeOpinion


class EvidenceRenderer:
    def render(
        self,
        opinion: CommitteeOpinion,
    ) -> str:
        lines = [
            f"{opinion.member} Committee",
            "",
            f"Vote: {opinion.vote}",
            f"Confidence: {opinion.confidence}%",
            "",
            "Evidence:",
        ]

        for item in opinion.evidence:
            lines.append(f"- {item.title}: {item.value}")

        lines.extend(
            [
                "",
                "Reason:",
                opinion.rationale,
            ]
        )

        return "\n".join(lines)
