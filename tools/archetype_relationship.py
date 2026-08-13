"""Role-aware archetype selection: the counterfactual, measured.

**Research harness. Read-only. Delete when the ruling lands.**

The question (2026-08-13 ruling): does the archetype engine confuse
*diversity of revenue mechanisms* with *diversity of independent
economic engines*, and would ED1's established economic relationships
resolve that without weakening evidence standards?

Two routes over identical evidence:

- **A** — `classify()` unchanged, straight from production.
- **B** — the same arithmetic with one change: a segment the filer
  states is economically driven by another business contributes no
  *independent engine* to the ranking. Its revenue still counts as
  explained, its size is untouched, and it is never erased.

Nothing here writes. It imports production modules to read them, builds
its consensus objects in memory, and touches no store, journal or
decision path. Two properties make that checkable: the archived-reading
loader copies knowledge files into a temp directory before relabelling
them, so `data/` is never modified; and route B is implemented *here*
rather than by patching the engine, so production behaviour cannot
change even by accident.

**On the archived readings.** Only VOW3.DE and JPM restore under the
current schema (13, reading 12); the rest of the corpus is schema 11 and
the store deliberately restores it as absent. For research the harness
relabels a *copy* 11 → 12. That bypasses a gate; it changes no claim —
every (segment, share, mechanism) tuple is exactly what the reading
stored. They are archived readings, labelled as such in every output
row, and they are not evidence that the live platform holds anything.

**On the relationships.** Zero `EconomicRelationship` facts exist in the
store: ED1 shipped its contract, and its acceptance readings are
credit-blocked. So route B cannot run on established relationships. It
runs on *projections* — the filer statements measured in
`ECONOMIC_DRIVER_DEPENDENCY.md` §1–§2 and §5, each carrying the quote
the measurement found — and every projected relationship is labelled
PROJECTED in the output. A projection is a hypothesis about what ED1
would establish once funded, never a fact this platform holds.
"""

from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from app.domain.company_archetype import ARCHETYPE_OF, Archetype
from app.domain.company_knowledge import EconomicRelationship, RevenueModel
from app.domain.knowledge_consensus import (
    CompanyKnowledgeConsensus,
    ConsensusSegment,
    consensus_of,
)
from app.repositories.company_knowledge_store import (
    PREVIOUS_SCHEMA_VERSION,
    JsonCompanyKnowledgeStore,
)
from app.services.archetype_engine import (
    ENOUGH_EXPLAINED,
    LEADS,
    TIED,
)
from app.services.company_knowledge_service import CompanyKnowledgeService

REPO = Path(__file__).resolve().parent.parent
KNOWLEDGE = REPO / "data" / "knowledge"


# ── the projected relationships ─────────────────────────────────────
#
# Each is a filer statement already measured against the document in
# ECONOMIC_DRIVER_DEPENDENCY.md. None is stored; none is established.
# The driver field is free text at the filer's own altitude, exactly as
# ED1's contract defines it — which is itself a finding, see §4 of the
# research document.


@dataclass(frozen=True)
class Projection:
    """A relationship ED1 would plausibly establish, with its evidence."""

    symbol: str
    relationship: EconomicRelationship

    #: Why this is a defensible projection rather than an assumption.
    warrant: str


PROJECTED: tuple[Projection, ...] = (
    Projection(
        symbol="VOW3.DE",
        relationship=EconomicRelationship(
            dependent="Finanzdienstleistungen",
            driver=(
                "the Automotive division's products and the Group's vehicle deliveries"
            ),
            statement=(
                "Volkswagen states that this business consists predominantly "
                "in sales support for the Automotive division's products, and "
                "that vehicle deliveries are decisive and material for the "
                "generation of its new contracts."
            ),
            quoted=(
                "Das Geschäftsmodell des Konzernbereichs Finanzdienstleistungen "
                "liegt im Wesentlichen in der Vertriebsunterstützung für "
                "Produkte des Konzernbereichs Automobile."
            ),
        ),
        warrant=(
            "a dedicated business-model sentence, a titled dependence risk "
            "disclosure, a penetration KPI (37.2% of the Group's own "
            "deliveries) and an intersegment revenue row at checked "
            "addresses; zero hits for financing of non-Group brands"
        ),
    ),
    Projection(
        symbol="CAT",
        relationship=EconomicRelationship(
            dependent="Financial Products Segment",
            driver="sales of Caterpillar products",
            statement=(
                "Caterpillar states that this business's financing plans are "
                "designed to support sales of Caterpillar products and to "
                "generate financing income, and that it also finances other "
                "equipment."
            ),
            quoted=(
                "The various financing plans offered by Cat Financial are "
                "designed to support sales of Caterpillar products and "
                "generate financing income"
            ),
        ),
        warrant=(
            "the filer's own support sentence — but the same filer states "
            "it finances 'Caterpillar and other equipment', so the "
            "dependence it discloses is qualified where Volkswagen's is not"
        ),
    ),
)

#: Companies whose filer states no dependence in any evidence held.
#: Listed explicitly so the controls are visible rather than implied.
NO_RELATIONSHIP_STATED = ("DIS", "NVDA", "JPM", "BNP.PA", "META", "NFLX")


