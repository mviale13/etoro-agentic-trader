"""Artificial CIO execution pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.application.brain.reasoning import ReasoningService
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.brief.executive_brief_builder import (
    ExecutiveBriefBuilder,
)
from app.application.committees.committee_service import CommitteeService
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.executive.executive_action_builder import (
    ExecutiveActionBuilder,
)
from app.application.executive.executive_evaluation import (
    ExecutiveEvaluation,
)
from app.application.learning.decision_journal import DecisionJournal
from app.application.thesis.investment_thesis_builder import (
    InvestmentThesisBuilder,
)
from app.brain import Brain
from app.cio.artificial_cio import ExecutiveDecisionEngine
from app.cio.digital_asset_decision import as_executive_decision
from app.domain.asset_class import AssetClass
from app.repositories.json_event_repository import JsonEventRepository
from app.services.business_quality_service import quality_of
from app.services.company_understanding_service import (
    CompanyUnderstandingService,
)
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)

from .executive_workspace import ExecutiveWorkspace


@dataclass(slots=True)
class ExecutivePipeline:
    """Execute the complete Artificial CIO pipeline."""

    reasoning: ReasoningService = field(
        default_factory=ReasoningService,
    )

    committees: CommitteeService = field(
        default_factory=CommitteeService,
    )

    evidence_builder: DecisionEvidenceBuilder = field(
        default_factory=DecisionEvidenceBuilder,
    )

    decision_engine: ExecutiveDecisionEngine = field(
        default_factory=ExecutiveDecisionEngine,
    )

    thesis_builder: InvestmentThesisBuilder = field(
        default_factory=InvestmentThesisBuilder,
    )

    action_builder: ExecutiveActionBuilder = field(
        default_factory=ExecutiveActionBuilder,
    )

    brief_builder: ExecutiveBriefBuilder = field(
        default_factory=ExecutiveBriefBuilder,
    )

    #: Where decisions are remembered. None runs the pipeline without
    #: memory, which is what a test or a what-if evaluation wants: nothing
    #: the investor never saw should enter the record.
    journal: DecisionJournal | None = None

    #: The read-only door onto stored statement evidence. Asks the store
    #: and stops: no filing is fetched and no model is asked, so a
    #: grounded quality score adds no spend to an evaluation.
    understanding: CompanyUnderstandingService = field(
        default_factory=CompanyUnderstandingService,
    )

    #: The one authoritative crypto judgment path. Read-only: it projects
    #: recorded committee judgments and stored assessment statements, so
    #: evaluating a digital asset costs no fetch and asks no model.
    digital_assets: DigitalAssetDecisionService = field(
        default_factory=DigitalAssetDecisionService,
    )

    @classmethod
    def with_memory(cls) -> ExecutivePipeline:
        """Build the pipeline that remembers what it decided."""

        return cls(
            journal=DecisionJournal(
                repository=JsonEventRepository(),
            ),
        )

    def execute_all(
        self,
        symbols: Sequence[str],
        brain: Brain,
    ) -> tuple[ExecutiveWorkspace, ...]:
        """
        Evaluate several securities against one Brain.

        Every security is judged against exactly the same view of reality,
        which is what makes their convictions comparable.

        The portfolio, the market and the account's risk do not depend on
        which security is being judged, so that view is reasoned once and
        shared across the cycle. Reasoning it per holding repeated three
        analyst passes for every name, and it let "exactly the same view"
        rest on the assessments coming out identical rather than on their
        being the one object they are here.
        """

        reasoning = self.reasoning.reason(brain)

        return tuple(
            self.execute(
                symbol=symbol,
                brain=brain,
                reasoning=reasoning,
            )
            for symbol in symbols
        )

    def execute(
        self,
        symbol: str,
        brain: Brain,
        reasoning: ReasoningSnapshot | None = None,
    ) -> ExecutiveWorkspace:

        workspace = ExecutiveWorkspace(
            symbol=symbol,
            brain=brain,
        )

        # Shared by `execute_all` across the cycle; computed here for a
        # caller judging a single security on its own.
        workspace.reasoning = (
            reasoning if reasoning is not None else self.reasoning.reason(brain)
        )

        # What kind of instrument this is, from the Brain — the narrowest
        # boundary at which this platform knows, and the same one the
        # evidence builder already consults. A digital asset's investment
        # judgment is settled by the crypto path and by nothing else, so
        # the branch is here rather than repeated downstream, and it turns
        # on the asset class rather than on any list of symbols.
        asset_class = brain.asset_class_for(symbol)

        if asset_class is AssetClass.CRYPTO:
            return self._digital_asset(workspace, brain)

        # The findings are gathered once, before anything states a
        # position over them, so that a committee's references and the
        # evidence built beside them point into the same ledger. Built
        # twice they could differ — the earnings calendar is read
        # against a day, and two calls either side of midnight would
        # leave an opinion referencing a finding the case does not hold.
        workspace.findings = self.evidence_builder.ledger(symbol, brain)

        workspace.committee_opinions = self.committees.review(
            brain,
            symbol,
            workspace.findings,
        )

        # What the company's own statements establish about how good the
        # business is, where they reach quorum. It governs the quality
        # score outright there; the provider-fed proxy stands unchanged
        # everywhere else, and the two never blend.
        #
        # The financial model is not resolved here. Which financial
        # language reads a company is decided by the layer that owns it,
        # and this slice changes no routing — so a company reaches the
        # default, and the questions this score asks are the same three
        # under either model.
        workspace.quality = quality_of(
            symbol,
            self.understanding.understanding(symbol).financial,
        )

        workspace.evidence = self.evidence_builder.build(
            symbol,
            brain,
            workspace.reasoning,
            workspace.committee_opinions,
            findings=workspace.findings,
            quality_assessment=workspace.quality,
        )

        workspace.decision = self.decision_engine.decide(
            workspace.evidence,
        )

        # The Brain perceived this history before the cycle began, so the
        # thesis compares today's decision against what came before it.
        workspace.thesis = self.thesis_builder.build(
            symbol=symbol,
            reasoning=workspace.reasoning,
            committee_opinions=workspace.committee_opinions,
            decision=workspace.decision,
            history=brain.decision_history_for(symbol),
            # The scores today's decision was made on, so the thesis can
            # say what moved since the last one — not merely that it did.
            evidence=workspace.evidence,
            # What kind of security this is, so a change in a token's
            # quality is worded as its dossier words the score.
            asset_class=brain.asset_class_for(symbol),
        )

        # What to consider doing about it. Not the decision restated: a
        # RECOMMEND on something already held asks a different question
        # from a RECOMMEND on something the investor does not own, and
        # only the portfolio knows which this is.
        workspace.action = self.action_builder.build(
            decision=workspace.decision,
            held=any(
                holding.symbol.upper().strip() == symbol.upper().strip()
                for holding in brain.portfolio.holdings
            ),
            catalysts=workspace.thesis.catalysts,
        )

        if self.journal is not None:
            # Recorded with its scores: a later cycle can only explain a
            # conviction move if this one wrote down what it moved from.
            self.journal.record(workspace.decision, workspace.evidence)

        workspace.brief = self.brief_builder.build(
            workspace,
        )

        return workspace

    def _digital_asset(
        self,
        workspace: ExecutiveWorkspace,
        brain: Brain,
    ) -> ExecutiveWorkspace:
        """One judgment for one digital asset, wherever it is shown.

        The measured defect this closes: BTC's canonical dossier answered
        INVESTIGATE with no conviction, and the same holding in the
        portfolio brief answered INVESTIGATE **conviction 46**, ranked
        eleventh of fourteen, with *"Market robustness: robust — $1,308.7bn"*
        printed as a reason for it and its annualised volatility printed
        against it. Two reasoning systems, one asset, and only the retired
        one had a number.

        **Nothing is decided here.** The decision is the crypto path's,
        translated into the record shape the surfaces read; the equity
        route below it is not run at all rather than run and discarded,
        because a provider-fed finding that exists is a finding something
        downstream can find.

        No committee opinions, no evidence and no quality assessment:
        those are the *company* reasoning system's outputs, and a digital
        asset has no company. Their absence is what makes it structurally
        impossible for the equity committees' agreement or a provider
        score to reappear beside a crypto holding.
        """

        symbol = workspace.symbol

        reasoning = workspace.reasoning

        assert reasoning is not None

        workspace.decision = as_executive_decision(
            self.digital_assets.decide(symbol),
        )

        workspace.thesis = self.thesis_builder.build(
            symbol=symbol,
            reasoning=reasoning,
            committee_opinions=(),
            decision=workspace.decision,
            history=brain.decision_history_for(symbol),
            # No scores were produced, and none is passed. The thesis
            # reports what moved since the last decision, and for a
            # digital asset there is no number that could move.
            evidence=None,
            asset_class=AssetClass.CRYPTO,
        )

        workspace.action = self.action_builder.build(
            decision=workspace.decision,
            held=any(
                holding.symbol.upper().strip() == symbol.upper().strip()
                for holding in brain.portfolio.holdings
            ),
            catalysts=workspace.thesis.catalysts,
        )

        # Deliberately not journalled. A decision derived from recorded
        # judgments is a projection, recomputed on every read — writing
        # it back would create a second history of the same judgments,
        # and DV3 left the crypto journal question open on purpose.

        workspace.brief = self.brief_builder.build(workspace)

        return workspace

    def evaluate(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveEvaluation:

        workspace = self.execute(
            symbol=symbol,
            brain=brain,
        )

        assert workspace.reasoning is not None
        assert workspace.decision is not None
        assert workspace.thesis is not None

        reasoning = workspace.reasoning
        decision = workspace.decision
        thesis = workspace.thesis

        return ExecutiveEvaluation(
            decision=decision,
            thesis=thesis,
            reasoning=reasoning,
            committee_opinions=workspace.committee_opinions,
        )
