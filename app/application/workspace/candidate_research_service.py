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
        reviewed: int | None = None,
    ) -> CandidateResearch:
        """
        Evaluate every evidenced candidate against the same Brain.

        `reviewed` is how many candidates this cycle actually spent a
        fundamentals request on. The caller sets that budget, so only the
        caller can report it; without it the funnel claims no more than what
        it can see.
        """

        evidenced = self.evidenced(brain)

        ranked = rank_by_conviction(
            self.pipeline.execute_all(
                symbols=[candidate.symbol for candidate in evidenced],
                brain=brain,
            )
        )

        return CandidateResearch(
            funnel=ResearchFunnel(
                candidates=len(brain.candidates),
                reviewed=reviewed if reviewed is not None else len(evidenced),
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
        )
