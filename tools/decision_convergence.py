"""The Equity Decision Convergence experiment — a disposable harness.

Runs the production decision route (A) beside a counterfactual (B) in
which the pipeline consumes the classification MOVRvest has actually
earned from Business Understanding — the grounded playbook, and the
financial model `model_for` derives from it — over identical evidence
and portfolio state.

Measurement only. Nothing here is production behaviour:

- Route B exists as two in-process patches inside this script — the
  industry factory answers with the grounded playbook, and the
  pipeline's `quality_of` call receives the grounded model — applied
  and removed around one brain build and one pipeline execution.
- No decision history is written (`ExecutivePipeline(journal=None)`).
- No store is touched; both routes read the same acquired evidence.
- Nothing imports this module. Delete it when the ruling lands.

Run: `python -m tools.decision_convergence` (venv active, eToro
reachable). Writes JSON traces per (symbol, route) beside a rendered
comparison to stdout.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.domain.financial_question import FinancialModel, model_for
from app.domain.playbook import InvestmentPlaybook, PlaybookKind
from app.domain.playbook_selection import PlaybookSelection
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.business_quality_service import quality_of
from app.services.financial_engine import measure
from app.services.financial_questions import answer_questions
from app.services.financial_statement_service import FinancialStatementService
from app.services.playbook_mapping import select_grounded
from app.services.research_strategy_factory import ResearchStrategyFactory
from app.services.understanding_engine import understand

CORPUS = ("JPM", "BNP.PA", "DIS", "NVDA", "CAT", "VOW3.DE")

OUT = Path("/tmp/convergence")


def grounded_playbook(symbol: str) -> tuple[InvestmentPlaybook | None, str]:
    """The playbook the platform earned, or None where grounding refused.

    Falls back to the archived schema-11 entries where the store's
    current protocol restores nothing: those readings were shown
    bit-identical text for every EDGAR and single-document filer (11→12
    changed only untagged-package capture; 12→13 added a question), so
    for a *measurement* their segment, size and description claims are
    the platform's own established readings. Labelled, never silent —
    and never a production behaviour: the store's own door is the only
    door production uses.
    """

    import glob as globbing
    import json as jsonlib

    from app.domain.knowledge_consensus import consensus_of
    from app.repositories.company_knowledge_store import _observation
    from app.repositories.source_codec import decode_source

    observations = JsonCompanyKnowledgeStore().latest(symbol)
    label = "store (current schema)"

    if not observations:
        pattern = f"data/knowledge/{symbol.replace('.', '_')}.*.json"
        files = globbing.glob(pattern) or globbing.glob(
            f"data/knowledge/{symbol}.*.json"
        )

        if files:
            stored = jsonlib.loads(Path(files[0]).read_text(encoding="utf-8"))
            source = decode_source(stored["source"])
            observations = tuple(
                _observation(symbol, source, observed, asked=False)
                for observed in stored.get("observations", ())
            )
            label = f"archived schema-{stored.get('schema_version')} readings"

    if not observations:
        return None, "no readings"

    selection = select_grounded(understand(consensus_of(observations)))

    if isinstance(selection, PlaybookSelection):
        return selection.playbook, label

    return None, f"{label}: grounding refused"


def financial_trace(symbol: str, model: FinancialModel) -> dict[str, Any]:
    """The model's question set over the statements that exist."""

    established = FinancialStatementService().established(symbol)

    if not established:
        return {
            "model": model.value,
            "statements": [],
            "questions": "no statements at quorum — every question awaits them",
        }

    understanding = measure(symbol, established)
    answers = answer_questions(model, understanding)

    return {
        "model": model.value,
        "statements": [kind.value for kind in established],
        "questions": [
            {
                "question": answer.question.value,
                "state": answer.state.value,
                "answer": str(getattr(answer, "answer", ""))[:140] or None,
            }
            for answer in answers
        ],
    }


