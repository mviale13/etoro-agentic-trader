"""Run the Artificial CIO across the securities the investor is watching."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.ranking import rank_by_conviction
from app.brain import Brain
from app.domain.research_candidate import ResearchCandidate


@dataclass(frozen=True, slots=True)
class ResearchFunnel:
    """How a watchlist became a shortlist, counted at every step."""

    #: Securities the watchlists name and the portfolio does not hold.
    candidates: int

    #: Candidates this cycle spent a fundamentals request on.
    reviewed: int

    #: Reviewed candidates the Brain ended up holding evidence for.
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

    A candidate is only judged when the Brain holds evidence about the
    security itself. Portfolio reasoning is identical for every symbol, so
    judging an unevidenced candidate would produce a verdict about the
    account wearing the candidate's name. Those candidates are counted and
    reported as unevidenced instead.
    """

    pipeline: ExecutivePipeline = field(
        default_factory=ExecutivePipeline,
    )

    def evidenced(
        self,
        brain: Brain,
    ) -> tuple[ResearchCandidate, ...]:
        """Return the candidates the Brain can describe on their own terms."""

        return tuple(
            candidate
            for candidate in brain.candidates
            if brain.evidence_for(candidate.symbol)
        )

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

        unevidenced = tuple(
            candidate
            for candidate in brain.candidates
            if candidate.symbol.upper().strip() in attempted
            and candidate.symbol not in evidenced_symbols
        )

        not_reviewed = tuple(
            candidate
            for candidate in brain.candidates
            if candidate.symbol.upper().strip() not in attempted
            and candidate.symbol not in evidenced_symbols
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
                reviewed=len(brain.attempted_candidates),
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
