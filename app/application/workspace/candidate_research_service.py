"""Run the Artificial CIO across the securities the investor is watching."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.ranking import rank_by_conviction
from app.brain import Brain
from app.domain.asset_class import AssetClass
from app.domain.research_candidate import ResearchCandidate
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)


@dataclass(frozen=True, slots=True)
class ResearchFunnel:
    """How a watchlist became a shortlist, counted at every step."""

    #: Securities the watchlists name and the portfolio does not hold.
    candidates: int

    #: Candidates this cycle examined.
    #:
    #: A company is examined by spending a fundamentals request on it. A
    #: digital asset is examined by reading the judgments its committees
    #: have already recorded, which costs nothing — so it is examined
    #: whether or not the request budget reached it, and being outside
    #: that budget is not a reason to leave it out.
    reviewed: int

    #: Examined candidates the reasoning system that judges them can
    #: describe on their own terms.
    evidenced: int

    #: Candidates the Artificial CIO judged.
    judged: int

    #: Judged candidates whose decision asks the investor to act.
    actionable: int

    @property
    def unevidenced(self) -> int:
        """Reviewed candidates no evidence could be obtained for."""

        return max(0, self.reviewed - self.evidenced)

    @property
    def not_reviewed(self) -> int:
        """Candidates this cycle did not have the budget to look at."""

        return max(0, self.candidates - self.reviewed)


@dataclass(frozen=True, slots=True)
class CandidateResearch:
    """The research pipeline: what was considered, and what survived."""

    funnel: ResearchFunnel

    #: Ranked by the conviction the Artificial CIO assigned, highest first.
    workspaces: tuple[ExecutiveWorkspace, ...]

    #: The candidate behind each evaluation, keyed by symbol.
    candidates: dict[str, ResearchCandidate]

    #: Candidates a fundamentals request was spent on that produced no
    #: evidence. Named, not just counted: the investor deserves to know
    #: which of their watched securities could not be described.
    unevidenced: tuple[ResearchCandidate, ...] = ()

    #: Candidates this cycle did not have the budget to look at. Named for
    #: the same reason — a security silently absent from the list reads as
    #: a security that was considered and dismissed.
    not_reviewed: tuple[ResearchCandidate, ...] = ()


@dataclass(slots=True)
class CandidateResearchService:
    """
    Judge the watched securities the investor does not own.

    A candidate is only judged when this platform can describe the
    security on its own terms. Portfolio reasoning is identical for every
    symbol, so judging a candidate it cannot describe would produce a
    verdict about the account wearing the candidate's name. Those
    candidates are counted and reported as unevidenced instead.

    **What counts as describing it belongs to the system that judges
    it.** Admission tested one thing — whether the company evidence
    pipeline had produced a provider row — for every asset alike, and
    since DV4 a digital asset is not judged by that pipeline at all.
    Measured: 1INCH, ARB and ADA each hold recorded committee judgments
    and a canonical INVESTIGATE, and all three were withheld from
    research because a *fundamentals request budget* had not reached
    them. A digital asset needs no such request; reading what its
    committees already recorded costs nothing.
    """

    pipeline: ExecutivePipeline = field(
        default_factory=ExecutivePipeline,
    )

    #: The one authoritative crypto judgment path, shared with the
    #: pipeline. Read-only and free: it projects recorded judgments, so
    #: asking it whether an asset can be researched spends nothing.
    digital_assets: DigitalAssetDecisionService = field(
        default_factory=DigitalAssetDecisionService,
    )

    def evidenced(
        self,
        brain: Brain,
    ) -> tuple[ResearchCandidate, ...]:
        """The candidates this platform can describe on their own terms."""

        return tuple(
            candidate
            for candidate in brain.candidates
            if self._can_be_described(brain, candidate)
        )

    def _can_be_described(
        self,
        brain: Brain,
        candidate: ResearchCandidate,
    ) -> bool:
        """Whether the system that judges this asset has anything to say.

        The dispatch is DV4's, at the same boundary: the asset class the
        Brain already holds. On `CRYPTO` itself rather than on
        `has_no_company`, which also covers funds and commodities — both
        of which the company pipeline still describes.

        A provider row neither grants nor is required for a digital
        asset. It cannot grant admission: a market price is not a
        judgment, and letting one stand in would admit a token no
        committee has looked at. And it cannot be required: the judgment
        is already recorded, and withholding it for want of a price
        would hide a conclusion this platform has actually reached.
        """

        if brain.asset_class_for(candidate.symbol) is AssetClass.CRYPTO:
            return self.digital_assets.decide(candidate.symbol).judged

        return bool(brain.evidence_for(candidate.symbol))

    def build(
        self,
        brain: Brain,
    ) -> CandidateResearch:
        """
        Evaluate every evidenced candidate against the same Brain.

        "Reviewed" is read off the Brain's own record of which candidates
        a fundamentals request was spent on. It used to be reconstructed
        from the budget by the caller, which counted the candidates that
        were left out but could not name them.
        """

        evidenced = self.evidenced(brain)

        attempted = {symbol.upper().strip() for symbol in brain.attempted_candidates}

        evidenced_symbols = {candidate.symbol for candidate in evidenced}

        # Examined: a fundamentals request was spent on it, or it was
        # describable without one. The two lists below and the funnel's
        # counts are both derived from this set, so a count can no longer
        # disagree with the names beside it.
        examined = tuple(
            candidate
            for candidate in brain.candidates
            if candidate.symbol.upper().strip() in attempted
            or candidate.symbol in evidenced_symbols
        )

        examined_symbols = {candidate.symbol for candidate in examined}

        unevidenced = tuple(
            candidate
            for candidate in examined
            if candidate.symbol not in evidenced_symbols
        )

        not_reviewed = tuple(
            candidate
            for candidate in brain.candidates
            if candidate.symbol not in examined_symbols
        )

        ranked = rank_by_conviction(
            self.pipeline.execute_all(
                symbols=[candidate.symbol for candidate in evidenced],
                brain=brain,
            )
        )

        return CandidateResearch(
            funnel=ResearchFunnel(
                candidates=len(brain.candidates),
                reviewed=len(examined),
                evidenced=len(evidenced),
                judged=len(ranked),
                actionable=sum(
                    1
                    for workspace in ranked
                    if workspace.decision is not None
                    and workspace.decision.state.asks_for_action
                ),
            ),
            workspaces=ranked,
            candidates={candidate.symbol: candidate for candidate in brain.candidates},
            unevidenced=unevidenced,
            not_reviewed=not_reviewed,
        )
