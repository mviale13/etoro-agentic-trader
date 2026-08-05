"""
The Executive Writer — the Communication layer's language specialist.

It receives canonical objects the Artificial CIO already produced, worded
as numbered findings, and returns an investment-committee narrative in
which every paragraph cites the findings it rests on. It never decides:
the recommendation it echoes is validated against the ExecutiveDecision,
a paragraph citing a finding that does not exist is rejected, and any
failure — no credentials, a declined request, an ungrounded draft —
produces an honest absence, never a fabricated narrative. The
deterministic renderers remain the canonical presentation; this layer
only adds language on top of a judgment that is already made.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.application.committees.models.committee_opinion import CommitteeOpinion
from app.cio.executive_decision import DecisionEvidence, ExecutiveDecision
from app.domain.executive_narrative import (
    NARRATIVE_SECTIONS,
    ExecutiveNarrative,
    NarrativeFinding,
    NarrativeSection,
)
from app.domain.provenance import Provenance
from app.domain.thesis.investment_thesis import InvestmentThesis

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic

#: Words per section beyond which a draft is rejected. The prompt asks
#: for at most 120; the validator allows headroom for connectives but
#: refuses essays — a narrative is a memorandum, not a report.
MAX_SECTION_WORDS = 160

SYSTEM_PROMPT = """\
You are the communication specialist of the Artificial CIO, an
investment platform whose reasoning is deterministic and already
finished before you are called.

You are not the decision maker.

Rules:
- Never invent facts.
- Never change the recommendation.
- Never introduce unsupported conclusions.
- Never predict or speculate.
- Never contradict the decision you are given.
- Every section must be supported by the supplied findings, and must
  list the ids of the findings it rests on.
- Mention both supporting and opposing evidence.
- Explain trade-offs plainly.
- Prefer institutional investment language, in complete sentences.
- At most 120 words per section.
- Where the findings state that something is missing or unmeasured,
  say so — absence is part of the case, not a gap to write around.
"""


class NarrativeRejected(Exception):
    """The writer's draft failed validation, with the reason worded."""


def build_findings(
    decision: ExecutiveDecision,
    thesis: InvestmentThesis,
    evidence: DecisionEvidence,
    opinions: tuple[CommitteeOpinion, ...],
) -> tuple[NarrativeFinding, ...]:
    """
    Word the canonical objects as numbered findings.

    This is the writer's entire world: it sees nothing the Artificial
    CIO did not produce, and every finding names the canonical object it
    came from so a citation on screen leads somewhere real.
    """

    findings: list[NarrativeFinding] = []

    def add(prefix: str, statements: list[tuple[str, str]]) -> None:
        for index, (statement, source) in enumerate(statements, start=1):
            findings.append(
                NarrativeFinding(
                    id=f"{prefix}{index}",
                    statement=statement,
                    source=source,
                )
            )

    add(
        "D",
        [
            (
                f"The Artificial CIO decided {decision.state.value} with "
                f"conviction {decision.conviction}/100. Rationale: "
                f"{decision.rationale}",
                "ExecutiveDecision",
            )
        ],
    )

    add(
        "E",
        [(line, "DecisionEvidence") for line in decision.evidence_weighed],
    )

    add(
        "M",
        [
            (f"Missing evidence: {line}", "DecisionEvidence — absent")
            for line in decision.missing_evidence
        ],
    )

    thesis_statements: list[tuple[str, str]] = [
        (f"Thesis summary: {thesis.summary}", "InvestmentThesis"),
        (
            f"Expected holding period: {thesis.expected_holding_period}",
            "InvestmentThesis",
        ),
    ]

    thesis_statements.extend(
        (f"Catalyst: {line}", "InvestmentThesis") for line in thesis.catalysts
    )

    thesis_statements.extend(
        (f"Invalidation condition: {line}", "InvestmentThesis")
        for line in thesis.invalidation_conditions
    )

    if thesis.previous_decisions:
        thesis_statements.append(
            (
                f"Recorded history: {thesis.previous_decisions}",
                "DecisionJournal",
            )
        )

    add("T", thesis_statements)

    add(
        "X",
        [
            (line, "Portfolio and market context — not the security")
            for line in (*thesis.context_strengths, *decision.context_risks)
        ],
    )

    committee_statements: list[tuple[str, str]] = []

    for opinion in opinions:
        if opinion.confidence is None:
            committee_statements.append(
                (
                    f"The {opinion.committee} committee abstained — an "
                    f"abstention, not opposition. {opinion.summary}",
                    f"CommitteeOpinion — {opinion.committee}",
                )
            )
        else:
            committee_statements.append(
                (
                    f"The {opinion.committee} committee recommends "
                    f"{opinion.recommendation.value} at confidence "
                    f"{opinion.confidence:.0f}. {opinion.summary}",
                    f"CommitteeOpinion — {opinion.committee}",
                )
            )

    add("C", committee_statements)

    if not evidence.security_evidenced:
        add(
            "N",
            [
                (
                    "Nothing about the security itself could be gathered "
                    "this cycle; the case rests on portfolio and market "
                    "context alone.",
                    "DecisionEvidence",
                )
            ],
        )

    return tuple(findings)


