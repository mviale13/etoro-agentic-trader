"""What the Executive Writer produced, grounded finding by finding."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.provenance import Provenance

#: The sections a narrative may carry, in the order they are rendered.
#: A section the writer returns outside this vocabulary is a contract
#: violation, not a new feature.
NARRATIVE_SECTIONS = (
    "executive_summary",
    "why_now",
    "trade_off",
    "committee_summary",
    "thesis_invalidators",
)


@dataclass(frozen=True, slots=True)
class NarrativeFinding:
    """
    One canonical fact the writer was allowed to write from.

    Findings are the whole grounding contract: the writer receives these,
    numbered, and every paragraph it returns must cite the ones it rests
    on. A paragraph that cites nothing, or cites a finding that does not
    exist, is rejected before it reaches any surface.
    """

    id: str
    statement: str
    source: str


@dataclass(frozen=True, slots=True)
class NarrativeSection:
    """One paragraph of the narrative, and the findings under it."""

    section: str
    text: str
    finding_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutiveNarrative:
    """
    The investment case in institutional language — communication only.

    The Artificial CIO owns the judgment; this object only words it.
    `recommendation` is an echo of the decision state the narrative was
    written about, kept so the validator can prove the writer changed
    nothing. The findings travel with the narrative so any surface can
    show what each paragraph rests on.
    """

    symbol: str
    recommendation: str
    headline: str
    sections: tuple[NarrativeSection, ...]
    findings: tuple[NarrativeFinding, ...]

    #: Which model wrote this, and when. A narrative is a reading like
    #: any other and states its provenance like any other.
    model: str
    reading: Provenance
