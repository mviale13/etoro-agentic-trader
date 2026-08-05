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

The model call itself sits behind `NarrativeProvider`: the writer builds
the prompts and the schema, the provider carries them over its own wire,
and every draft — whoever wrote it — passes through the one validator
here. A provider can therefore never loosen the grounding contract; it
can only fail it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

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
from app.domain.token_usage import TokenUsage
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)

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
- A scheduled event is a date, not an outcome. Where a finding says a
  company reports on a date, you may say the date is coming; you may
  never suggest what the report will contain.
- Never contradict the decision you are given.
- Every section must be supported by the supplied findings, and must
  list the ids of the findings it rests on.
- Cite finding ids only in the finding_ids field — never write ids,
  citation lists or "Findings:" trailers inside the section text. The
  reader sees the citations beside each paragraph already; repeating
  them in prose says everything twice.
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
        (f"Invalidation condition: {line}", "InvestmentThesis")
        for line in thesis.invalidation_conditions
    )

    if thesis.trend is not None:
        thesis_statements.append(
            (
                f"Recorded history: {thesis.trend.stated}",
                "DecisionJournal",
            )
        )

    add("T", thesis_statements)

    # Scheduled events belonging to this security, dated — what "why now"
    # is entitled to rest on. They are kept out of the thesis group above
    # and given their own source line because of what they are not: a
    # catalyst is a date on a calendar, and the writer must not read a
    # scheduled report as an expectation about the report.
    add(
        "W",
        [
            (
                f"Scheduled: {line}",
                "InvestmentThesis — a dated event, not a view on its outcome",
            )
            for line in thesis.catalysts
        ],
    )

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


#: How much room a draft gets. A narrative is five short sections, but
#: both providers' current models spend reasoning tokens out of this
#: same budget, so the ceiling leaves room to think and to write.
MAX_DRAFT_TOKENS = 16000


@dataclass(frozen=True, slots=True)
class WriterResult:
    """A validated narrative and what the draft measurably cost.

    `usage` is the provider's own report, or None where it reported
    none. It rides beside the narrative rather than inside it because
    token spend is a fact about the call, not about the case.
    """

    narrative: ExecutiveNarrative
    usage: TokenUsage | None


class ExecutiveWriter:
    """Ask a provider for language, then trust only what survives validation."""

    def __init__(
        self,
        provider: NarrativeProvider,
    ) -> None:
        self.provider = provider

    async def write(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> ExecutiveNarrative:
        result = await self.write_measured(
            symbol=symbol,
            decision=decision,
            thesis=thesis,
            evidence=evidence,
            opinions=opinions,
        )

        return result.narrative

    async def write_measured(
        self,
        symbol: str,
        decision: ExecutiveDecision,
        thesis: InvestmentThesis,
        evidence: DecisionEvidence,
        opinions: tuple[CommitteeOpinion, ...],
    ) -> WriterResult:
        """Write the narrative and keep the provider's usage report beside it."""

        findings = build_findings(decision, thesis, evidence, opinions)

        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(
                symbol,
                decision.state.value,
                findings,
            ),
            schema=narrative_schema(),
            max_tokens=MAX_DRAFT_TOKENS,
        )

        try:
            draft = await self.provider.draft(request)
        except NarrativeDeclined as declined:
            # The decline keeps its wording: a provider states why there
            # is no draft, and the rejection carries that statement.
            raise NarrativeRejected(str(declined)) from declined

        if not draft.text.strip():
            # Distinct from unparseable: an empty draft usually means the
            # model spent its whole budget before writing, and the absence
            # should say so rather than blame the parser.
            raise NarrativeRejected(
                "The writer returned an empty draft, so no narrative was produced."
            )

        try:
            payload = json.loads(draft.text)
        except json.JSONDecodeError as error:
            raise NarrativeRejected(
                "The writer returned unparseable output."
            ) from error

        narrative = narrative_from_payload(
            payload,
            symbol=symbol,
            decision_state=decision.state.value,
            findings=findings,
            model=draft.model,
        )

        return WriterResult(
            narrative=narrative,
            usage=draft.usage,
        )