def narrative_schema() -> dict[str, Any]:
    """The structured-output contract the writer must fill."""

    return {
        "type": "object",
        "properties": {
            "headline": {"type": "string"},
            "recommendation": {
                "type": "string",
                "description": (
                    "Echo the decision state exactly as supplied. You do not choose it."
                ),
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "enum": list(NARRATIVE_SECTIONS),
                        },
                        "text": {"type": "string"},
                        "finding_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["section", "text", "finding_ids"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["headline", "recommendation", "sections"],
        "additionalProperties": False,
    }


def user_prompt(
    symbol: str,
    decision_state: str,
    findings: tuple[NarrativeFinding, ...],
) -> str:
    lines = [
        f"Security: {symbol}",
        f"Decision (already made, echo it exactly): {decision_state}",
        "",
        "Findings — the only facts you may use. Cite ids per section:",
    ]

    lines.extend(
        f"[{finding.id}] ({finding.source}) {finding.statement}" for finding in findings
    )

    lines.append("")
    lines.append(
        "Write the narrative sections: executive_summary, why_now, "
        "trade_off, committee_summary, thesis_invalidators. Omit a "
        "section only when no finding supports it."
    )

    return "\n".join(lines)


def narrative_from_payload(
    payload: dict[str, Any],
    symbol: str,
    decision_state: str,
    findings: tuple[NarrativeFinding, ...],
    model: str,
) -> ExecutiveNarrative:
    """
    Accept a draft only if it is grounded and changes nothing.

    Rejections are worded, because the reason a narrative is absent is
    itself something the investor may be shown.
    """

    if payload.get("recommendation") != decision_state:
        raise NarrativeRejected(
            "The writer returned a different recommendation than the "
            "Artificial CIO decided, so the draft was discarded."
        )

    known = {finding.id for finding in findings}

    raw_sections = payload.get("sections") or []

    if not raw_sections:
        raise NarrativeRejected("The writer returned no sections.")

    sections: list[NarrativeSection] = []
    seen: set[str] = set()

    for raw in raw_sections:
        name = raw.get("section", "")

        if name not in NARRATIVE_SECTIONS or name in seen:
            raise NarrativeRejected(
                f"The writer returned an unknown or repeated section "
                f"({name!r}), so the draft was discarded."
            )

        seen.add(name)

        text = (raw.get("text") or "").strip()
        cited = tuple(raw.get("finding_ids") or ())

        if not text:
            raise NarrativeRejected(f"Section {name} was empty.")

        if len(text.split()) > MAX_SECTION_WORDS:
            raise NarrativeRejected(
                f"Section {name} exceeded {MAX_SECTION_WORDS} words."
            )

        if not cited:
            raise NarrativeRejected(
                f"Section {name} cites no findings. Every paragraph must "
                "be traceable to evidence."
            )

        unknown = [item for item in cited if item not in known]

        if unknown:
            raise NarrativeRejected(
                f"Section {name} cites findings that do not exist "
                f"({', '.join(unknown)}), so the draft was discarded."
            )

        sections.append(NarrativeSection(section=name, text=text, finding_ids=cited))

    headline = (payload.get("headline") or "").strip()

    if not headline:
        raise NarrativeRejected("The writer returned no headline.")

    ordered = tuple(
        sorted(sections, key=lambda item: NARRATIVE_SECTIONS.index(item.section))
    )

    return ExecutiveNarrative(
        symbol=symbol,
        recommendation=decision_state,
        headline=headline,
        sections=ordered,
        findings=findings,
        model=model,
        reading=Provenance(
            source=f"Executive Writer ({model})",
            observed_at=datetime.now(UTC),
        ),
    )


class ExecutiveWriter:
    """Call the model, then trust only what survives validation."""

    def __init__(
        self,
        client: AsyncAnthropic,
        model: str,
    ) -> None:
        self._client = client
        self._model = model

    async def write(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> ExecutiveNarrative:
        findings = build_findings(decision, thesis, evidence, opinions)

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": narrative_schema(),
                }
            },
            messages=[
                {
                    "role": "user",
                    "content": user_prompt(
                        symbol,
                        decision.state.value,
                        findings,
                    ),
                }
            ],
        )

        if response.stop_reason == "refusal":
            raise NarrativeRejected(
                "The writing model declined the request, so no narrative was produced."
            )

        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise NarrativeRejected(
                "The writer returned unparseable output."
            ) from error

        return narrative_from_payload(
            payload,
            symbol=symbol,
            decision_state=decision.state.value,
            findings=findings,
            model=self._model,
        )