def workspace_trace(workspace: Any, brain: Any, symbol: str) -> dict[str, Any]:
    evidence = workspace.evidence
    company = brain.security_evidence(symbol)

    research = company.signals.research if company is not None else None

    return {
        "playbook": (
            {
                "kind": research.playbook.kind.value,
                "name": research.playbook.name,
                "analysts": [a.value for a in research.playbook.analysts],
            }
            if research is not None
            else None
        ),
        "research_opinions": (
            {str(key): str(opinion)[:140] for key, opinion in research.opinions.items()}
            if research is not None
            else None
        ),
        "quality_assessment": (
            {
                "band": workspace.quality.band.value,
                "score": workspace.quality.score,
                "answered": workspace.quality.answered,
                "excluded": len(workspace.quality.excluded),
            }
            if workspace.quality is not None
            else None
        ),
        "scores": (
            {
                "quality": evidence.quality_score,
                "valuation": evidence.valuation_score,
                "safety": evidence.safety_score,
                "evidence": evidence.evidence_score,
            }
            if evidence is not None
            else None
        ),
        "missing_evidence": list(evidence.missing_evidence) if evidence else None,
        "committees": [
            {
                "committee": opinion.committee,
                "stance": opinion.stance.value if opinion.stance else None,
                "abstained": opinion.abstained_because is not None,
                "supporting": len(opinion.supporting),
            }
            for opinion in (workspace.committee_opinions or ())
        ],
        "conviction": workspace.decision.conviction if workspace.decision else None,
        "decision": workspace.decision.state.value if workspace.decision else None,
        "rationale": workspace.decision.rationale[:160] if workspace.decision else None,
    }


async def run_route(symbol: str, grounded: InvestmentPlaybook | None) -> dict:
    """One route's complete trace. `grounded=None` is route A."""

    patches = []

    if grounded is not None:
        patches.append(
            mock.patch.object(
                ResearchStrategyFactory,
                "playbook",
                lambda self, profile, _pb=grounded: _pb,
            )
        )

        model = model_for(grounded.kind).model

        original_quality_of = quality_of

        def grounded_quality(sym, understanding, _m=model, _q=original_quality_of):
            return _q(sym, understanding, _m)

        patches.append(
            mock.patch(
                "app.application.workspace.executive_pipeline.quality_of",
                grounded_quality,
            )
        )

    for patch in patches:
        patch.start()

    try:
        brain = await BrainBuilderService().build(focus_symbols=(symbol,))

        pipeline = ExecutivePipeline(journal=None)
        workspace = pipeline.execute(symbol, brain)

        trace = workspace_trace(workspace, brain, symbol)
    finally:
        for patch in patches:
            patch.stop()

    kind = (
        grounded.kind
        if grounded is not None
        else (
            PlaybookKind(trace["playbook"]["kind"])
            if trace["playbook"]
            else PlaybookKind.UNCLASSIFIED
        )
    )

    trace["financial"] = financial_trace(symbol, model_for(kind).model)

    return trace


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    for symbol in CORPUS:
        grounded, grounded_source = grounded_playbook(symbol)

        route_a = await run_route(symbol, None)
        route_b = await run_route(symbol, grounded) if grounded is not None else route_a

        result = {
            "symbol": symbol,
            "grounded_exists": grounded is not None,
            "grounded_kind": grounded.kind.value if grounded else None,
            "grounded_source": grounded_source,
            "route_a": route_a,
            "route_b": route_b,
        }

        (OUT / f"{symbol.replace('.', '_')}.json").write_text(
            json.dumps(result, indent=1, default=str),
            encoding="utf-8",
        )

        a, b = route_a, route_b
        print(
            f"\n════ {symbol}  grounded={result['grounded_kind']}  [{grounded_source}]"
        )
        for label, t in (("A", a), ("B", b)):
            kind = t["playbook"]["kind"] if t["playbook"] else "(no evidence)"
            quality = t["scores"]["quality"] if t["scores"] else None
            print(
                f"  {label}: {kind:<18} quality={quality}"
                f" conviction={t['conviction']} decision={t['decision']}"
            )


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