# ── loading, without touching the store ─────────────────────────────


def archived_consensus(symbol: str) -> tuple[CompanyKnowledgeConsensus | None, bool]:
    """The consensus for one symbol, and whether it came from an archive.

    Live first: a symbol the current schema restores is read through the
    ordinary read-only door and marked live. Only where the door
    answers nothing does the harness fall back to the archive, and the
    fallback relabels a *copy* — `data/` is opened read-only.
    """

    live = CompanyKnowledgeService().established(symbol).knowledge

    if live is not None:
        return live, False

    files = [
        path
        for path in KNOWLEDGE.glob("*.json")
        if json.loads(path.read_text())["symbol"] == symbol
    ]

    if not files:
        return None, True

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)

        for path in files:
            stored = json.loads(path.read_text())
            # The relabel: a gate bypass for research, not a claim
            # change. Every segment, share and mechanism below is what
            # the reading stored.
            stored["schema_version"] = PREVIOUS_SCHEMA_VERSION
            (root / path.name).write_text(json.dumps(stored))

        observations = JsonCompanyKnowledgeStore(root).latest(symbol)

    return (consensus_of(observations) if observations else None), True


# ── route B: the same arithmetic, engine-aware ──────────────────────


@dataclass(frozen=True)
class Verdict:
    """One route's answer for one company, with the rule that decided."""

    stated: str
    primary: Archetype | None
    rule: str
    explained: float
    coverage: tuple[tuple[str, float], ...]


def coverage_of(
    segments: tuple[ConsensusSegment, ...],
    ignore_models_of: frozenset[str] = frozenset(),
) -> tuple[tuple[RevenueModel, float], ...]:
    """How much of the business earns each way, widest first.

    Production's arithmetic, with one option: a segment named in
    `ignore_models_of` contributes its size to no mechanism. That is
    the whole of route B — the segment keeps its revenue, its size and
    its mechanisms, and stops being counted as an *independent engine*
    in the ranking.
    """

    weight: dict[RevenueModel, float] = defaultdict(float)

    for segment in segments:
        if segment.name in ignore_models_of:
            continue

        for model in segment.revenue_models:
            weight[model] += segment.revenue_share or 0.0

    return tuple(sorted(weight.items(), key=lambda item: (-item[1], item[0].value)))


def verdict_for(
    knowledge: CompanyKnowledgeConsensus,
    dependent: frozenset[str] = frozenset(),
) -> Verdict:
    """Production's decision procedure, optionally engine-aware.

    Deliberately a re-implementation rather than a patch: production
    cannot change because of anything here, and the one difference is
    visible on one line. Route A is this function with no dependents.
    """

    if knowledge.segments_because is not None:
        return Verdict("Not classified", None, "segments-unsettled", 0.0, ())

    earning = tuple(seg for seg in knowledge.segments if seg.revenue_models)

    if not earning:
        return Verdict("Not classified", None, "nothing-explained", 0.0, ())

    measurable = tuple(seg for seg in earning if seg.revenue_share)

    if not measurable:
        return Verdict("Unranked", None, "nothing-measured", 0.0, ())

    # The dependent segment's revenue is still explained: the filing
    # does say how it earns. Only its claim to be a separate engine is
    # withdrawn. Erasing it here would refuse VW harder, not classify it.
    explained = sum(seg.revenue_share or 0.0 for seg in measurable)

    if explained < ENOUGH_EXPLAINED:
        return Verdict(
            "Not classified",
            None,
            "too-little-explained",
            explained,
            tuple((m.value, c) for m, c in coverage_of(measurable, dependent)),
        )

    covers = coverage_of(measurable, dependent)
    shown = tuple((m.value, c) for m, c in covers)
    leading = [(model, share) for model, share in covers if share >= LEADS]

    if not leading:
        return Verdict(
            "Diversified",
            Archetype.DIVERSIFIED,
            "no-way-of-earning-leads",
            explained,
            shown,
        )

    top_model, top_share = leading[0]
    contenders = [m for m, share in leading if abs(share - top_share) < TIED]

    if len(contenders) > 1:
        return Verdict(
            "Diversified",
            Archetype.DIVERSIFIED,
            "no-single-way-of-earning-leads",
            explained,
            shown,
        )

    primary = ARCHETYPE_OF[top_model]

    return Verdict(primary.value, primary, "one-way-of-earning-leads", explained, shown)


# ── the description-altitude axis ───────────────────────────────────


def with_mechanisms(
    knowledge: CompanyKnowledgeConsensus,
    segment_name: str,
    models: tuple[RevenueModel, ...],
) -> CompanyKnowledgeConsensus:
    """A research copy where one segment's earning is granted.

    The counterfactual for VW's real blocker: `Pkw und leichte
    Nutzfahrzeuge` is 76% of measured revenue and carries no
    established mechanism, because the filer describes that activity at
    a different reporting altitude than the reportable segment's own
    name. Nothing here infers a mechanism from a name — it *grants* one
    to ask what the rules would then do.
    """

    return replace(
        knowledge,
        segments=tuple(
            replace(seg, revenue_models=models) if seg.name == segment_name else seg
            for seg in knowledge.segments
        ),
    )


def pct(share: float) -> str:
    return f"{share * 100:.1f}%"
